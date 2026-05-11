import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="FE過去問道場（年度選択版）", layout="centered")

def load_data():
    # ヘッダーがある前提の読み込みに変更（画像から推測）
    df = pd.read_csv("questions.csv")
    # 年度だけを抽出
    df['year_group'] = df['year'].str.extract(r'(令和\d+年|平成\d+年)')
    df['year_group'] = df['year_group'].fillna("その他")
    return df

df = load_data()

# セッション状態の初期化
if "solved_indices" not in st.session_state:
    st.session_state.solved_indices = []
if "wrong_indices" not in st.session_state:
    st.session_state.wrong_indices = []
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "mode" not in st.session_state:
    st.session_state.mode = "通常"

def next_question(filtered_df):
    # --- ここを修正：モードによって対象を切り替える ---
    if st.session_state.mode == "復習":
        # 復習モード：選択年度の中で、間違えたリストに入っているもの
        target_indices = [i for i in filtered_df.index if i in st.session_state.wrong_indices]
        if not target_indices:
            st.warning("この年度の復習対象（間違えた問題）はありません。通常モードに切り替えます。")
            st.session_state.mode = "通常"
            # 通常モードの対象（未回答）をセット
            target_indices = [i for i in filtered_df.index if i not in st.session_state.solved_indices]
    else:
        # 通常モード：選択年度の中で、まだ正解していないもの
        target_indices = [i for i in filtered_df.index if i not in st.session_state.solved_indices]

    # 全問終了チェック
    if not target_indices:
        if st.session_state.mode == "復習":
            st.success("復習対象をすべて解きました！通常モードに戻ります。")
            st.session_state.mode = "通常"
            st.rerun()
        else:
            st.balloons()
            st.success("選択した年度の問題をすべて解き終わりました！記録をリセットします。")
            st.session_state.solved_indices = []
            st.session_state.current_question = None
            st.rerun()
            return

    next_idx = random.choice(target_indices)
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
st.sidebar.title("🛠️ 設定")
all_years = sorted(df['year_group'].unique().tolist(), reverse=True)
selected_years = st.sidebar.multiselect("解きたい年度を選択", options=all_years, default=all_years)

# ラジオボタンの値をsession_stateと同期
new_mode = st.sidebar.radio("学習モード", ["通常", "復習"], index=0 if st.session_state.mode == "通常" else 1)
if new_mode != st.session_state.mode:
    st.session_state.mode = new_mode
    st.session_state.current_question = None # モードが変わったら問題を出し直す
    st.rerun()

# フィルタリング
filtered_df = df[df['year_group'].isin(selected_years)]

if st.sidebar.button("学習記録をリセット"):
    st.session_state.solved_indices = []
    st.session_state.wrong_indices = []
    st.session_state.current_question = None
    st.rerun()

# --- メインロジック ---
if not selected_years:
    st.warning("サイドバーから年度を1つ以上選択してください。")
else:
    # 現在の問題がない、または年度が変わった場合に次へ
    if st.session_state.current_question is None or \
       st.session_state.current_question['year_group'] not in selected_years:
        next_question(filtered_df)

    q = st.session_state.current_question
    texts = st.session_state.shuffled_texts

    st.title("🛡️ FE過去問道場")
    
    # 進捗表示の微調整
    if st.session_state.mode == "通常":
        st.write(f"📊 通常モード進捗: {len(st.session_state.solved_indices)} / {len(filtered_df)} 問完了")
    else:
        st.write(f"📝 復習モード: 残り {len([i for i in st.session_state.wrong_indices if i in filtered_df.index])} 問")

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
            # 正解したらsolvedに追加
            if st.session_state.current_idx not in st.session_state.solved_indices:
                st.session_state.solved_indices.append(st.session_state.current_idx)
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
            next_question(filtered_df)
            st.rerun()
