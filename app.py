import streamlit as st
import requests

st.set_page_config(page_title="Prospecting Engine", page_icon="🔗", layout="wide")

# ============================================================
# Webhook URLs — add these 4 keys to your .streamlit/secrets.toml
#
# PROSPECT_BRIEF_NEW_RUN_WEBHOOK_URL = "https://..."
# PROSPECT_BRIEF_EXISTING_DB_WEBHOOK_URL = "https://..."
# RELATIONSHIP_GRAPH_NEW_RUN_WEBHOOK_URL = "https://..."
# RELATIONSHIP_GRAPH_EXISTING_DB_WEBHOOK_URL = "https://..."
# ============================================================
WEBHOOKS = {
    "prospect_brief": {
        "new_run": st.secrets["PROSPECT_BRIEF_NEW_RUN_WEBHOOK_URL"],
        "existing_database": st.secrets["PROSPECT_BRIEF_EXISTING_DB_WEBHOOK_URL"],
    },
    "relationship_graph": {
        "new_run": st.secrets["RELATIONSHIP_GRAPH_NEW_RUN_WEBHOOK_URL"],
        "existing_database": st.secrets["RELATIONSHIP_GRAPH_EXISTING_DB_WEBHOOK_URL"],
    },
}
 
MODE_LABELS = {
    "new_run": "New run",
    "existing_database": "Existing database",
}
 
 
def init_state(tab_key):
    """Make sure this tab has its own isolated chat history and mode."""
    if f"{tab_key}_messages" not in st.session_state:
        st.session_state[f"{tab_key}_messages"] = []
    if f"{tab_key}_mode" not in st.session_state:
        st.session_state[f"{tab_key}_mode"] = None
 
 
def render_mode_selector(tab_key):
    st.info("How would you like to start?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🆕 New run", key=f"{tab_key}_new_run_btn", use_container_width=True):
            st.session_state[f"{tab_key}_mode"] = "new_run"
            st.rerun()
    with col2:
        if st.button("🗂️ Existing database", key=f"{tab_key}_existing_db_btn", use_container_width=True):
            st.session_state[f"{tab_key}_mode"] = "existing_database"
            st.rerun()
 
 
def render_chat(tab_key, title):
    init_state(tab_key)
    st.subheader(title)
 
    mode = st.session_state[f"{tab_key}_mode"]
 
    # No mode chosen yet -> show the two starter buttons and stop here
    if mode is None:
        render_mode_selector(tab_key)
        return
 
    st.caption(f"Mode: **{MODE_LABELS[mode]}**")
 
    # Defined here (not inside `if user_input`) so it's always available,
    # including on the very first render right after a mode is picked
    webhook_url = WEBHOOKS[tab_key][mode]
 
    # Show chat history
    for msg in st.session_state[f"{tab_key}_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
 
    user_input = st.chat_input("Type your message to the agent...", key=f"{tab_key}_chat_input")
 
    if user_input:
        st.session_state[f"{tab_key}_messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
 
        with st.chat_message("assistant"):
            with st.spinner("Agent is thinking..."):
                try:
                    response = requests.post(
                        webhook_url,
                        json={"message": user_input, "mode": mode},
                        # timeout=660  # LLM responses can take longer than a typical API call
                    )
 
                    if response.status_code == 200:
                        # Response Body = {{ $json.output }} with Response With = Text,
                        # so response.text is already the final reply text
                        reply = response.text
                        st.markdown(reply)
                        st.session_state[f"{tab_key}_messages"].append(
                            {"role": "assistant", "content": reply}
                        )
                    else:
                        error_text = (
                            f"Error {response.status_code}.\n\n"
                            f"Check whether you clicked 'Execute workflow' in n8n.\n\n"
                            f"Server response: {response.text[:500]}"
                        )
                        st.error(error_text)
 
                except requests.exceptions.Timeout:
                    st.error("Timed out waiting for a response from n8n.")
                except requests.exceptions.RequestException as e:
                    st.error(f"Could not reach n8n: {e}")
 
    # Per-tab controls in the sidebar
    with st.sidebar:
        st.divider()
        st.caption(f"**{title}** controls")
        if st.button("🔄 Change mode", key=f"{tab_key}_reset_mode_btn", use_container_width=True):
            st.session_state[f"{tab_key}_mode"] = None
            st.session_state[f"{tab_key}_messages"] = []
            st.rerun()
        if st.button("🗑️ Clear chat history", key=f"{tab_key}_clear_btn", use_container_width=True):
            st.session_state[f"{tab_key}_messages"] = []
            st.rerun()
        st.caption(f"Webhook: `{webhook_url}`")

# ============================================================
# Sidebar navigation between the two tabs
# ============================================================
st.sidebar.title("🔗 Prospecting Engine")
page = st.sidebar.radio("Navigation", ["Prospect Brief", "Relationship Graph"])

if page == "Prospect Brief":
    render_chat("prospect_brief", "📋 Prospect Brief")
else:
    render_chat("relationship_graph", "🕸️ Relationship Graph")