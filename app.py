import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="FE過去問道場（20問演習版）", layout="centered")

def load_data():
    # ヘッダーがある前提の読み込み
    df = pd.read_csv("questions.csv")
    df['year_group'] = df['year'].str.extract(r'(令和\d+年|平成\d+年)')
    df['year_group'] = df['year_group'].fillna("その他")
    return df

df = load_data()

# セッション状態の初期化
if "solved_in_set" not in st.session_state:
    st.session_state.solved_in_set = [] # 現在のセットで解いたインデックス
if "wrong_indices" not in st.session_state:
    st.session_state.wrong_indices = [] # 永続的な間違えた問題リスト
if "current_set" not in st.session_state:
    st.session_state.current_set = []   # 現在挑戦中の20問のインデックス
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "mode" not in st.session_state:
    st.session_state.mode = "通常"

def start_new_set(filtered_df):
    """新しい20問セットを作成する"""
    all_indices = filtered_df.index.tolist()
    
    if st.session_state.mode == "復習":
        # 復習モード：全年度の中から間違えたリストにあるものを優先
        target_pool = [i for i in st.session_state.wrong_indices if i in filtered_df.index]
        if not target_pool:
            st.warning("この年度の復習対象はありません。")
            return
    else:
        # 通常モード：全年度からランダム
        target_pool = all_indices

    # 最大20問をランダムに抽出
    sample_size = min(20, len(target_pool))
    st.session_state.current_set = random.sample(target_pool, sample_size)
    st.session_state.solved_in_set = []
    st.session_state.current_question = None
    next_question()

def next_question():
    """現在のセットから次の問題を出す"""
    remaining = [i for i in st.session_state.current_set if i not in st.session_state.solved_in_set]
    
    if not remaining:
        st.session_state.current_question = None
        return

    next_idx = remaining[0] # セットの順番通り、またはrandom.choiceでも可
    q = df.iloc[next_idx]
    
    # 選択肢のシャッフル
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
st.sidebar.title("🛠️ 演習設定")
all_years = sorted(df['year_group'].unique().tolist(), reverse=True)
selected_years = st.sidebar.multiselect("対象年度を選択", options=all_years, default=all_years)

new_mode = st.sidebar.radio("学習モード", ["通常", "復習"])
if new_mode != st.session_state.mode:
    st.session_state.mode = new_mode
    st.session_state.current_set = [] # モード変更でセットをクリア

filtered_df = df[df['year_group'].isin(selected_years)]

if st.sidebar.button("📋 新しい20問セットを開始"):
    if not filtered_df.empty:
        start_new_set(filtered_df)
        st.rerun()
    else:
        st.sidebar.error("年度を選択してください")

if st.sidebar.button("記録をすべてリセット"):
    st.session_state.wrong_indices = []
    st.session_state.current_set = []
    st.rerun()

# --- メインロジック ---
st.title("🛡️ FE過去問道場 (20問演習)")

if not st.session_state.current_set:
    st.info("サイドバーの「新しい20問セットを開始」ボタンを押すとスタートします。")
elif st.session_state.current_question is None and len(st.session_state.solved_in_set) >= len(st.session_state.current_set):
    st.balloons()
    st.success(f"セット完了！ {len(st.session_state.current_set)}問中 {len(st.session_state.current_set)}問解きました。")
    if st.button("次のセットへ"):
        start_new_set(filtered_df)
        st.rerun()
else:
    # 現在の問題がある場合
    if st.session_state.current_question is None:
        next_question()

    q = st.session_state.current_question
    texts = st.session_state.shuffled_texts

    # 進捗表示（プログレスバー）
    progress = len(st.session_state.solved_in_set)
    total = len(st.session_state.current_set)
    st.write(f"📊 セット内進捗: {progress + 1} / {total}")
    st.progress((progress) / total)

    st.info(f"**{q['year']}**")
    st.subheader(q['question_text'])

    col1, col2 = st.columns(2)
    for i, t in enumerate(texts):
        with col1 if i % 2 == 0 else col2:
            if st.button(t, use_container_width=True, key=f"btn_{i}"):
                st.session_state.user_choice_text = t
                st.session_state.show_explanation = True

    if st.session_state.show_explanation and st.session_state.user_choice_text:
        st.divider()
        if st.session_state.user_choice_text == st.session_state.correct_text:
            st.success("⭕ **正解！**")
            # 復習リストから消す
            if st.session_state.current_idx in st.session_state.wrong_indices:
                st.session_state.wrong_indices.remove(st.session_state.current_idx)
        else:
            st.error(f"❌ **不正解...** \n\n 正解は: \n **{st.session_state.correct_text}**")
            # 間違えたら復習リストへ
            if st.session_state.current_idx not in st.session_state.wrong_indices:
                st.session_state.wrong_indices.append(st.session_state.current_idx)

        st.write(f"**【解説】**\n{q['explanation']}")
        
        if st.button("次の問題へ ➡️"):
            st.session_state.solved_in_set.append(st.session_state.current_idx)
            next_question()
            st.rerun()
