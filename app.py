import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="FE過去問道場（完全版）", layout="centered")

# データの読み込み
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
if "shuffled_texts" not in st.session_state:
    st.session_state.shuffled_texts = [] # シャッフルされた「文章のみ」を保持
if "correct_text" not in st.session_state:
    st.session_state.correct_text = "" # 「正解の文章」を保持

def next_question():
    # 問題の選出（通常 or 復習）
    if st.session_state.get("mode") == "復習":
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
    q = df.iloc[next_idx]
    
    # --- 修正の要：文章そのものをリスト化してシャッフル ---
    all_choices = {
        "ア": str(q['choice_a']),
        "イ": str(q['choice_b']),
        "ウ": str(q['choice_c']),
        "エ": str(q['choice_d'])
    }
    
    # 正解の「文章」を抜き出しておく
    correct_label = q['correct_answer'].strip() # 「ア」など
    st.session_state.correct_text = all_choices[correct_label]
    
    # 4つの文章をバラバラにする
    choice_texts = list(all_choices.values())
    random.shuffle(choice_texts)
    
    st.session_state.current_question = q
    st.session_state.current_idx = next_idx
    st.session_state.shuffled_texts = choice_texts
    st.session_state.show_explanation = False
    st.session_state.user_choice_text = None

if st.session_state.current_question is None:
    next_question()

q = st.session_state.current_question
texts = st.session_state.shuffled_texts

# メイン画面
st.title("🛡️ FE過去問道場")
st.write(f"進捗: {len(st.session_state.solved_indices)} / {len(df)}")

st.info(f"**{q['year']}**")
st.subheader(q['question_text'])

# ボタン表示
col1, col2 = st.columns(2)
for i, t in enumerate(texts):
    with col1 if i % 2 == 0 else col2:
        if st.button(t, use_container_width=True, key=f"btn_{i}"):
            st.session_state.user_choice_text = t
            st.session_state.show_explanation = True

# 判定：選んだボタンの「文章」が「正解の文章」と一致するか
if st.session_state.show_explanation and st.session_state.user_choice_text:
    st.divider()
    if st.session_state.user_choice_text == st.session_state.correct_text:
        st.success("⭕ **正解！**")
        if st.session_state.current_idx in st.session_state.wrong_indices:
            st.session_state.wrong_indices.remove(st.session_state.current_idx)
    else:
        st.error(f"❌ **不正解...** \n\n 正解は: \n **{st.session_state.correct_text}**")
        if st.session_state.current_idx not in st.session_state.wrong_indices:
            st.session_state.wrong_indices.append(st.session_state.current_idx)

    if st.session_state.current_idx not in st.session_state.solved_indices:
        st.session_state.solved_indices.append(st.session_state.current_idx)

    st.write(f"**【解説】**")
    st.write(q['explanation'])
    
    if st.button("次の問題へ ➡️"):
        next_question()
        st.rerun()

# サイドバー
st.sidebar.title("設定")
st.session_state.mode = st.sidebar.radio("モード", ["通常", "復習"])
if st.sidebar.button("リセット"):
    st.session_state.solved_indices = []
    st.session_state.wrong_indices = []
    next_question()
    st.rerun()
