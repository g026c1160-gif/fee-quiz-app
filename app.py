import streamlit as st
import pandas as pd
import random

# --- 1. データの読み込み ---
@st.cache_data
def load_data():
    df = pd.read_csv('questions.csv', header=None, names=['year_group', 'question', 'ans_key', 'text_a', 'text_i', 'text_u', 'text_e', 'hint'])
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

all_years = sorted(df['year_group'].unique().tolist(), reverse=True)
selected_years = st.sidebar.multiselect("解きたい年度を選択", options=all_years, default=all_years)

selected_mode = st.sidebar.radio("学習モード", ["通常", "復習"])

if st.session_state.last_mode != selected_mode:
    st.session_state.last_mode = selected_mode
    st.session_state.current_question = None
    st.rerun()

st.sidebar.write(f"現在の復習対象: **{len(st.session_state.wrong_indices)}** 問")

if st.sidebar.button("学習記録をリセット"):
    st.session_state.solved_indices = []
    st.session_state.wrong_indices = []
    st.session_state.current_question = None
    st.rerun()

# --- 4. 出題ロジック ---
filtered_df = df[df['year_group'].isin(selected_years)]

if selected_mode == "復習":
    target_indices = [i for i in st.session_state.wrong_indices if i in filtered_df.index]
    if not target_indices:
        st.info("この年度に復習対象はありません。")
        st.stop()
else:
    target_indices = [i for i in filtered_df.index if i not in st.session_state.solved_indices]
    if not target_indices:
        st.success("全ての対象問題を解き終わりました！")
        if st.button("記録をリセット"):
            st.session_state.solved_indices = []
            st.rerun()
        st.stop()

if st.session_state.current_question is None:
    idx = random.choice(target_indices)
    row = df.loc[idx]
    
    # 【解決の核】記号と文章をマッピングする
    # CSVの構成: ans_key(ア), text_a(文章), text_i(文章), text_u(文章), text_e(文章)
    mapping = {
        "ア": str(row['text_a']),
        "イ": str(row['text_i']),
        "ウ": str(row['text_u']),
        "エ": str(row['text_e'])
    }
    
    # 記号（アなど）から正解の文章を特定
    correct_text = mapping.get(str(row['ans_key']).strip(), str(row['ans_key']))
    
    # 選択肢リスト（文章のみ）
    clean_choices = [str(row['text_a']), str(row['text_i']), str(row['text_u']), str(row['text_e'])]
    random.shuffle(clean_choices)
    
    st.session_state.current_question = {
        'index': idx,
        'year': row['year_group'],
        'text': row['question'],
        'correct_ans': correct_text,
        'choices': clean_choices,
        'hint': row['hint']
    }

# --- 5. クイズ画面表示 ---
q = st.session_state.current_question

st.caption(f"📅 {q['year']} | No.{q['index']}")
st.markdown(f"### {q['text']}")

# ラジオボタン。keyに問題インデックスを入れて確実にリセット
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
