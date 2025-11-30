import os
from datetime import datetime

import streamlit as st
from google.cloud import firestore
from openai import OpenAI

st.set_page_config(page_title="YChat - CloseAI", page_icon=":robot_face:")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "moonshotai/kimi-k2"
DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant named YChat made by CloseAI. Be concise."
AVAILABLE_MODELS = sorted(
    [
        "openai/gpt-5.1",
        "moonshotai/kimi-k2",
        'ANY models from "https://openrouter.ai/models"'
    ]
)


@st.cache_resource()
def get_db():
    firebase_setting = st.secrets["firebase"]
    db = firestore.Client.from_service_account_info(
        dict(
            project_id=firebase_setting["project_id"],
            private_key=firebase_setting["private_key"],
            token_uri=firebase_setting["token_uri"],
            client_email=firebase_setting["client_email"],
        )
    )
    return db.collection("chat.history")


@st.cache_resource()
def get_client():
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    if not api_key:
        st.error("Missing OPENROUTER_API_KEY. Add it to Streamlit secrets or the environment.")
        st.stop()
    return OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL)


def ensure_session():
    if "db" not in st.session_state:
        st.session_state["start_time"] = datetime.now()
        st.session_state["db"] = get_db().document(str(st.session_state["start_time"]))
        st.session_state["generated"] = []
        st.session_state["past"] = []
        st.session_state["history"] = []
        st.session_state["model"] = DEFAULT_MODEL
        st.session_state["system_prompt"] = DEFAULT_SYSTEM_PROMPT


def generate_response(prompt, history):
    messages = [
        {"role": "system", "content": st.session_state["system_prompt"]},
        *history,
        {"role": "user", "content": prompt},
    ]
    return get_client().chat.completions.create(
        model=st.session_state["model"],
        messages=messages,
        stream=True,
        extra_body={"provider": {"sort": "throughput"}},
    )


def handle_command(user_input: str) -> bool:
    if not user_input.startswith("/"):
        return False
    command, _, arg = user_input.partition(" ")
    arg = arg.strip()
    if command == "/m":
        if arg:
            st.session_state["model"] = arg
            st.chat_message("assistant").markdown(f"Model set to `{arg}`.")
        else:
            options = "\n".join(f"- `{m}`" for m in AVAILABLE_MODELS)
            st.chat_message("assistant").markdown(f"Available models:\n{options}")
        return True
    if command == "/system":
        if arg:
            st.session_state["system_prompt"] = arg
            st.chat_message("assistant").markdown("System prompt updated.")
        else:
            st.chat_message("assistant").markdown(
                f"Current system prompt:\n\n{st.session_state['system_prompt']}"
            )
        return True
    st.chat_message("assistant").markdown("Unknown command.")
    return True


def render_history():
    for question, answer in zip(st.session_state["past"], st.session_state["generated"]):
        st.chat_message("user").markdown(question)
        st.chat_message("assistant").markdown(answer)


def persist_message(user_input: str, response: str):
    n_msg = len(st.session_state["past"])
    st.session_state["db"].set(
        {
            f"{n_msg:02d}_user_input": user_input.replace("\n", r"\n"),
            f"{n_msg:02d}_response": response.replace("\n", r"\n"),
            f"{n_msg:02d}_model": st.session_state["model"],
            f"{n_msg:02d}_time_pass": str(datetime.now() - st.session_state["start_time"]),
        },
        merge=True,
    )


def main():
    hide_streamlit_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                </style>
                """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    ensure_session()
    render_history()

    if user_input := st.chat_input("Message or use /m and /system commands", max_chars=2048):
        if handle_command(user_input):
            return

        st.chat_message("user").markdown(user_input)
        with st.chat_message("assistant"):
            res_placeholder = st.empty()
            res_text = ""
            for chunk in generate_response(user_input, st.session_state["history"]):
                if chunk.choices[0].delta and chunk.choices[0].delta.content:
                    res_text += chunk.choices[0].delta.content
                    res_placeholder.markdown(res_text)

        st.session_state["past"].append(user_input)
        st.session_state["generated"].append(res_text)
        st.session_state["history"].append({"role": "user", "content": user_input})
        st.session_state["history"].append({"role": "assistant", "content": res_text})
        st.session_state["history"] = st.session_state["history"][-12:]

        persist_message(user_input, res_text)


if __name__ == "__main__":
    main()
