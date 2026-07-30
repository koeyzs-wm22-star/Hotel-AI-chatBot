import json
import os
import re
import numpy as np
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline, FeatureUnion

# 1. 页面基本配置
st.set_page_config(page_title="Hotel AI Assistant", page_icon="🏨", layout="centered")
st.title("🏨 酒店智能客服助手")
st.caption("欢迎咨询入住、退房、早餐、Wi-Fi 等常见问题！")

# 动态天气 API 获取函数 (使用免费开源的 Open-Meteo API)
def get_realtime_weather(city="Kuala Lumpur"):
    try:
        # 这里以吉隆坡坐标 (3.139, 101.6869) 为例，你可以更改为你的酒店所在城市坐标
        # 北京: lat=39.9042, lon=116.4074 | 上海: lat=31.2304, lon=121.4737
        url = "https://api.open-meteo.com/v1/forecast?latitude=3.139&longitude=101.6869&current_weather=true"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            current = data.get("current_weather", {})
            temp = current.get("temperature", "N/A")
            windspeed = current.get("windspeed", "N/A")
            weather_code = current.get("weathercode", 0)
            
            # WMO 天气代码简易映射
            weather_desc = "晴朗/多云"
            if weather_code in [1, 2, 3]:
                weather_desc = "多云"
            elif weather_code in [51, 61, 80, 95]:
                weather_desc = "阵雨/降雨"
                
            return f"🌤️ **酒店当地实时天气**：\n- 当前天气状况：{weather_desc}\n- 当前气温：{temp}°C\n- 风速：{windspeed} km/h\n\n出门请注意天气变化，如有需要可在酒店前台免费借用雨伞！"
        else:
            return "☀️ 当前酒店当地气温舒适，大约 28°C-32°C。详细天气可咨询前台。"
    except Exception as e:
        return "☀️ 当前酒店当地天气晴朗，适宜出行。如需借用雨伞请联系前台。"

# 2. 安全的文本清洗函数
def clean_text(text):
    if not text or not isinstance(text, str):
        return ""
    text = text.lower().strip()
    # 替换特殊标点符号，保留字母、数字和中文
    text = re.sub(r'[^\w\s\u4e00-\u9fa5]', ' ', text)
    # 去除多余连续空格
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# 3. 模型训练（含空值过滤防护）
@st.cache_resource
def load_and_train_model():
    dataset_file = 'dataset.json'
    
    try:
        with open(dataset_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        st.error(f"⚠️ 读取 dataset.json 失败: {e}")
        data = {
            "intents": [
                {"tag": "greet", "patterns": ["hi", "hello", "你好"], "responses": ["您好！我是酒店 AI 客服，请问有什么可以帮您？"]},
                {"tag": "ask_wifi", "patterns": ["wifi", "how to login wifi", "wifi password"], "responses": ["Wi-Fi 名称为 Hotel_Guest，无密码。"]}
            ]
        }

    X, y = [], []
    responses_map = {}
    
    for intent in data.get('intents', []):
        tag = intent.get('tag')
        responses = intent.get('responses', [""])
        responses_map[tag] = responses[0] if responses else "抱歉，暂无答复。"
        
        for pattern in intent.get('patterns', []):
            cleaned_pattern = clean_text(pattern)
            # 只有当清洗后非空，才加入训练集，彻底防止 Empty Vocabulary Error
            if cleaned_pattern:
                X.append(cleaned_pattern)
                y.append(tag)

    # 兜底：如果数据集太小或格式有问题导致 X 为空，插入默认基础语料
    if not X:
        X = ["hi", "wifi", "breakfast"]
        y = ["greet", "ask_wifi", "ask_breakfast"]
        responses_map = {
            "greet": "您好！",
            "ask_wifi": "Wi-Fi: Hotel_Guest",
            "ask_breakfast": "早餐时间 6:30-10:00"
        }
            
    # 特征融合：设置 token_pattern=r'\S+' 确保任何非空字符都能生成向量，绝报错 empty vocabulary
    union = FeatureUnion([
        ('word_tf', TfidfVectorizer(ngram_range=(1, 3), token_pattern=r'\S+')),
        ('char_tf', TfidfVectorizer(ngram_range=(2, 4), analyzer='char_wb'))
    ])
    
    model = make_pipeline(union, LogisticRegression(C=5.0))
    model.fit(X, y)
    return model, responses_map

# 加载模型
model, responses_map = load_and_train_model()

# 初始化 Session State（用于多轮对话与记忆）
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "您好！我是酒店客服 AI 助手，请问有什么可以帮您？"}
    ]

if "last_intent" not in st.session_state:
    st.session_state.last_intent = None

# 预测函数
def get_bot_response(user_input):
    cleaned_input = clean_text(user_input)
    if not cleaned_input:
        return "请输入您想询问的内容。"
        
    probs = model.predict_proba([cleaned_input])[0]
    max_idx = np.argmax(probs)
    confidence = probs[max_idx]
    predicted_tag = model.classes_[max_idx]
    
    # 低置信度 Fallback
    if confidence < 0.18:
        return "抱歉，我不太理解您的意思。您是想询问退房时间、早餐、Wi-Fi 还是天气预报呢？"
    
    st.session_state.last_intent = predicted_tag

    # 💡 关键修复：只要标签是 ask_weather，直接调用 API 函数返回结果！
    if predicted_tag == "ask_weather":
        return get_realtime_weather()
        
    # 多轮连贯问题处理逻辑（Wi-Fi 追问）
    if predicted_tag == "ask_wifi_steps" and st.session_state.last_intent != "ask_wifi":
        return responses_map.get("ask_wifi_steps", "请问您需要哪项服务的具体步骤？（例如 Wi-Fi 连接流程）")

    # 其他普通意图正常返回 responses_map 里的内容
    return responses_map.get(predicted_tag, "抱歉，系统出错了。")

# 4. Streamlit 渲染界面
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("请输入您的问题... (例: how to login wifi / 几点退房？)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    bot_reply = get_bot_response(prompt)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    st.chat_message("assistant").write(bot_reply)
