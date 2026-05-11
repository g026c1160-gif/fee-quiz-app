import streamlit as st
import pandas as pd
import random
import os
import glob
import re

# --- 1. データの自動集約読み込み ---
@st.cache_data(show_spinner=False, ttl=60) 
def load_all_data():
    df_list = []
    # 既存の全CSVを読み込み
    files = glob.glob("*.csv") + glob.glob("data/*.csv")
    for f in set(files):
        try:
            tmp = pd.read_csv(f, header=None).dropna(how='all')
            df_list.append(tmp)
        except: pass
    
    if not df_list:
        return pd.DataFrame([["設定中", "問題なし", "A", "B", "C", "D", "ヒント"]])
    
    # 結合して重複排除
    df = pd.concat(df_list, axis=0, ignore_index=True).drop_duplicates()

    # 年度ラベルの抽出（「令和3年」や「令和4年」だけを抜き出す）
    def extract_year(text):
        match = re.search(r'(令和\d+年|平成\d+年)', str(text))
        return match.group(0) if match else "その他"

    df['year_label'] = df[0].apply(extract_year)
    return df

st.cache_data.clear()
df = load_all_data()

# --- 2. セッション状態の初期化 ---
if 'solved_indices' not in st.session_state:
    st.session_state.solved_indices = []
if 'wrong_indices' not in st.session_state:
    st.session_state.wrong_indices = []
if 'current_question' not in st.session_state:
    st.session_state.current_question = None
if 'last_selected_years' not in st.session_state:
    st.session_state.last_selected_years = []

# --- 3. サイドバー設定 ---
st.sidebar.title("🛠️ 試験対策設定")

# 正確な年度ごとのユニークな問題数をカウント
year_counts = df['year_label'].value_counts()
unique_years = sorted(year_counts.index.tolist(), reverse=True)
year_options = [f"{y} ({year_counts[y]}問)" for y in unique_years]
year_map = {f"{y} ({year_counts[y]}問)": y for y in unique_years}

selected_options = st.sidebar.multiselect("年度を選択", options=year_options, default=year_options)
selected_years = [year_map[opt] for opt in selected_options]

# 選択が変わったらリセット
if st.session_state.last_selected_years != selected_years:
    st.session_state.last_selected_years = selected_years
    st.session_state.current_question = None
    st.rerun()

if st.sidebar.button("学習記録をリセット"):
    st.session_state.solved_indices = []
    st.session_state.wrong_indices = []
    st.session_state.current_question = None
    st.rerun()

# --- 4. 出題・進捗ロジック ---
filtered_df = df[df['year_label'].isin(selected_years)]
target_indices = [i for i in filtered_df.index if i not in st.session_state.solved_indices]

if not target_indices:
    st.success("🎉 選択した年度の問題をすべて解きました！")
    st.stop()

# --- 5. 問題のセットアップ (解説・選択肢のズレを徹底修正) ---
if st.session_state.current_question is None:
    idx = random.choice(target_indices)
    row = df.loc[idx].values.tolist()
    
    # 1. 選択肢の抽出 (2列目以降から、年度ラベルや空データを除外した純粋なリストを作る)
    # row[0]:管理番号, row[1]:問題文, row[2]:正解/記号, row[3...]:選択肢...
    
    ans_col_val = str(row[2]).strip()
    if ans_col_val in ["ア", "イ", "ウ", "エ"]:
        # 記号形式: [ア, 文, 文, 文, 文]
        symbol_idx = {"ア": 3, "イ": 4, "ウ": 5, "エ": 6}
        correct_ans = str(row[symbol_idx[ans_col_val]])
        choices = [str(row[3]), str(row[4]), str(row[5]), str(row[6])]
    else:
        # 文章形式: [正解文, 誤1, 誤2, 誤3]
        correct_ans = str(row[2])
        choices = [str(row[2]), str(row[3]), str(row[4]), str(row[5])]
    
    # 2. 解説の抽出 (データの末尾から「year_label」を除いた最後の有効な値を採用)
    valid_items = [x for x in row if pd.notna(x) and str(x).strip() != ""]
    # 最後の1つは year_label なので、その前が解説
    hint_text = valid_items[-2] if len(valid_items) > 2 else "解説はありません。"

    random.shuffle(choices)
    st.session_state.current_question = {
        'index': idx, 'year': row[0], 'text': row[1],
        'correct_ans': correct_ans, 'choices': choices, 'hint': hint_text
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
        st.session_state.solved_indices.append(q['index'])
    else:
        st.error(f"❌ 不正解... 正解は「{q['correct_ans']}」")
    
    st.info(f"💡 解説：{q['hint']}")
    if st.button("次の問題へ"):
        st.session_state.current_question = None
        st.rerun()
