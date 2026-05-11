import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="FE過去問道場（復習モード）", layout="centered")

def load_data():
    df = pd.read_csv("questions.csv")
    return df

df = load_data()

# セッション状態の初期化
if "solved_indices" not in st.session_state:
    st.session_state.solved_indices = []
if "wrong_indices" not in st.session_state:
    st.session_state.wrong_indices = []  # 間違えた問題の番号を保存
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "mode" not in st.session_state:
    st.session_state.mode = "通常"  # 「通常」か「復習」か

def next_question():
    # モードに応じて対象となる問題リストを変える
    if st.session_state.mode == "復習":
        target_indices = [i for i in st.session_state.wrong_indices if i not in st.session_state.solved_indices]
        if not target_indices:
            st.success("復習リストの問題をすべて解きました！通常モードに戻ります。")
            st.session_state.mode = "通常"
            target_indices = [i for i in df.index if i not in st.session_state.solved_indices]
    else:
        target_indices = [i for i in df.index if i not in st.session_state.solved_indices]

    if not target_indices:
        st.balloons()
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

# サイドバー設定
st.sidebar.title("設定・記録")
st.session_state.mode = st.sidebar.radio("モード切替", ["通常", "復習"], index=0 if st.session_state.mode=="通常" else 1)
st.sidebar.write(f"間違えた問題数: {len(st.session_state.wrong_indices)} 問")
if st.sidebar.button("間違えた記録をリセット"):
    st.session_state.wrong_indices = []
    st.rerun()

# メイン画面
st.title(f"🛡️ FE過去問道場 ({st.session_state.mode}モード)")
st.write(f"進捗: **{len(st.session_state.solved_indices)} / {len(df)}** 問完了")
st.progress(min(len(st.session_state.solved_indices) / len(df), 1.0))

st.info(f"**{q['year']}**")
st.write(q['question_text'])

# 選択肢と判定
choices = {"ア": q['choice_a'], "イ": q['choice_b'], "ウ": q['choice_c'], "エ": q['choice_d']}
col1, col2 = st.columns(2)

for i, (key, val) in enumerate(choices.items()):
    with col1 if i % 2 == 0 else col2:
        if st.button(f"{key}：{val}", use_container_width=True):
            st.session_state.user_answer = key
            st.session_state.show_explanation = True

if st.session_state.show_explanation:
    is_correct = st.session_state.user_answer == q['correct_answer']
    
    if is_correct:
        st.success(f"⭕ 正解！ (あなたの回答: {st.session_state.user_answer})")
        # 正解したら「間違えたリスト」から消す（復習完了）
        if st.session_state.current_idx in st.session_state.wrong_indices:
            st.session_state.wrong_indices.remove(st.session_state.current_idx)
    else:
        st.error(f"❌ 不正解... 正解は「{q['correct_answer']}」です。")
        # 間違えたら「間違えたリスト」に追加
        if st.session_state.current_idx not in st.session_state.wrong_indices:
            st.session_state.wrong_indices.append(st.session_state.current_idx)

    if st.session_state.current_idx not in st.session_state.solved_indices:
        st.session_state.solved_indices.append(st.session_state.current_idx)

    st.write(f"**【解説】**\n{q['explanation']}")
    
    if st.button("次の問題へ"):
        next_question()
        st.rerun()
