import streamlit as st
import pandas as pd
import random
import os

# ページ設定
st.set_page_config(page_title="FE過去問道場", layout="centered")

def load_data():
    # ファイルの存在確認
    if not os.path.exists("questions.csv"):
        st.error("questions.csv が見つかりません。リポジトリにアップロードしてください。")
        return pd.DataFrame()
    
    df = pd.read_csv("questions.csv")
    # 年度抽出（令和・平成）
    df['year_group'] = df['year'].str.extract(r'(令和\d+年|平成\d+年)')
    df['year_group'] = df['year_group'].fillna("その他")
    return df

df = load_data()

# --- セッション状態の初期化 ---
if "total_solved" not in st.session_state:
    st.session_state.total_solved = [] 
if "wrong_indices" not in st.session_state:
    st.session_state.wrong_indices = [] 
if "current_set" not in st.session_state:
    st.session_state.current_set = []   
if "solved_in_set" not in st.session_state:
    st.session_state.solved_in_set = [] 
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "mode" not in st.session_state:
    st.session_state.mode = "通常"

def start_new_set(filtered_df):
    all_indices = filtered_df.index.tolist()
    
    if st.session_state.mode == "復習":
        target_pool = [i for i in st.session_state.wrong_indices if i in filtered_df.index]
        if not target_pool:
            st.warning("この年度の復習対象（間違えた問題）はありません。")
            return
    else:
        # 通常モード：一度正解した問題（total_solved）を除外
        target_pool = [i for i in all_indices if i not in st.session_state.total_solved]
        
        if not target_pool:
            st.balloons()
            st.success("おめでとうございます！選択した年度の全問題を解ききりました！")
            return

    sample_size = min(20, len(target_pool))
    st.session_state.current_set = random.sample(target_pool, sample_size)
    st.session_state.solved_in_set = []
    st.session_state.current_question = None
    next_question()

def next_question():
    remaining = [i for i in st.session_state.current_set if i not in st.session_state.solved_in_set]
    if not remaining:
        st.session_state.current_question = None
        return

    next_idx = remaining[0]
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

# --- UI構築 ---
st.sidebar.title("🛠️ 演習設定")
if not df.empty:
    all_years = sorted(df['year_group'].unique().tolist(), reverse=True)
    selected_years = st.sidebar.multiselect("対象年度を選択", options=all_years, default=all_years)
    new_mode = st.sidebar.radio("学習モード", ["通常", "復習"])
    if new_mode != st.session_state.mode:
        st.session_state.mode = new_mode
        st.session_state.current_set = []

    filtered_df = df[df['year_group'].isin(selected_years)]

    if st.sidebar.button("📋 新しい20問セットを開始"):
        if not filtered_df.empty:
            start_new_set(filtered_df)
            st.rerun()
        else:
            st.sidebar.error("年度を選択してください")

    if st.sidebar.button("🧹 記録をすべてリセット"):
        st.session_state.total_solved = []
        st.session_state.wrong_indices = []
        st.session_state.current_set = []
        st.session_state.current_question = None
        st.rerun()

    # --- メイン表示 ---
    st.title("🛡️ FE過去問道場")
    
    # 全体進捗
    total_in_scope = len(filtered_df)
    solved_in_scope = len([i for i in st.session_state.total_solved if i in filtered_df.index])
    st.caption(f"現在の選択範囲: 未回答 {total_in_scope - solved_in_scope}問 / 苦手 {len(st.session_state.wrong_indices)}問")

    if not st.session_state.current_set:
        st.info("サイドバーから条件を設定して、20問演習を開始してください。")
    elif st.session_state.current_question is None and len(st.session_state.solved_in_set) >= len(st.session_state.current_set):
        st.balloons()
        st.success("セット完了！")
        if st.button("次のセットへ ➡️"):
            start_new_set(filtered_df)
            st.rerun()
    else:
        if st.session_state.current_question is None:
            next_question()

        q = st.session_state.current_question
        texts = st.session_state.shuffled_texts

        st.write(f"📊 セット進捗: {len(st.session_state.solved_in_set) + 1} / {len(st.session_state.current_set)}")
        st.progress(len(st.session_state.solved_in_set) / len(st.session_state.current_set))

        st.info(f"**{q['year']}**")
        st.subheader(q['question_text'])

        col1, col2 = st.columns(2)
        for i, t in enumerate(texts):
            with col1 if i % 2 == 0 else col2:
                if st.button(t, use_container_width=True, key=f"btn_{i}", disabled=st.session_state.show_explanation):
                    st.session_state.user_choice_text = t
                    st.session_state.show_explanation = True
                    st.rerun()

        if st.session_state.show_explanation:
            st.divider()
            if st.session_state.user_choice_text == st.session_state.correct_text:
                st.success("⭕ 正解！")
                if st.session_state.current_idx not in st.session_state.total_solved:
                    st.session_state.total_solved.append(st.session_state.current_idx)
                if st.session_state.current_idx in st.session_state.wrong_indices:
                    st.session_state.wrong_indices.remove(st.session_state.current_idx)
            else:
                st.error(f"❌ 不正解...\n\n正解は: **{st.session_state.correct_text}**")
                if st.session_state.current_idx not in st.session_state.wrong_indices:
                    st.session_state.wrong_indices.append(st.session_state.current_idx)

            st.write(f"**【解説】**\n{q['explanation']}")
            if st.button("次の問題へ ➡️"):
                st.session_state.solved_in_set.append(st.session_state.current_idx)
                next_question()
                st.rerun()
