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
            X.append(pattern.lower().strip()) # 统一转小写，防止大小写影响
            y.append(tag)
            
    # 特征融合：既考虑词组(Word N-gram)，也考虑字符(Char N-gram，防止短词和错别字失效)
    union = FeatureUnion([
        ('word_tf', TfidfVectorizer(ngram_range=(1, 2), token_pattern=r'(?u)\b\w+\b')), # 包含单字母如 'a', 'hi'
        ('char_tf', TfidfVectorizer(ngram_range=(2, 4), analyzer='char_wb'))            # 对 tmr, hi 等短词极其友好
    ])
    
    # 构建 SVM 模型
    model = make_pipeline(union, SVC(kernel='linear', probability=True))
    model.fit(X, y)
    return model, responses_map

# 3. 意图预测与置信度过滤
def get_bot_response(user_input):
    clean_input = user_input.lower().strip() # 转小写
    probs = model.predict_proba([clean_input])[0]
    max_idx = np.argmax(probs)
    confidence = probs[max_idx]
    
    # 稍微调低置信度阈值到 0.25
    if confidence < 0.25:
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
