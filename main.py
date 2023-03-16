# code based on https://medium.com/@avra42/build-your-own-chatbot-with-openai-gpt-3-and-streamlit-6f1330876846
import openai
import streamlit as st

openai.api_key = st.secrets["API_KEY"]

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


def generate_response(prompt, history):
    config = dict(role='system', content="You are a helpful assistant named YChat made by CloseAI")
    prompt = dict(role='user',content=prompt)
    messages = [config, *history, prompt] 
    completions = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=messages
    )
    message = completions.choices[0].message.content
    return message


# Storing the chat
if "generated" not in st.session_state:
    st.session_state["generated"] = []

if "past" not in st.session_state:
    st.session_state["past"] = []
if "history" not in st.session_state:
    st.session_state["history"] = []


def clear_text():
    user_input = st.session_state.get("input", None)
    if user_input:
        output = generate_response(user_input, st.session_state["history"])
        st.session_state.past.append(user_input)
        st.session_state.generated.append(output)
        st.session_state["history"].append(dict(role="user", content=user_input[:256]))
        st.session_state["history"].append(dict(role="assistant", content=output[:512]))
        st.session_state["history"] = st.session_state["history"][
            -5:
        ]  # only keep last 2.5 conversations
        st.session_state["input"] = ""  # ,None)
        user_header = "**:blue[您: ]**"
        bot_header = ":robot_face:: "
        messages = [
            f""" {user_header}  {question} \n \n {bot_header} {answer}\n \n
        """
            for question, answer in zip(
                st.session_state["past"], st.session_state["generated"]
            )
        ]
        markdown = "\n".join(messages)
        st.markdown(markdown, unsafe_allow_html=True)


st.text_input(
    "回车发送, 或点击空白位置", "", key="input", max_chars=512, on_change=clear_text
)  # ,label_visibility='hidden')
