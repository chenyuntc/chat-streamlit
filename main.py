from openai import OpenAI

import streamlit as st
from google.cloud import firestore
from datetime import datetime
st.set_page_config(page_title='YChat - CloseAI', page_icon=':robot_face:')
client = OpenAI(api_key=st.secrets["API_KEY"])
@st.cache_resource()
def get_db():
    firebase_setting=st.secrets['firebase']
    db=firestore.Client.from_service_account_info(dict(project_id=firebase_setting['project_id'], private_key=firebase_setting['private_key'],token_uri=firebase_setting['token_uri'],client_email=firebase_setting['client_email']))
    doc=db.collection('chat.history')#.document('history').collection((str(datetime.now())))
    return doc
if 'db' not in st.session_state:
    st.session_state['start_time']=datetime.now()
    st.session_state['db'] = get_db().document(str(st.session_state['start_time']))
    st.session_state["generated"] = []
    st.session_state["past"] = []
    st.session_state["history"] = []
    #st.session_state['model'] = 'gpt-3.5-turbo'
    st.session_state['model'] = 'gpt-4o'

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
# st.markdown(hide_streamlit_style, unsafe_allow_html=True)

def generate_response(prompt, history):
    config = dict(role='system', content="You are a helpful assistant named YChat made by CloseAI, be concise")
    prompt = dict(role='user',content=prompt)
    messages = [config, *history, prompt] 
    completions = client.chat.completions.create(model=st.session_state['model'], messages=messages,stream=True)
    return completions

def clear_text():
    user_input = st.session_state.get("input", None)
    if user_input:
        if user_input.startswith('/use gpt4'):
            st.session_state['model'] = 'gpt-4o'
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
            if xx.choices[0].delta.content:
                res_text += xx.choices[0].delta.content
                res_st.markdown(f"{bot_header} {res_text}")
        st.session_state.past.append(user_input)
        st.session_state.generated.append(res_text)
        st.session_state["history"].append(dict(role="user", content=user_input[:256]))
        st.session_state["history"].append(dict(role="assistant", content=res_text[-256:]))
        st.session_state["history"] = st.session_state["history"][-4:]
        # st.session_state["input"] = ""  # ,None)
        n_msg=len(st.session_state["past"])
        st.session_state['db'].set(
            {
                f"{n_msg:02d}_user_input":user_input.replace('\n',r'\n'),
                f"{n_msg:02d}_response":res_text.replace('\n',r'\n'),
                f"{n_msg:02d}_time_pass": str(datetime.now()-st.session_state['start_time'])
            },
            merge=True
        )

st.chat_input(
    "回车发送", key="input", max_chars=512, on_submit=clear_text)#,label_visibility='hidden' if len(st.session_state['history']) else 'visible')
