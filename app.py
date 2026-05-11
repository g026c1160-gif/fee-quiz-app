import streamlit as st
import pandas as pd
import random

# 1. ページ構成のアプリ化
st.set_page_config(page_title="FE過去問道場 Pro", layout="centered")

# 2. アプリ風のカスタムCSS（UIパーツの装飾のみ）
st.markdown("""
    <style>
    /* 問題文エリアの装飾 */
    .stAlert {
        border-radius: 15px;
    }
    /* 回答ボタンを大きく押しやすく */
    div.stButton > button {
        width: 100%;
        height: 70px;
        font-size: 1.1rem !important;
        border-radius: 12px;
        border: 1px solid #d1d5db;
        background-color: white;
        transition: all 0.2s;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    div.stButton > button:hover {
        border-color: #ff4b4b;
        background-color: #fffafa;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    /* 解説エリア */
    .explanation-box {
        background-color: #f8fafc;
        border-left: 5px solid #64748b;
        padding: 15px;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv("questions.csv")
    df['year_group'] = df['year'].str.extract(r'(令和\d+年)')
    return df

df = load_data()

# セッション状態の初期化（ロジック変更なし）
if "solved_indices" not in st.session_state:
    st.session_state.solved_indices = []
if "wrong_indices" not in st.session_state:
    st.session_state.wrong_indices = []
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "selected_years" not in st.session_state:
    st.session_state.selected_years = []

def next_question(filtered_df):
    target_indices = [i for i in filtered_df.index if i not in st.session_state.solved_indices]

    if st.session_state.get("mode") == "復習":
        target_indices = [i for i in target_indices if i in st.session_state.wrong_indices]
        if not target_indices:
            st.warning("この年度の復習対象の問題はありません。通常モードの問題を表示します。")
            target_indices = [i for i in filtered_df.index if i not in st.session_state.solved_indices]

    if not target_indices:
        st.balloons()
        st.success("選択した年度の問題をすべて解き終わりました！記録をリセットします。")
        st.session_state.solved_indices = []
        target_indices = list(filtered_df.index)
    
    next_idx = random.choice(target_indices)
    q = df.iloc[next_idx]
    
    all_choices = {"ア": str(q['choice_a']), "イ": str(q['choice_b']), "ウ": str(q['choice_c']), "エ": str(q['choice_d'])}
    st.session_state.correct_text = all_choices[q['correct_answer'].strip()]
    choice_texts = list(all_choices.values())
    random.shuffle(choice_texts)
    
    st.session_state.current_question = q
    st.session_state.current_idx = next_idx
    st.session_state.shuffled_texts = choice_texts
    st.session_state.show_explanation = False
    st.session_state.user_choice_text = None

# --- サイドバー設定 ---
st.sidebar.title("🛡️ SETTINGS")
all_years = sorted(df['year_group'].unique().tolist(), reverse=True)
selected_years = st.sidebar.multiselect("解きたい年度を選択", options=all_years, default=all_years)
st.session_state.mode = st.sidebar.radio("学習モード", ["通常", "復習"])

if st.sidebar.button("学習記録をリセット"):
    st.session_state.solved_indices = []
    st.session_state.wrong_indices = []
    st.rerun()

# --- メインロジック ---
filtered_df = df[df['year_group'].isin(selected_years)]

if not selected_years:
    st.warning("サイドバーから年度を1つ以上選択してください。")
else:
    if st.session_state.current_question is None or \
       st.session_state.current_question['year_group'] not in selected_years:
        next_question(filtered_df)

    q = st.session_state.current_question
    texts = st.session_state.shuffled_texts

    # --- UI: ヘッダーエリア ---
    st.title("🛡️ FE過去問道場")
    
    # 進行状況をプログレスバーとメトリクスで表示（UI追加）
    progress_val = len(st.session_state.solved_indices) / len(filtered_df) if len(filtered_df) > 0 else 0
    st.progress(progress_val)
    
    m_col1, m_col2 = st.columns(2)
    m_col1.metric("完了数", f"{len(st.session_state.solved_indices)}問")
    m_col2.metric("復習待ち", f"{len(st.session_state.wrong_indices)}問")

    # --- UI: 問題文エリア ---
    st.markdown("---")
    st.info(f"**{q['year']}**")
    st.markdown(f"### {q['question_text']}")
    st.write("") # スペース

    # --- UI: 回答ボタン（2列レイアウト） ---
    col1, col2 = st.columns(2)
    for i, t in enumerate(texts):
        with col1 if i % 2 == 0 else col2:
            if st.button(t, use_container_width=True, key=f"btn_{i}"):
                st.session_state.user_choice_text = t
                st.session_state.show_explanation = True

    # --- UI: 解説エリア ---
    if st.session_state.show_explanation and st.session_state.user_choice_text:
        st.markdown("---")
        if st.session_state.user_choice_text == st.session_state.correct_text:
            st.success("✨ **正解！**")
            if st.session_state.current_idx in st.session_state.wrong_indices:
                st.session_state.wrong_indices.remove(st.session_state.current_idx)
