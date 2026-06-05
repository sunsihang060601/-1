// 严格按照你提供的分类标准，构建垃圾分类数据库
const garbageDatabase = [
    // 1. 可回收物（二级分6类）
    { name: "纸类", mainCategory: "可回收物", subCategory: "纸类", keywords: ["纸", "纸箱", "报纸", "书本", "杂志", "传单"] },
    { name: "塑料类", mainCategory: "可回收物", subCategory: "塑料类", keywords: ["塑料", "塑料瓶", "塑料盒", "塑料玩具", "塑料桶"] },
    { name: "玻璃类", mainCategory: "可回收物", subCategory: "玻璃类", keywords: ["玻璃", "玻璃瓶", "玻璃杯", "玻璃碗", "镜子"] },
    { name: "金属类", mainCategory: "可回收物", subCategory: "金属类", keywords: ["金属", "易拉罐", "铁盒", "铝罐", "铁钉", "金属餐具"] },
    { name: "纺织类", mainCategory: "可回收物", subCategory: "纺织类", keywords: ["衣服", "布料", "纺织", "围巾", "袜子", "书包"] },
    { name: "电器/电子产品", mainCategory: "可回收物", subCategory: "电器/电子产品", keywords: ["电器", "电子", "手机", "电脑", "遥控器", "耳机", "家电"] },

    // 2. 有害垃圾（二级分5类）
    { name: "废电池", mainCategory: "有害垃圾", subCategory: "废电池", keywords: ["电池", "蓄电池", "纽扣电池", "充电电池"] },
    { name: "废灯管", mainCategory: "有害垃圾", subCategory: "废灯管", keywords: ["灯管", "荧光灯", "节能灯", "灯泡"] },
    { name: "废药品", mainCategory: "有害垃圾", subCategory: "废药品", keywords: ["药品", "过期药", "药片", "药膏", "药瓶"] },
    { name: "废油漆/溶剂/容器", mainCategory: "有害垃圾", subCategory: "废油漆/溶剂/容器", keywords: ["油漆", "溶剂", "油漆桶", "杀虫剂罐"] },
    { name: "其他有害日用品", mainCategory: "有害垃圾", subCategory: "其他有害日用品", keywords: ["杀虫剂", "消毒剂", "水银", "温度计", "化妆品"] },

    // 3. 厨余垃圾（湿垃圾）（二级分4类）
    { name: "食材果蔬类", mainCategory: "厨余垃圾", subCategory: "食材果蔬类", keywords: ["蔬菜", "水果", "食材", "青菜", "苹果", "香蕉", "白菜"] },
    { name: "餐厨剩饭菜", mainCategory: "厨余垃圾", subCategory: "餐厨剩饭菜", keywords: ["剩饭", "剩菜", "饭菜", "餐厨垃圾", "食物残渣"] },
    { name: "瓜皮果核", mainCategory: "厨余垃圾", subCategory: "瓜皮果核", keywords: ["瓜皮", "果核", "果皮", "桃核", "西瓜皮", "香蕉皮"] },
    { name: "糕点零食残渣", mainCategory: "厨余垃圾", subCategory: "糕点零食残渣", keywords: ["糕点", "零食", "蛋糕", "饼干", "面包", "零食渣"] },

    // 4. 其他垃圾（干垃圾）（二级分4类）
    { name: "污染一次性用品", mainCategory: "其他垃圾", subCategory: "污染一次性用品", keywords: ["一次性", "污染纸巾", "外卖盒", "一次性筷子", "餐盒"] },
    { name: "陶瓷/渣土砖瓦", mainCategory: "其他垃圾", subCategory: "陶瓷/渣土砖瓦", keywords: ["陶瓷", "渣土", "砖瓦", "碎碗", "花盆", "瓷砖"] },
    { name: "毛发灰土", mainCategory: "其他垃圾", subCategory: "毛发灰土", keywords: ["毛发", "灰土", "灰尘", "头发", "烟头", "烟灰"] },
    { name: "难以归类杂物", mainCategory: "其他垃圾", subCategory: "难以归类杂物", keywords: ["杂物", "污染塑料袋", "尿不湿", "卫生巾", "口罩"] }
];

// DOM元素获取
const imageUpload = document.getElementById("imageUpload");
const previewArea = document.getElementById("previewArea");
const resultCard = document.getElementById("resultCard");
const itemName = document.getElementById("itemName");
const categoryTag = document.getElementById("categoryTag");
const subCategory = document.getElementById("subCategory");
const searchInput = document.getElementById("searchInput");
const searchBtn = document.getElementById("searchBtn");
const queryResult = document.getElementById("queryResult");

// 主类对应颜色配置
const categoryColors = {
    "可回收物": { bg: "#3498db", lightBg: "#d1e7ff" },
    "有害垃圾": { bg: "#e74c3c", lightBg: "#fde2e2" },
    "厨余垃圾": { bg: "#e67e22", lightBg: "#feecd5" },
    "其他垃圾": { bg: "#95a5a6", lightBg: "#e9ecef" }
};

// 图片上传与识别逻辑
imageUpload.addEventListener("change", function (e) {
    const file = e.target.files[0];
    if (!file) return;

    // 图片预览
    const reader = new FileReader();
    reader.onload = function (ev) {
        previewArea.innerHTML = `<img src="${ev.target.result}" alt="垃圾图片预览">`;
    };
    reader.readAsDataURL(file);

    // 模拟识别（真实项目可接入AI图像识别接口）
    itemName.textContent = "正在识别中...";
    categoryTag.textContent = "";
    subCategory.textContent = "";
    resultCard.style.borderLeftColor = "#3498db";

    setTimeout(() => {
        const fileName = file.name.toLowerCase();
        const result = matchGarbage(fileName);
        displayResult(result);
    }, 1000);
});

// 关键词匹配函数
function matchGarbage(text) {
    for (const item of garbageDatabase) {
        for (const keyword of item.keywords) {
            if (text.includes(keyword.toLowerCase())) {
                return item;
            }
        }
    }
    // 无匹配时返回默认结果
    return {
        name: "未知垃圾",
        mainCategory: "其他垃圾",
        subCategory: "难以归类杂物"
    };
}

// 展示识别结果
function displayResult(result) {
    itemName.textContent = `识别物品：${result.name}`;
    categoryTag.textContent = result.mainCategory;
    categoryTag.style.background = categoryColors[result.mainCategory].bg;
    categoryTag.style.color = "white";
    subCategory.textContent = `二级分类：${result.subCategory}`;
    resultCard.style.borderLeftColor = categoryColors[result.mainCategory].bg;
}

// 垃圾分类查询功能
searchBtn.addEventListener("click", function () {
    const searchText = searchInput.value.trim();
    if (!searchText) {
        queryResult.innerHTML = "<p style='color: #e74c3c;'>请输入垃圾名称进行查询！</p>";
        return;
    }

    const result = matchGarbage(searchText);
    queryResult.innerHTML = `
        <p>物品：<strong>${result.name}</strong></p>
        <p>主分类：<span style='background: ${categoryColors[result.mainCategory].bg}; color: white; padding: 3px 10px; border-radius: 12px;'>${result.mainCategory}</span></p>
        <p>二级分类：${result.subCategory}</p>
    `;
});

// 回车触发查询
searchInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
        searchBtn.click();
    }
});