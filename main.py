# code based on https://medium.com/@avra42/build-your-own-chatbot-with-openai-gpt-3-and-streamlit-6f1330876846
import openai
import streamlit as st
openai.api_key = st.secrets["API_KEY"]
if 'history' not in st.session_state:
    st.session_state['history'] = []

def message_fn(messages, role='user'):
    user_header = '**:blue[您: ]**'
    bot_header = ':robot_face:: '
    messages = [f'''{bot_header} {answer} \n \n {user_header}  {question} \n \n
      ''' for question,answer in zip (st.session_state['past'], st.session_state['generated'])][::-1]
    markdown = '\n'.join(messages)
    st.markdown(markdown,unsafe_allow_html=True)

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

def generate_response(prompt, history):
    messagees = (
        [
            {"role": "system", "content": "You are a helpful assistant named YChat made by CloseAI."},
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


# st.title("YChat: 智能聊天机器人")

# Storing the chat
if "generated" not in st.session_state:
    st.session_state["generated"] = []

if "past" not in st.session_state:
    st.session_state["past"] = []


def get_text():
    input_text = st.text_area("输入, ctrl+回车发送", "", key="input",max_chars=512,label_visibility='hidden')
    st.button("发送")
    return input_text


user_input = get_text()
if user_input:
    output = generate_response(user_input, st.session_state['history'])
    st.session_state.past.append(user_input)
    st.session_state.generated.append(output)
    st.session_state['history'].append(dict(role="user", content=user_input[:256]))
    st.session_state['history'].append(dict(role="assistant", content=output[:512]))
    st.session_state['history']  = st.session_state['history'][-5:]  # only keep last 2.5 conversations

if st.session_state["generated"]:
    message_fn('x')
  