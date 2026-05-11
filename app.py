import streamlit as st
import pandas as pd
import random

# --- 1. データの読み込み ---
@st.cache_data
def load_data():
    df = pd.read_csv('questions.csv', header=None)
    return df

df = load_data()

# --- 2. セッション状態の初期化 ---
if 'solved_indices' not in st.session_state:
    st.session_state.solved_indices = []
if 'wrong_indices' not in st.session_state:
    st.session_state.wrong_indices = []
if 'current_question' not in st.session_state:
    st.session_state.current_question = None
if 'last_mode' not in st.session_state:
    st.session_state.last_mode = "通常"

# --- 3. サイドバー設定 ---
st.sidebar.title("🛠️ 設定")

all_years = sorted(df[0].unique().tolist(), reverse=True)
selected_years = st.sidebar.multiselect("解きたい年度を選択", options=all_years, default=all_years)

selected_mode = st.sidebar.radio("学習モード", ["通常", "復習"])

if st.session_state.last_mode != selected_mode:
    st.session_state.last_mode = selected_mode
    st.session_state.current_question = None
    st.rerun()

st.sidebar.divider() # 区切り線
st.sidebar.write(f"📁 現在の復習対象: **{len(st.session_state.wrong_indices)}** 問")

if st.sidebar.button("学習記録をリセット"):
    st.session_state.solved_indices = []
    st.session_state.wrong_indices = []
    st.session_state.current_question = None
    st.rerun()

# --- 4. 出題ロジック & 進捗計算 ---
filtered_df = df[df[0].isin(selected_years)]
total_in_scope = len(filtered_df) # 選択された年度の総問題数

if selected_mode == "復習":
    target_indices = [i for i in st.session_state.wrong_indices if i in filtered_df.index]
    progress_count = len(st.session_state.wrong_indices) # 復習は残り件数
    if not target_indices:
        st.info("復習対象がありません。")
        st.stop()
else:
    target_indices = [i for i in filtered_df.index if i not in st.session_state.solved_indices]
    # 現在の進捗（解いた数）
    solved_in_scope = [i for i in st.session_state.solved_indices if i in filtered_df.index]
    progress_count = len(solved_in_scope)
    
    if not target_indices:
        st.success("🎉 全ての対象問題を解き終わりました！")
        if st.button("リセットして最初から"):
            st.session_state.solved_indices = []
            st.rerun()
        st.stop()

# 進捗バーの表示
if selected_mode == "通常":
    progress_percent = progress_count / total_in_scope
    st.write(f"📊 **進捗: {progress_count} / {total_in_scope} 問** ({int(progress_percent * 100)}%)")
    st.progress(progress_percent)
else:
    st.write(f"📝 **復習残り: {len(target_indices)} 問**")

# 新しい問題のセット
if st.session_state.current_question is None:
    idx = random.choice(target_indices)
    row = df.loc[idx]
    
    # 選択肢整理（文章のみを抽出）
    raw_choices = [str(row[2]), str(row[3]), str(row[4]), str(row[5])]
    final_choices = [c for c in raw_choices if c.strip() not in ["ア", "イ", "ウ", "エ"]]
    
    if len(final_choices) < 4:
        final_choices = [str(row[3]), str(row[4]), str(row[5]), str(row[6])]
        symbol_map = {"ア": str(row[3]), "イ": str(row[4]), "ウ": str(row[5]), "エ": str(row[6])}
        correct_ans = symbol_map.get(str(row[2]).strip(), str(row[2]))
        hint_text = str(row[7])
    else:
        correct_ans = str(row[2])
        hint_text = str(row[6])

    random.shuffle(final_choices)
    st.session_state.current_question = {
        'index': idx, 'year': row[0], 'text': row[1],
        'correct_ans': correct_ans, 'choices': final_choices, 'hint': hint_text
    }

# --- 5. クイズ画面表示 ---
q = st.session_state.current_question
st.divider()
st.caption(f"📅 {q['year']} | 管理番号: {q['index']}")
st.markdown(f"### {q['text']}")

answer = st.radio("選択肢を選んでください", q['choices'], key=f"q_{q['index']}")

if st.button("回答する"):
    if answer == q['correct_ans']:
        st.success("✨ 正解！")
        if q['index'] not in st.session_state.solved_indices:
            st.session_state.solved_indices.append(q['index'])
        if q['index'] in st.session_state.wrong_indices:
            st.session_state.wrong_indices.remove(q['index'])
    else:
        st.error(f"❌ 不正解... 正解は「{q['correct_ans']}」でした。")
        if q['index'] not in st.session_state.wrong_indices:
            st.session_state.wrong_indices.append(q['index'])
    
    st.info(f"💡 解説：{q['hint']}")
    
    if st.button("次の問題へ"):
        st.session_state.current_question = None
        st.rerun()
