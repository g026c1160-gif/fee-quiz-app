import streamlit as st
import pandas as pd
import random

# --- 1. データの読み込み ---
@st.cache_data
def load_data():
    # questions.csvを読み込み。CSVの列名に合わせて適宜修正してください
    df = pd.read_csv('questions.csv', header=None, names=['year_group', 'question', 'ans', 'choice2', 'choice3', 'choice4', 'hint'])
    return df

df = load_data()

# --- 2. セッション状態（記録）の初期化 ---
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

# 年度選択
all_years = sorted(df['year_group'].unique().tolist(), reverse=True)
selected_years = st.sidebar.multiselect("解きたい年度を選択", options=all_years, default=all_years)

# モード選択（切り替えた瞬間に画面をリセットする）
selected_mode = st.sidebar.radio("学習モード", ["通常", "復習"])

if st.session_state.last_mode != selected_mode:
    st.session_state.last_mode = selected_mode
    st.session_state.current_question = None
    st.rerun()

# 復習対象の件数を表示
wrong_count = len(st.session_state.wrong_indices)
st.sidebar.write(f"現在の復習対象: **{wrong_count}** 問")

if st.sidebar.button("学習記録をリセット"):
    st.session_state.solved_indices = []
    st.session_state.wrong_indices = []
    st.session_state.current_question = None
    st.rerun()

# --- 4. 出題ロジック ---
# 年度でフィルタリング
filtered_df = df[df['year_group'].isin(selected_years)]

# 復習モードの場合は、さらに「間違えた問題」に絞る
if selected_mode == "復習":
    current_wrong_indices = [i for i in st.session_state.wrong_indices if i in filtered_df.index]
    if not current_wrong_indices:
        st.info("この条件に合う復習対象はありません。通常モードで問題を解きましょう！")
        st.stop()
    target_df = df.loc[current_wrong_indices]
else:
    # まだ解いていない問題に絞る
    unsolved_indices = [i for i in filtered_df.index if i not in st.session_state.solved_indices]
    if not unsolved_indices:
        st.success("全ての対象問題を解き終わりました！")
        if st.button("もう一度最初から解く"):
            st.session_state.solved_indices = []
            st.rerun()
        st.stop()
    target_df = df.loc[unsolved_indices]

# 問題の選択
if st.session_state.current_question is None:
    idx = random.choice(target_df.index.tolist())
    row = df.loc[idx]
    
    # 選択肢のシャッフル
    choices = [row['ans'], row['choice2'], row['choice3'], row['choice4']]
    random.shuffle(choices)
    
    st.session_state.current_question = {
        'index': idx,
        'year': row['year_group'],
        'text': row['question'],
        'correct_ans': row['ans'],
        'choices': choices,
        'hint': row['hint']
    }

# --- 5. クイズ画面表示 ---
q = st.session_state.current_question

st.title(f"🚀 {q['year']}")
st.subheader(q['text'])

# 解答選択
answer = st.radio("選択肢を選んでください", q['choices'], key="answer_radio")

if st.button("回答する"):
    if answer == q['correct_ans']:
        st.success("✨ 正解！")
        # 通常モードの場合のみ「解いた」ことにする
        if q['index'] not in st.session_state.solved_indices:
            st.session_state.solved_indices.append(q['index'])
        # 復習モードで正解したらリストから消す
        if q['index'] in st.session_state.wrong_indices:
            st.session_state.wrong_indices.remove(q['index'])
    else:
        st.error(f"❌ 不正解... 正解は「{q['correct_ans']}」でした。")
        # 間違えたリストに追加（重複なし）
        if q['index'] not in st.session_state.wrong_indices:
            st.session_state.wrong_indices.append(q['index'])
    
    st.info(f"💡 解説：{q['hint']}")
    
    if st.button("次の問題へ"):
        st.session_state.current_question = None
        st.rerun()
