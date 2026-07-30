import json
import os
import re  # <-- 确保导入了 re 库！
import numpy as np
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline, FeatureUnion

# 1. 页面基本配置
st.set_page_config(page_title="Hotel AI Assistant", page_icon="🏨", layout="centered")
st.title("🏨 酒店智能客服助手")
st.caption("欢迎咨询入住、退房、早餐、Wi-Fi 等常见问题！")

# 2. 文本清洗函数（支持英文字符、数字和中文）
def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower().strip()
    # 替换掉常见标点符号，保留中英文和数字
    text = re.sub(r'[^\w\s\u4e00-\u9fa5]', ' ', text)
    return text

# 3. 训练模型（带异常捕获与缓存）
@st.cache_resource
def load_and_train_model():
    dataset_file = 'dataset.json'
    
    try:
        with open(dataset_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        st.error(f"⚠️ 读取 dataset.json 失败，请检查文件格式！错误: {e}")
        # 提供默认兜底数据，防止整个页面卡死崩溃
        data = {
            "intents": [
                {"tag": "greet", "patterns": ["hi", "hello", "你好"], "responses": ["您好！我是酒店 AI 客服，请问有什么可以帮您？"]},
                {"tag": "ask_wifi", "patterns": ["wifi", "how to login wifi", "wifi password"], "responses": ["Wi-Fi 名称为 Hotel_Guest，无密码。"]}
            ]
        }

    X, y = [], []
    responses_map = {}
    
    for intent in data['intents']:
        tag = intent['tag']
        responses_map[tag] = intent['responses'][0]
        for pattern in intent['patterns']:
            cleaned_pattern = clean_text(pattern)
            if cleaned_pattern: # 确保不是空字符串
                X.append(cleaned_pattern)
                y.append(tag)
            
    # 特征融合：词组 (Word N-gram 1-3) + 字符 (Char-WB N-gram 2-4)
    union = FeatureUnion([
        ('word_tf', TfidfVectorizer(ngram_range=(1, 3), token_pattern=r'(?u)\b\w+\b')),
        ('char_tf', TfidfVectorizer(ngram_range=(2, 4), analyzer='char_wb'))
    ])
    
    # 提高 C 参数 (C=5.0) 增强泛化和识别能力
    model = make_pipeline(union, LogisticRegression(C=5.0))
    model.fit(X, y)
    return model, responses_map

# 加载模型
model, responses_map = load_and_train_model()

# 4. 预测函数
def get_bot_response(user_input):
    cleaned_input = clean_text(user_input)
    if not cleaned_input:
        return "请输入您想询问的内容。"
        
    probs = model.predict_proba([cleaned_input])[0]
    max_idx = np.argmax(probs)
    confidence = probs[max_idx]
    
    # 置信度阈值设置为 0.18
    if confidence < 0.18:
        return "抱歉，我不太理解您的意思。您是想询问退房时间、早餐还是 Wi-Fi 密码呢？如果需要人工帮助，请回复“转人工”。"
    
    predicted_tag = model.classes_[max_idx]
    return responses_map.get(predicted_tag, "抱歉，系统出错了。")

# 5. Streamlit 对话界面渲染
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "您好！我是酒店客服 AI 助手，请问有什么可以帮您？"}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("请输入您的问题... (例如: how to login wifi / 几点退房？)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    bot_reply = get_bot_response(prompt)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    st.chat_message("assistant").write(bot_reply)
