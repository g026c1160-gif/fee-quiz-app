import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="FE過去問道場（年度選択版）", layout="centered")

def load_data():
    # 【修正ポイント】header=None を指定し、namesで列名を固定する
    # これにより、1行目にある問題も欠落せずに読み込めます
    df = pd.read_csv("questions.csv", header=None, names=[
        'year', 'question_text', 'correct_answer', 
        'choice_a', 'choice_b', 'choice_c', 'choice_d', 'explanation'
    ])
    
    # 年度だけを抽出
    df['year_group'] = df['year'].astype(str).str.extract(r'(令和\d+年|平成\d+年)')
    df['year_group'] = df['year_group'].fillna("その他")
    
    # 【修正ポイント】重複や空行によるカウントミスを防ぐため、念のため重複削除
    df = df.drop_duplicates().dropna(subset=['question_text'])
    return df

df = load_data()

# --- 以降、セッション状態の初期化やロジックは変更なし ---

if "solved_indices" not in st.session_state:
    st.session_state.solved_indices = []
if "wrong_indices" not in st.session_state:
    st.session_state.wrong_indices = []
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "mode" not in st.session_state:
    st.session_state.mode = "通常"

def next_question(filtered_df):
    if st.session_state.mode == "復習":
        target_indices = [i for i in filtered_df.index if i in st.session_state.wrong_indices]
        if not target_indices:
            st.warning("この年度の復習対象（間違えた問題）はありません。通常モードに切り替えます。")
            st.session_state.mode = "通常"
            target_indices = [i for i in filtered_df.index if i not in st.session_state.solved_indices]
    else:
        target_indices = [i for i in filtered_df.index if i not in st.session_state.solved_indices]

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
    q = df.loc[next_idx] # indexを正確に指定するためlocを使用
    
    all_choices = {"ア": str(q['choice_a']), "イ": str(q['choice_b']), "ウ": str(q['choice_c']), "エ": str(q['choice_d'])}
    st.session_state.correct_text = all_choices[str(q['correct_answer']).strip()]
    choice_texts = list(all_choices.values())
    random.shuffle(choice_texts)
    
    st.session_state.current_question = q
    st.session_state.current_idx = next_idx
    st.session_state.shuffled_texts = choice_texts
    st.session_state.show_explanation = False
    st.session_state.user_choice_text = None

# --- サイドバー設定以降のUI部分は元のコードと同じ ---
st.sidebar.title("🛠️ 設定")
all_years = sorted(df['year_group'].unique().tolist(), reverse=True)
selected_years = st.sidebar.multiselect("解きたい年度を選択", options=all_years, default=all_years)

new_mode = st.sidebar.radio("学習モード", ["通常", "復習"], index=0 if st.session_state.mode == "通常" else 1)
if new_mode != st.session_state.mode:
    st.session_state.mode = new_mode
    st.session_state.current_question = None
    st.rerun()

filtered_df = df[df['year_group'].isin(selected_years)]

if st.sidebar.button("学習記録をリセット"):
    st.session_state.solved_indices = []
    st.session_state.wrong_indices = []
    st.session_state.current_question = None
    st.rerun()

if not selected_years:
    st.warning("サイドバーから年度を1つ以上選択してください。")
else:
    if st.session_state.current_question is None or \
       st.session_state.current_question['year_group'] not in selected_years:
        next_question(filtered_df)

    q = st.session_state.current_question
    texts = st.session_state.shuffled_texts

    st.title("🛡️ FE過去問道場")
    
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
            if st.session_state.current_idx not in st.session_state.solved_indices:
                st.session_state.solved_indices.append(st.session_state.current_idx)
            if st.session_state.current_idx in st.session_state.wrong_indices:
                st.session_state.wrong_indices.remove(st.session_state.current_idx)
        else:
            st.error(f"❌ **不正解...** \n\n 正解は: \n **{st.session_state.correct_text}**")
            if st.session_state.current_idx not in st.session_state.wrong_indices:
                st.session_state.wrong_indices.append(st.session_state.current_idx)

        st.write(f"**【解説】**\n{q['explanation']}")
        
        if st.button("次の問題へ ➡️"):
            next_question(filtered_df)
            st.rerun()
