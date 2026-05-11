import streamlit as st
import pandas as pd
import random
import re

# 1. ページ設定（検索エンジン向けの説明を追加）
st.set_page_config(
    page_title="FE過去問道場 Pro | 基本情報技術者試験 演習",
    page_icon="🛡️",
    layout="centered"
)

# 2. Google Search Console 確認用メタタグ（必要に応じてcontentの中身を書き換えてください）
st.markdown('<meta name="google-site-verification" content="YourCodeHere" />', unsafe_allow_html=True)

@st.cache_data
def load_data():
    try:
        # header=Noneで1行目から読み込み、空行を除去
        df = pd.read_csv("questions.csv", header=None).dropna(how='all')
        df.columns = ['year', 'question_text', 'correct_answer', 'choice_a', 'choice_b', 'choice_c', 'choice_d', 'explanation']
        
        # 文字列として扱い、前後の空白を削除
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            
        # 年度グループ作成
        df['year_group'] = df['year'].str.extract(r'(令和\d+年|平成\d+年)').fillna("その他")
        return df
    except Exception as e:
        st.error(f"CSVの読み込みに失敗しました。ファイル形式を確認してください: {e}")
        return pd.DataFrame()

df = load_data()

# セッション状態の初期化
if "solved_indices" not in st.session_state: st.session_state.solved_indices = []
if "wrong_indices" not in st.session_state: st.session_state.wrong_indices = []
if "current_question" not in st.session_state: st.session_state.current_question = None
if "mode" not in st.session_state: st.session_state.mode = "通常"

def clean_text(text):
    """選択肢の冒頭にある 'ア：' や 'ア.' などを完全に除去する"""
    return re.sub(r'^[ア-エ][：:．.\s]+', '', str(text)).strip()

def next_question(filtered_df):
    if st.session_state.mode == "復習":
        target_indices = [i for i in filtered_df.index if i in st.session_state.wrong_indices]
        if not target_indices:
            st.session_state.mode = "通常"
            target_indices = [i for i in filtered_df.index if i not in st.session_state.solved_indices]
    else:
        target_indices = [i for i in filtered_df.index if i not in st.session_state.solved_indices]

    if not target_indices:
        if st.session_state.mode == "通常": st.balloons()
        st.session_state.solved_indices = []
        st.session_state.current_question = None
        st.rerun()

    next_idx = random.choice(target_indices)
    q = df.loc[next_idx]
    
    # 選択肢のクリーニングと辞書化
    all_choices = {
        "ア": clean_text(q['choice_a']),
        "イ": clean_text(q['choice_b']),
        "ウ": clean_text(q['choice_c']),
        "エ": clean_text(q['choice_d'])
    }
    
    # 正解テキストの取得（KeyError対策）
    ans_key = q['correct_answer']
    st.session_state.correct_text = all_choices.get(ans_key, "データエラー")
    
    st.session_state.current_question = q
    st.session_state.current_idx = next_idx
    st.session_state.shuffled_texts = random.sample(list(all_choices.values()), 4)
    st.session_state.show_explanation = False
    st.session_state.user_choice_text = None

# --- UI ---
st.sidebar.title("🛡️ SETTINGS")
all_years = sorted(df['year_group'].unique().tolist(), reverse=True)
selected_years = st.sidebar.multiselect("年度選択", options=all_years, default=all_years)
st.session_state.mode = st.sidebar.radio("学習モード", ["通常", "復習"])

if st.sidebar.button("記録リセット"):
    st.session_state.solved_indices = []
    st.session_state.wrong_indices = []
    st.rerun()

filtered_df = df[df['year_group'].isin(selected_years)]

if not selected_years or filtered_df.empty:
    st.warning("年度を選択してください")
else:
    if st.session_state.current_question is None or st.session_state.current_question['year_group'] not in selected_years:
        next_question(filtered_df)

    q = st.session_state.current_question
    
    st.title("🛡️ FE過去問道場")
    st.progress(len(st.session_state.solved_indices) / len(filtered_df) if len(filtered_df)>0 else 0)
    
    st.info(f"**{q['year']}**")
    st.markdown(f"### {q['question_text']}")

    cols = st.columns(2)
    for i, t in enumerate(st.session_state.shuffled_texts):
        with cols[i % 2]:
            if st.button(t, key=f"btn_{i}", use_container_width=True):
                st.session_state.user_choice_text = t
                st.session_state.show_explanation = True

    if st.session_state.show_explanation:
        st.divider()
        if st.session_state.user_choice_text == st.session_state.correct_text:
            st.success("✅ **正解！**")
            if st.session_state.current_idx not in st.session_state.solved_indices:
                st.session_state.solved_indices.append(st.session_state.current_idx)
            if st.session_state.current_idx in st.session_state.wrong_indices:
                st.session_state.wrong_indices.remove(st.session_state.current_idx)
        else:
            st.error(f"❌ **不正解**（正解: {st.session_state.correct_text}）")
            if st.session_state.current_idx not in st.session_state.wrong_indices:
                st.session_state.wrong_indices.append(st.session_state.current_idx)

        st.info(f"**【解説】**\n\n{q['explanation']}")
        if st.button("次の問題へ ➡️", type="primary"):
            next_question(filtered_df)
            st.rerun()
