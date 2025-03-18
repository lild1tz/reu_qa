import streamlit as st
import requests

# Определяем URL FastAPI-сервера (локально или в контейнере)
API_URL = "http://localhost:8000/api/request"

# Интерфейс Streamlit
st.set_page_config(page_title="REU QA", page_icon="🤖", layout="centered")

st.title("🔍 AI Вопрос-Ответ для РЭУ")

# Поле ввода текста
user_input = st.text_area("Введите ваш вопрос:", height=100)

# Кнопка отправки запроса
if st.button("🔍 Отправить запрос"):
    if user_input.strip():
        with st.spinner("⏳ Модель обрабатывает запрос..."):
            # Отправляем запрос в FastAPI
            response = requests.post(API_URL, json={"query": user_input})
            
            if response.status_code == 200:
                data = response.json()
                st.success("✅ Ответ от модели:")
                st.write(f"**📌 Ответ:** {data['answer']}")
                st.write(f"🧐 **Обоснование:** {data['reasoning']}")
                
                if data.get("sources"):
                    st.write("🔗 **Источники:**")
                    for source in data["sources"]:
                        st.markdown(f"- [{source}]({source})")
            else:
                st.error("❌ Ошибка! Не удалось получить ответ от сервера.")
    else:
        st.warning("⚠️ Введите вопрос перед отправкой!")
