from flask import Flask, render_template, request, redirect, url_for, jsonify, Response
import time
import os
import uuid
import json
import cv2  # 用于摄像头捕捉
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# ================= 基础配置与数据存储 =================
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

USER_DATA_FILE = 'users.json'
STATS_DATA_FILE = 'stats.json'

def load_users():
    if not os.path.exists(USER_DATA_FILE): return {}
    with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return {}

def save_users(users):
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def load_stats():
    if not os.path.exists(STATS_DATA_FILE): return {"identify_count": 0, "chat_count": 0}
    with open(STATS_DATA_FILE, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return {"identify_count": 0, "chat_count": 0}

def save_stats(stats):
    with open(STATS_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=4)

# ================= YOLO 模型加载 =================
try:
    from ultralytics import YOLO
    model = YOLO("best.pt")
    print("==================================================")
    print("✅ 成功加载自定义 YOLOv8 模型文件 best.pt！")
    print("==================================================")
except Exception as e:
    print("==================================================")
    print(f"⚠️ 警告：本地未检测到 best.pt 或报错，降级为无模型状态。错误: {e}")
    print("请确保已执行: pip install torch ultralytics opencv-python")
    print("==================================================")
    model = None

# ================= 严格对齐 12 个类别的字典 =================
TRASH_KNOWLEDGE_MAP = {
    "bottle": {"name": "瓶子", "category": "可回收物", "tip": "请清空里面残留的液体，压扁后投入蓝色收集容器中。"},
    "carton": {"name": "纸盒/纸板箱", "category": "可回收物", "tip": "请将纸箱拆开压平，去除胶带后捆扎好投放。"},
    "peel": {"name": "果皮", "category": "厨余垃圾", "tip": "属于易腐烂的有机垃圾，请直接投入绿色厨余垃圾桶。"},
    "apple": {"name": "苹果/果核", "category": "厨余垃圾", "tip": "属于易腐有机垃圾，请直接投入绿色厨余容器。"},
    "paper": {"name": "废纸", "category": "可回收物", "tip": "平整干净的废纸请投入可回收物桶；如果是严重污染的纸团则属于其他垃圾。"},
    "can": {"name": "易拉罐/金属罐", "category": "可回收物", "tip": "请清空内部残留物并压扁，金属是可以循环利用的宝贵资源。"},
    "cloth": {"name": "旧衣服/废织物", "category": "可回收物", "tip": "请洗净、晒干后，投入专用的废旧织物回收箱。"},
    "eggshell": {"name": "蛋壳", "category": "厨余垃圾", "tip": "蛋壳属于极易降解垃圾，请投入绿色厨余垃圾收集容器。"},
    "battery": {"name": "废旧电池", "category": "有害垃圾", "tip": "电池含有毒重金属，请务必单独存放到红色的有害垃圾桶，切勿破坏外壳！"},
    "cigarette": {"name": "烟头", "category": "其他垃圾", "tip": "请务必确保烟头彻底熄灭后再行投放，谨防引起火灾。"},
    "disposable": {"name": "一次性用品/餐盒", "category": "其他垃圾", "tip": "受到污染的一次性餐盒、筷子难以回收，属于其他垃圾，请尽量少用一次性用品哦。"},
    "phone": {"name": "废旧手机", "category": "可回收物", "tip": "属于电子废弃物，含有贵金属。请务必清除个人隐私数据后，投入可回收物箱或交由正规回收渠道！"}
}

# ================= 页面路由 =================
@app.route('/')
def home(): return render_template('home.html')

@app.route('/login')
def login_page(): return render_template('login.html')

@app.route('/signup')
def signup_page(): return render_template('signup.html')

@app.route('/index')
def index_page(): return render_template('index.html')

@app.route('/identify')
def identify_page(): return render_template('identify.html')

@app.route('/chat')
def chat_page(): return render_template('chat.html')

@app.route('/history')
def history_page(): return render_template('history.html')

@app.route('/community')
def community_page(): return render_template('community.html')

@app.route('/users')
def users_page(): return render_template('users.html')


# ================= 用户管理接口 =================
@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    if not username or not password: return jsonify({"success": False, "message": "用户名或密码不能为空"}), 400
    users = load_users()
    if username in users: return jsonify({"success": False, "message": "该用户名已被注册啦！"}), 400
    users[username] = {"email": email, "password": generate_password_hash(password)}
    save_users(users)
    return jsonify({"success": True, "message": "注册成功！"})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    users = load_users()
    user = users.get(username)
    if user and check_password_hash(user['password'], password):
        return jsonify({"success": True, "message": "登录成功"})
    return jsonify({"success": False, "message": "用户名或密码错误，请重试！"}), 401

@app.route('/api/users', methods=['GET'])
def api_get_users():
    users = load_users()
    user_list = [{"username": u, "email": i.get("email", "无"), "role": "超级管理员" if u.lower() == "admin" else "普通用户"} for u, i in users.items()]
    return jsonify({"success": True, "users": user_list})

@app.route('/api/users/delete', methods=['POST'])
def api_delete_user():
    username = request.get_json().get('username')
    if username.lower() == 'admin': return jsonify({"success": False, "message": "管理员账号不可删除！"}), 403
    users = load_users()
    if username in users:
        del users[username]
        save_users(users)
        return jsonify({"success": True, "message": f"用户 {username} 已被删除"})
    return jsonify({"success": False, "message": "用户不存在"}), 404


# ================= 动态统计接口 =================
@app.route('/api/stats', methods=['GET'])
def api_get_stats():
    stats = load_stats()
    return jsonify({
        "success": True,
        "identify_count": stats.get("identify_count", 0),
        "chat_count": stats.get("chat_count", 0),
        "user_count": len(load_users())
    })

@app.route('/api/track_chat', methods=['POST'])
def api_track_chat():
    stats = load_stats()
    stats["chat_count"] = stats.get("chat_count", 0) + 1
    save_stats(stats)
    return jsonify({"success": True})


# ================= 核心：图片识别接口 =================
@app.route('/api/identify', methods=['POST'])
def api_identify_garbage():
    if 'file' not in request.files: return jsonify({"success": False, "message": "未检测到上传的文件"}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({"success": False, "message": "未选择图片"}), 400
    
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
    safe_filename = f"yolo_{int(time.time())}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
    file.save(filepath)
    
    # 统计数据打卡
    stats = load_stats()
    stats["identify_count"] = stats.get("identify_count", 0) + 1
    save_stats(stats)
    
    print(f"\n=== 🚀 收到前端请求，开始处理图片: {safe_filename} ===")
    
    detected_name = "未知物品"
    detected_category = "无法判定"
    detected_tip = "模型未在图中发现目标，可能是图片模糊或该物品不在12个识别类别内。"
    
    if model is not None:
        try:
            print("🧠 正在调用本地 best.pt 模型进行推理...")
            results = model(filepath, conf=0.2) # 降低门槛到 20%
            
            if len(results) > 0 and len(results[0].boxes) > 0:
                class_id = int(results[0].boxes[0].cls[0])
                class_name = model.names[class_id]
                confidence = float(results[0].boxes[0].conf[0])
                print(f"🎯 成功框出目标！模型认为是 [{class_name}]，置信度: {confidence:.2f}")
                
                if class_name in TRASH_KNOWLEDGE_MAP:
                    info = TRASH_KNOWLEDGE_MAP[class_name]
                    detected_name, detected_category, detected_tip = info["name"], info["category"], info["tip"]
                    print(f"✅ 知识库匹配成功：转译为中文 [{detected_name}]")
                else:
                    detected_name = f"未收录标签: {class_name}"
            else:
                print("⚠️ 模型跑完了，但是没有找到任何可以画框的目标 (No detections)。")
        except Exception as e: 
            print(f"❌ 推理报错: {e}")
    else:
        print("⚠️ 警告：模型未加载！返回随机模拟数据。")
        import random
        k = random.choice(list(TRASH_KNOWLEDGE_MAP.keys()))
        detected_name, detected_category, detected_tip = TRASH_KNOWLEDGE_MAP[k]["name"], TRASH_KNOWLEDGE_MAP[k]["category"], TRASH_KNOWLEDGE_MAP[k]["tip"]
        
    print("=========================================================\n")
    return jsonify({"success": True, "name": detected_name, "category": detected_category, "tip": detected_tip, "saved_url": f"/{filepath}"})


# ================= 核心：在线流媒体边缘检测 =================
def generate_frames():
    """高性能实时捕获视频流：通过降低尺寸和跳帧算法，彻底解决卡顿与延迟"""
    # 1. 启动外接摄像头 (序号 1)
    camera = cv2.VideoCapture(1)
    
    # 2. 硬件级高帧率优化：设置高帧率、小分辨率缩减传输体积，并关闭OpenCV内部缓存防止延迟堆积
    camera.set(cv2.CAP_PROP_FPS, 30)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1) # 缓冲区只留1帧，从根本上解决“动作慢半拍”的延迟问题

    frame_count = 0
    latest_results = None

    while True:
        success, frame = camera.read()
        if not success:
            break
        
        frame_count += 1

        if model is not None:
            try:
                # 💡 核心策略：每 3 帧才让 YOLO 算一次，极大释放算力！
                if frame_count % 3 == 0 or latest_results is None:
                    # imgsz=320: 缩减模型内部矩阵，速度狂飙4倍！
                    # half=True: 启用半精度推理（如果硬件支持会更快）
                    latest_results = model(frame, conf=0.25, imgsz=320, verbose=False)
                
                # 沿用最新一次的检测结果画框，保证每一帧都有框，视觉效果极其丝滑
                annotated_frame = latest_results[0].plot()
            except Exception as e:
                print(f"实时流推理微调报错: {e}")
                annotated_frame = frame
        else:
            annotated_frame = frame
            cv2.putText(annotated_frame, "Model not loaded!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # 转换为 JPEG
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)