import json
import numpy as np
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.pipeline import make_pipeline

# 1. 页面基本配置
st.set_page_config(page_title="Hotel AI Assistant", page_icon="🏨", layout="centered")
st.title("🏨 酒店智能客服助手")
st.caption("欢迎咨询入住、退房、早餐、Wi-Fi 等常见问题！")

# 2. 训练模型（使用 @st.cache_resource 避免每次刷新页面都重新训练）
@st.cache_resource
def load_and_train_model():
    with open('dataset.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    X, y = [], []
    responses_map = {}
    
    for intent in data['intents']:
        tag = intent['tag']
        responses_map[tag] = intent['responses'][0]
        for pattern in intent['patterns']:
            X.append(pattern)
            y.append(tag)
            
    # 构建 TF-IDF + SVM 模型
    model = make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), SVC(kernel='linear', probability=True))
    model.fit(X, y)
    return model, responses_map

model, responses_map = load_and_train_model()

# 3. 意图预测与置信度过滤
def get_bot_response(user_input):
    probs = model.predict_proba([user_input])[0]
    max_idx = np.argmax(probs)
    confidence = probs[max_idx]
    
    # 低置信度（低于 35%）触发 Fallback
    if confidence < 0.35:
        return "抱歉，我不太理解您的意思。您是想询问退房时间、早餐还是 Wi-Fi 密码呢？如果需要人工帮助，请回复“转人工”。"
    
    predicted_tag = model.classes_[max_idx]
    return responses_map.get(predicted_tag, "抱歉，系统出错了。")

# 4. Streamlit 聊天历史渲染与交互
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "您好！我是酒店客服 AI 助手，请问有什么可以帮您？"}
    ]

# 显示历史消息
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 处理用户输入
if prompt := st.chat_input("请输入您的问题... (例如: 几点退房？早餐在哪吃？)"):
    # 渲染用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    # 生成并渲染 Bot 答复
    bot_reply = get_bot_response(prompt)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    st.chat_message("assistant").write(bot_reply)
