# code based on https://medium.com/@avra42/build-your-own-chatbot-with-openai-gpt-3-and-streamlit-6f1330876846
import openai
import streamlit as st

from streamlit_chat import message

openai.api_key = st.secrets["API_KEY"]
if 'history' not in st.session_state:
    st.session_state['history'] = []


def generate_response(prompt, history):
    messagees = (
        [
            {"role": "system", "content": "You are YChat made by CloseAI. Be concise."},
        ]
        + history
        + [
            {"role": "user", "content": prompt},
        ]
    )
    completions = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=messagees
    )
    message = completions.choices[0].message.content
    return message


st.title("YChat: 智能聊天机器人")

# Storing the chat
if "generated" not in st.session_state:
    st.session_state["generated"] = []

if "past" not in st.session_state:
    st.session_state["past"] = []


def get_text():
    input_text = st.text_input("输入(回车发送): ", "", key="input",max_chars=512)
    return input_text


user_input = get_text()

if user_input:
    output = generate_response(user_input, st.session_state['history'])
    # store the output
    st.session_state.past.append(user_input)
    st.session_state.generated.append(output)
    st.session_state['history'].append(dict(role="user", content=user_input[:256]))
    st.session_state['history'].append(dict(role="assistant", content=output[:256]))
    st.session_state['history']  = st.session_state['history'][-3:]  # only keep last 1.5 conversations

if st.session_state["generated"]:
    for i in range(len(st.session_state["generated"]) - 1, -1, -1):
        message(st.session_state["generated"][i], key=str(i))
        message(st.session_state["past"][i], is_user=True, key=str(i) + "_user")
