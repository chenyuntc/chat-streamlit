import openai
import streamlit as st
from google.cloud import firestore
from datetime import datetime
@st.cache_resource()
def get_db():
    firebase_setting=st.secrets['firebase']
    db=firestore.Client.from_service_account_info(dict(project_id=firebase_setting['project_id'], private_key=firebase_setting['private_key'],token_uri=firebase_setting['token_uri'],client_email=firebase_setting['client_email']))
    doc=db.collection('chat').document('history').collection((str(datetime.now())))
    return doc
db = get_db()

openai.api_key = st.secrets["API_KEY"]
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

def generate_response(prompt, history):
    config = dict(role='system', content="You are a helpful assistant named YChat made by CloseAI, be concise")
    prompt = dict(role='user',content=prompt)
    messages = [config, *history, prompt] 
    completions = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages,stream=True)
    return completions

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
        user_header = "**:blue[您: ]**"
        bot_header = ":robot_face:: "
        output = generate_response(user_input, st.session_state["history"])
        messages = [
            f"{user_header}  {question} \n \n {bot_header} {answer}\n \n"
            for question, answer in zip(
                st.session_state["past"], st.session_state["generated"]
            )
        ]
        markdown = "\n".join(messages)
        st.markdown(markdown)
        st.markdown(f'{user_header} {user_input} \n\n')
        res_st=st.empty()
        res_text = ''
        for idx,xx in enumerate(output):
            if 'content'  in xx.choices[0]['delta']:
                res_text += xx.choices[0]['delta']['content']
            if idx %3==0:
                res_st.markdown(f"{bot_header} {res_text}")
        st.session_state.past.append(user_input)
        st.session_state.generated.append(res_text)
        st.session_state["history"].append(dict(role="user", content=user_input[:256]))
        st.session_state["history"].append(dict(role="assistant", content=res_text[-256:]))
        st.session_state["history"] = st.session_state["history"][-4:]
        st.session_state["input"] = ""  # ,None)
        db.document(str(datetime.now())).create(dict(response=res_text.replace('\n',r'\\n'),user_input=user_input))

st.text_input(
    "回车发送, 或点击空白位置", "", key="input", max_chars=512, on_change=clear_text,label_visibility='hidden' if len(st.session_state['history']) else 'visible')
