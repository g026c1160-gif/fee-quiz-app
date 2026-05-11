import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="FE過去問道場", page_icon="📝")

@st.cache_data
def load_data():
    return pd.read_csv("questions.csv")

df = load_data()

st.title("基本情報技術者 過去問演習")

if 'current_question' not in st.session_state:
    st.session_state.current_question = df.sample(n=1).iloc[0]
    st.session_state.show_answer = False

def next_question():
    st.session_state.current_question = df.sample(n=1).iloc[0]
    st.session_state.show_answer = False

q = st.session_state.current_question

st.subheader(f"分野: {q['year']}")
st.write(q['question_text'])

# 選択肢ボタン
col1, col2 = st.columns(2)
with col1:
    if st.button(f"ア: {q['choice_a']}"): st.session_state.show_answer = True
    if st.button(f"イ: {q['choice_b']}"): st.session_state.show_answer = True
with col2:
    if st.button(f"ウ: {q['choice_c']}"): st.session_state.show_answer = True
    if st.button(f"エ: {q['choice_d']}"): st.session_state.show_answer = True

if st.session_state.show_answer:
    st.success(f"正解は: {q['correct_answer']}")
    st.info(f"【解説】\n{q['explanation']}")
    st.button("次の問題へ", on_click=next_question)
