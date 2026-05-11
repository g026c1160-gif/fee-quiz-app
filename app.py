import streamlit as st
import pandas as pd
import random
import os
import glob
import re

# --- 1. データの自動集約読み込み ---
@st.cache_data(show_spinner=False)
def load_all_data():
    df_list = []
    # 1. ルートの questions.csv
    if os.path.exists('questions.csv'):
        df_list.append(pd.read_csv('questions.csv', header=None))
    # 2. dataフォルダ内の全CSV
    if os.path.exists('data'):
        for f in glob.glob("data/*.csv"):
            df_list.append(pd.read_csv(f, header=None))
    
    if not df_list:
        return pd.DataFrame([["設定中", "問題が見つかりません", "A", "B", "C", "D", "ヒント"]])
    
    df = pd.concat(df_list, axis=0, ignore_index=True).drop_duplicates()

    # 【重要】1列目から「年度」だけを抽出する処理
    # 「令和5年 問1」から「令和5年」だけを取り出して新しい列(year_label)を作る
    def extract_year(text):
        match = re.search(r'(令和\d+年|平成\d+年)', str(text))
        return match.group(0) if match else str(text)

    df['year_label'] = df[0].apply(extract_year)
    return df

df = load_all_data()

# --- 2. セッション状態の初期化 ---
for key in ['solved_indices', 'wrong_indices', 'current_question']:
    if key not in st.session_state:
        st.session_state[key] = [] if 'indices' in key else None
if 'last_mode' not in st.session_state:
    st.session_state.last_mode = "通常"

# --- 3. サイドバー設定 ---
st.sidebar.title("🛠️ 試験対策設定")

# 【ここが修正ポイント】年度を「令和5年」「令和4年」単位で表示
unique_years = sorted(df['year_label'].unique().tolist(), reverse=True)
selected_years = st.sidebar.multiselect(
    "解きたい年度を選択してください",
    options=unique_years,
    default=unique_years
)

selected_mode = st.sidebar.radio("学習モード", ["通常", "復習"])

# モードや年度の選択が変わったら現在の問題をクリアしてリセット
if st.session_state.last_mode != selected_mode:
    st.session_state.last_mode = selected_mode
    st.session_state.current_question = None
    st.rerun()

st.sidebar.divider()
st.sidebar.write(f"📁 復習対象: **{len(st.session_state.wrong_indices)}** 問")

if st.sidebar.button("学習記録をリセット"):
    st.session_state.solved_indices = []
    st.session_state.wrong_indices = []
    st.session_state.current_question = None
    st.rerun()

# --- 4. 出題・進捗ロジック ---
# 選択された年度でフィルタリング
filtered_df = df[df['year_label'].isin(selected_years)]
total_in_scope = len(filtered_df)

if selected_mode == "復習":
    target_indices = [i for i in st.session_state.wrong_indices if i in filtered_df.index]
    if not target_indices:
        st.info("選択された年度に復習対象はありません。")
        st.stop()
    st.write(f"📝 **復習残り: {len(target_indices)} 問**")
else:
    target_indices = [i for i in filtered_df.index if i not in st.session_state.solved_indices]
    solved_in_scope = [i for i in st.session_state.solved_indices if i in filtered_df.index]
    
    if not target_indices:
        st.success(f"🎉 {'・'.join(selected_years)} の問題をすべて解きました！")
        if st.button("もう一度最初から"):
            st.session_state.solved_indices = []
            st.rerun()
        st.stop()

    progress_count = len(solved_in_scope)
    progress_percent = progress_count / total_in_scope if total_in_scope > 0 else 0
    st.write(f"📊 **進捗: {progress_count} / {total_in_scope} 問** ({int(progress_percent * 100)}%)")
    st.progress(progress_percent)

# --- 5. 問題のセットアップ ---
if st.session_state.current_question is None:
    idx = random.choice(target_indices)
    row = df.loc[idx]
    
    # 選択肢整理
    raw_choices = [str(row[2]), str(row[3]), str(row[4]), str(row[5])]
    final_choices = [c for c in raw_choices if c.strip() not in ["ア", "イ", "ウ", "エ"]]
    
    if len(final_choices) < 4:
        final_choices = [str(row[3]), str(row[4]), str(row[5]), str(row[6])]
        symbol_map = {"ア": str(row[3]), "イ": str(row[4]), "ウ": str(row[5]), "エ": str(row[6])}
        correct_ans = symbol_map.get(str(row[2]).strip(), str(row[2]))
        hint_text = str(row[7]) if len(row) > 7 else str(row[6])
    else:
        correct_ans = str(row[2])
        hint_text = str(row[6])

    random.shuffle(final_choices)
    st.session_state.current_question = {
        'index': idx, 'year': row[0], 'text': row[1],
        'correct_ans': correct_ans, 'choices': final_choices, 'hint': hint_text
    }

# --- 6. クイズ画面表示 ---
q = st.session_state.current_question
st.divider()
st.caption(f"📅 {q['year']}")
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
        st.error(f"❌ 不正解... 正解は「{q['correct_ans']}」")
        if q['index'] not in st.session_state.wrong_indices:
            st.session_state.wrong_indices.append(q['index'])
    st.info(f"💡 解説：{q['hint']}")
    if st.button("次の問題へ"):
        st.session_state.current_question = None
        st.rerun()
