import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="FE過去問道場（完全版）", layout="centered")

def load_data():
    df = pd.read_csv("questions.csv")
    return df

df = load_data()

# セッション状態の初期化
if "solved_indices" not in st.session_state:
    st.session_state.solved_indices = []
if "wrong_indices" not in st.session_state:
    st.session_state.wrong_indices = []
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "mode" not in st.session_state:
    st.session_state.mode = "通常"
if "show_explanation" not in st.session_state:
    st.session_state.show_explanation = False
if "user_answer" not in st.session_state:
    st.session_state.user_answer = None

def next_question():
    if st.session_state.mode == "復習":
        target_indices = [i for i in st.session_state.wrong_indices if i not in st.session_state.solved_indices]
        if not target_indices:
            st.session_state.mode = "通常"
            target_indices = [i for i in df.index if i not in st.session_state.solved_indices]
    else:
        target_indices = [i for i in df.index if i not in st.session_state.solved_indices]

    if not target_indices:
        st.session_state.solved_indices = []
        target_indices = list(df.index)
    
    next_idx = random.choice(target_indices)
    st.session_state.current_question = df.iloc[next_idx]
    st.session_state.current_idx = next_idx
    st.session_state.show_explanation = False
    st.session_state.user_answer = None

if st.session_state.current_question is None:
    next_question()

q = st.session_state.current_question

# サイドバー
st.sidebar.title("設定・記録")
st.session_state.mode = st.sidebar.radio("モード切替", ["通常", "復習"], index=0 if st.session_state.mode=="通常" else 1)
st.sidebar.write(f"間違えた問題数: {len(st.session_state.wrong_indices)} 問")

# メイン画面
st.title(f"🛡️ FE過去問道場")
st.caption(f"現在のモード: {st.session_state.mode}")
st.write(f"進捗: **{len(st.session_state.solved_indices)} / {len(df)}** 問完了")

st.info(f"**{q['year']}**")
st.subheader(q['question_text'])

# --- 修正ポイント：ボタンの押し分けを確実に取得 ---
col1, col2 = st.columns(2)
with col1:
    if st.button(f"ア：{q['choice_a']}", use_container_width=True):
        st.session_state.user_answer = "ア"
        st.session_state.show_explanation = True
    if st.button(f"ウ：{q['choice_c']}", use_container_width=True):
        st.session_state.user_answer = "ウ"
        st.session_state.show_explanation = True
with col2:
    if st.button(f"イ：{q['choice_b']}", use_container_width=True):
        st.session_state.user_answer = "イ"
        st.session_state.show_explanation = True
    if st.button(f"エ：{q['choice_d']}", use_container_width=True):
        st.session_state.user_answer = "エ"
        st.session_state.show_explanation = True

# 解説と判定
if st.session_state.show_explanation and st.session_state.user_answer:
    st.divider()
    is_correct = (st.session_state.user_answer == q['correct_answer'])
    
    if is_correct:
        st.success(f"⭕ **正解！**（あなたの回答：{st.session_state.user_answer}）")
        if st.session_state.current_idx in st.session_state.wrong_indices:
            st.session_state.wrong_indices.remove(st.session_state.current_idx)
    else:
        st.error(f"❌ **不正解...**（正解は「{q['correct_answer']}」でした）")
        if st.session_state.current_idx not in st.session_state.wrong_indices:
            st.session_state.wrong_indices.append(st.session_state.current_idx)

    if st.session_state.current_idx not in st.session_state.solved_indices:
        st.session_state.solved_indices.append(st.session_state.current_idx)

    st.write(f"**【解説】**")
    st.write(q['explanation'])
    
    if st.button("次の問題へ ➡️"):
        next_question()
        st.rerun()
