import json
import numpy as np
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline, FeatureUnion

# 1. 页面基本配置
st.set_page_config(page_title="Hotel AI Assistant", page_icon="🏨", layout="centered")
st.title("🏨 酒店智能客服助手")
st.caption("欢迎咨询入住、退房、早餐、Wi-Fi 等常见问题！")

# 2. 训练模型（使用 @st.cache_resource 避免重复训练）
@st.cache_resource
def load_and_train_model():
    dataset_file = 'dataset.json'
    
    # 自动容错：如果文件损坏或不存在，自动写入默认的 json
    try:
        with open(dataset_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        st.error(f"⚠️ 读取 dataset.json 失败（可能是 JSON 语法错误），已自动加载默认测试数据！错误详情: {e}")
        data = {
            "intents": [
                {"tag": "greet", "patterns": ["hi", "hello", "你好"], "responses": ["您好！请问有什么可以帮您？"]},
                {"tag": "breakfast", "patterns": ["what time for breakfast", "早餐几点"], "responses": ["早餐时间为 06:30 - 10:00。"]}
            ]
        }

    X, y = [], []
    responses_map = {}
    
    for intent in data['intents']:
        tag = intent['tag']
        responses_map[tag] = intent['responses'][0]
        for pattern in intent['patterns']:
            X.append(pattern.lower().strip())
            y.append(tag)
            
    # 特征融合 (支持短单词如 hi, tmr 以及中英文)
    union = FeatureUnion([
        ('word_tf', TfidfVectorizer(ngram_range=(1, 2), token_pattern=r'(?u)\b\w+\b')),
        ('char_tf', TfidfVectorizer(ngram_range=(2, 4), analyzer='char_wb'))
    ])
    
    model = make_pipeline(union, LogisticRegression())
    model.fit(X, y)
    return model, responses_map

# 加载模型
model, responses_map = load_and_train_model()

# 3. 预测函数
def get_bot_response(user_input):
    clean_input = user_input.lower().strip()
    probs = model.predict_proba([clean_input])[0]
    max_idx = np.argmax(probs)
    confidence = probs[max_idx]
    
    # 低置信度触发 Fallback
    if confidence < 0.25:
        return "抱歉，我不太理解您的意思。您是想询问退房时间、早餐还是 Wi-Fi 密码呢？如果需要人工帮助，请回复“转人工”。"
    
    predicted_tag = model.classes_[max_idx]
    return responses_map.get(predicted_tag, "抱歉，系统出错了。")

# 4. Streamlit 对话界面渲染
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "您好！我是酒店客服 AI 助手，请问有什么可以帮您？"}
    ]

# 显示历史对话
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 用户输入处理
if prompt := st.chat_input("请输入您的问题... (例如: 几点退房？早餐在哪吃？)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    bot_reply = get_bot_response(prompt)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    st.chat_message("assistant").write(bot_reply)
