import streamlit as st
import requests

st.set_page_config(page_title="OSINT Agent Chat", page_icon="🕵️")
st.title("🕵️ OSINT Agent — чат")


N8N_WEBHOOK_URL = st.secrets["N8N_WEBHOOK_URL"]

# Храним историю чата в session_state, иначе она будет исчезать при каждом действии
if "messages" not in st.session_state:
    st.session_state.messages = []

# Отображаем всю историю сообщений
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Поле ввода внизу экрана (стандартный чат-интерфейс Streamlit)
user_input = st.chat_input("Напишите сообщение агенту...")

if user_input:
    # Показываем сообщение пользователя сразу
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Отправляем запрос в n8n
    with st.chat_message("assistant"):
        with st.spinner("Агент думает..."):
            try:
                response = requests.post(
                    N8N_WEBHOOK_URL,
                    json={"message": user_input},
                    timeout=60  # LLM может отвечать дольше обычного API
                )

                if response.status_code == 200:
                    # Response Body = {{ $json.output }} с Response with = Text
                    # значит response.text — это уже готовый текст ответа
                    reply = response.text
                    st.markdown(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                else:
                    error_text = (
                        f"Ошибка {response.status_code}.\n\n"
                        f"Проверьте, нажали ли вы 'Execute workflow' в n8n.\n\n"
                        f"Ответ сервера: {response.text[:500]}"
                    )
                    st.error(error_text)

            except requests.exceptions.Timeout:
                st.error("Превышено время ожидания ответа от n8n (60 сек).")
            except requests.exceptions.RequestException as e:
                st.error(f"Не удалось связаться с n8n: {e}")

# Кнопка для очистки истории чата — удобно при тестировании
with st.sidebar:
    st.subheader("Управление")
    if st.button("🗑️ Очистить историю чата"):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption(f"Webhook: `{N8N_WEBHOOK_URL}`")