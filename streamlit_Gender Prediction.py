import json
import os
import re
import numpy as np
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline, FeatureUnion

st.set_page_config(page_title="Hotel AI Assistant", page_icon="🏨", layout="centered")
st.title("🏨 酒店智能客服助手")
st.caption("欢迎咨询入住、退房、早餐、Wi-Fi 等常见问题！")

def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s\u4e00-\u9fa5]', ' ', text)
    return text

@st.cache_resource
def load_and_train_model():
    dataset_file = 'dataset.json'
    
    try:
        with open(dataset_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        st.error(f"⚠️ 读取 dataset.json 失败: {e}")
        data = {"intents": []}

    X, y = [], []
    responses_map = {}
    
    for intent in data['intents']:
        tag = intent['tag']
        responses_map[tag] = intent['responses'][0]
        for pattern in intent['patterns']:
            cleaned_pattern = clean_text(pattern)
            if cleaned_pattern:
                X.append(cleaned_pattern)
                y.append(tag)
            
    union = FeatureUnion([
        ('word_tf', TfidfVectorizer(ngram_range=(1, 3), token_pattern=r'(?u)\b\w+\b')),
        ('char_tf', TfidfVectorizer(ngram_range=(2, 4), analyzer='char_wb'))
    ])
    
    model = make_pipeline(union, LogisticRegression(C=5.0))
    model.fit(X, y)
    return model, responses_map

model, responses_map = load_and_train_model()

# 初始化 Session State（用于多轮对话记忆）
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "您好！我是酒店客服 AI 助手，请问有什么可以帮您？"}
    ]

# 记住上一次对话的意图 (Context State)
if "last_intent" not in st.session_state:
    st.session_state.last_intent = None

# 多轮上下文预测逻辑
def get_bot_response(user_input):
    cleaned_input = clean_text(user_input)
    if not cleaned_input:
        return "请输入您想询问的内容。"
        
    probs = model.predict_proba([cleaned_input])[0]
    max_idx = np.argmax(probs)
    confidence = probs[max_idx]
    predicted_tag = model.classes_[max_idx]
    
    # 💡 多轮对话核心处理逻辑：
    # 如果用户问的是 generic/follow-up 问题，且上一轮聊的是 Wi-Fi
    if predicted_tag == "ask_wifi_steps" and st.session_state.last_intent != "ask_wifi":
        # 如果前面没聊过 Wi-Fi，直接问步骤时，给一个更通用的提示
        st.session_state.last_intent = "ask_wifi"
        return responses_map.get("ask_wifi_steps", "请问您需要哪项服务的具体步骤？（例如 Wi-Fi 连接或延迟退房流程）")

    # 低置信度 Fallback
    if confidence < 0.18:
        return "抱歉，我不太理解您的意思。您是想询问退房时间、早餐还是 Wi-Fi 密码呢？"
    
    # 更新当前 Intent 状态，以便下一轮追问使用
    st.session_state.last_intent = predicted_tag
    return responses_map.get(predicted_tag, "抱歉，系统出错了。")

# 渲染对话界面
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("请输入您的问题... (例: how to login wifi -> can you guide me step by step?)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    bot_reply = get_bot_response(prompt)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    st.chat_message("assistant").write(bot_reply)
