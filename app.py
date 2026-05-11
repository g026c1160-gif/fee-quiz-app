import streamlit as st
import pandas as pd
import random

# ページの設定
st.set_page_config(page_title="FE過去問道場（重複なし版）", layout="centered")

# データの読み込み
@st.cache_data
def load_data():
    df = pd.read_csv("questions.csv")
    return df

df = load_data()

# セッション状態（メモ帳）の初期化
if "solved_indices" not in st.session_state:
    st.session_state.solved_indices = []  # 解き終わった問題の番号を記録するリスト
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "show_explanation" not in st.session_state:
    st.session_state.show_explanation = False

# 次の問題を選ぶ関数
def next_question():
    # まだ解いていない問題のインデックス（番号）を探す
    remaining_indices = [i for i in df.index if i not in st.session_state.solved_indices]
    
    if not remaining_indices:
        st.warning("全問題を解き終わりました！記録をリセットします。")
        st.session_state.solved_indices = []
        remaining_indices = list(df.index)
    
    # 残っている問題からランダムに1つ選ぶ
    next_idx = random.choice(remaining_indices)
    st.session_state.current_question = df.iloc[next_idx]
    st.session_state.current_idx = next_idx # 現在の問題番号を保持
    st.session_state.show_explanation = False

# 初回起動時
if st.session_state.current_question is None:
    next_question()

q = st.session_state.current_question

# 表示部分
st.title("🛡️ FE過去問道場")
st.caption(f"進捗: {len(st.session_state.solved_indices)} / {len(df)} 問完了")

st.info(f"**{q['year']}**")
st.write(q['question_text'])

# 選択肢ボタン
col1, col2 = st.columns(2)
with col1:
    if st.button(f"ア：{q['choice_a']}", use_container_width=True):
        st.session_state.show_explanation = True
    if st.button(f"ウ：{q['choice_c']}", use_container_width=True):
        st.session_state.show_explanation = True
with col2:
    if st.button(f"イ：{q['choice_b']}", use_container_width=True):
        st.session_state.show_explanation = True
    if st.button(f"エ：{q['choice_d']}", use_container_width=True):
        st.session_state.show_explanation = True

# 解説表示
if st.session_state.show_explanation:
    # 今の問題を「解いたリスト」に追加
    if st.session_state.current_idx not in st.session_state.solved_indices:
        st.session_state.solved_indices.append(st.session_state.current_idx)
    
    st.subheader(f"正解：{q['correct_answer']}")
    st.write(q['explanation'])
    
    if st.button("次の問題へ"):
        next_question()
        st.rerun()

# 記録のリセットボタン（サイドバー）
if st.sidebar.button("学習記録をリセット"):
    st.session_state.solved_indices = []
    next_question()
    st.rerun()
