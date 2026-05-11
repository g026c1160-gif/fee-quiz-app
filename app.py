import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="FE過去問道場（全問対応版）", layout="centered")

# キャッシュをあえて使わず、毎回読み込む設定に変更
def load_data():
    df = pd.read_csv("questions.csv")
    return df

df = load_data()
total_questions = len(df) # ここでCSVの行数を数えています

if "solved_indices" not in st.session_state:
    st.session_state.solved_indices = []
if "current_question" not in st.session_state:
    st.session_state.current_question = None

def next_question():
    remaining_indices = [i for i in df.index if i not in st.session_state.solved_indices]
    
    if not remaining_indices:
        st.balloons() # 全問解いたら風船を飛ばす演出！
        st.success(f"おめでとうございます！全 {total_questions} 問を解き終わりました！")
        st.session_state.solved_indices = []
        remaining_indices = list(df.index)
    
    next_idx = random.choice(remaining_indices)
    st.session_state.current_question = df.iloc[next_idx]
    st.session_state.current_idx = next_idx
    st.session_state.show_explanation = False

if st.session_state.current_question is None:
    next_question()

q = st.session_state.current_question

st.title("🛡️ FE過去問道場")
# 進捗状況を常に表示
st.write(f"進捗: **{len(st.session_state.solved_indices)} / {total_questions}** 問完了")
st.progress(len(st.session_state.solved_indices) / total_questions)

st.info(f"**{q['year']}**")
st.write(q['question_text'])

# 選択肢ボタン（以下、前回と同じ）
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

if st.session_state.get("show_explanation", False):
    if st.session_state.current_idx not in st.session_state.solved_indices:
        st.session_state.solved_indices.append(st.session_state.current_idx)
    
    st.subheader(f"正解：{q['correct_answer']}")
    st.write(q['explanation'])
    
    if st.button("次の問題へ"):
        next_question()
        st.rerun()

if st.sidebar.button("学習記録をリセット"):
    st.session_state.solved_indices = []
    next_question()
    st.rerun()
