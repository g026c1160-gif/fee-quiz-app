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
    if os.path.exists('questions.csv'):
        try: df_list.append(pd.read_csv('questions.csv', header=None))
        except: pass
    if os.path.exists('data'):
        for f in glob.glob("data/*.csv"):
            try: df_list.append(pd.read_csv(f, header=None))
            except: pass
    
    if not df_list:
        return pd.DataFrame([["設定中", "問題が見つかりません", "A", "B", "C", "D", "ヒント"]])
    
    df = pd.concat(df_list, axis=0, ignore_index=True).drop_duplicates()

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
if 'last_mode' not in st.session_state:
    st.session_state.last_mode = "通常"
if 'last_selected_years' not in st.session_state:
    st.session_state.last_selected_years = []

# --- 3. サイドバー設定 ---
st.sidebar.title("🛠️ 試験対策設定")
year_counts = df['year_label'].value_counts()
unique_years = sorted(year_counts.index.tolist(), reverse=True)
year_options = [f"{y} ({year_counts[y]}問)" for y in unique_years]
year_map = {f"{y} ({year_counts[y]}問)": y for y in unique_years}

selected_options = st.sidebar.multiselect("年度を選択", options=year_options, default=year_options)
selected_years = [year_map[opt] for opt in selected_options]

if st.session_state.last_selected_years != selected_years:
    st.session_state.last_selected_years = selected_years
    st.session_state.current_question = None
    st.rerun()

selected_mode = st.sidebar.radio("学習モード", ["通常", "復習"])

if st.session_state.last_mode != selected_mode:
    st.session_state.last_mode = selected_mode
    st.session_state.current_question = None
    st.rerun()

if st.sidebar.button("学習記録をリセット"):
    st.session_state.solved_indices = []
    st.session_state.wrong_indices = []
    st.session_state.current_question = None
    st.rerun()

# --- 4. 出題・進捗ロジック ---
filtered_df = df[df['year_label'].isin(selected_years)]
total_in_scope = len(filtered_df)

if selected_mode == "復習":
    target_indices = [i for i in st.session_state.wrong_indices if i in filtered_df.index]
    if not target_indices:
        st.info("復習対象はありません。")
        st.stop()
else:
    target_indices = [i for i in filtered_df.index if i not in st.session_state.solved_indices]
    if not target_indices:
        st.success("🎉 選択した年度の問題をすべて解きました！")
        st.stop()

# --- 5. 問題のセットアップ (解説列のズレを修正) ---
if st.session_state.current_question is None and len(target_indices) > 0:
    idx = random.choice(target_indices)
    row = df.loc[idx].values.tolist() # 扱いやすいようにリスト化
    
    # 2列目が「ア」などの記号かどうか判定
    ans_key = str(row[2]).strip()
    is_symbol_format = ans_key in ["ア", "イ", "ウ", "エ"]
    
    if is_symbol_format:
        # 記号形式: [0:年度, 1:問題, 2:記号, 3:ア文, 4:イ文, 5:ウ文, 6:エ文, 7:解説...]
        symbol_map = {"ア": row[3], "イ": row[4], "ウ": row[5], "エ": row[6]}
        correct_ans = str(symbol_map.get(ans_key))
        final_choices = [str(row[3]), str(row[4]), str(row[5]), str(row[6])]
        # 解説は一番最後のデータ（空文字を除外した末尾）
        hint_text = [item for item in row if pd.notna(item)][-2] # year_labelの一個前が本物の解説
    else:
        # 通常形式: [0:年度, 1:問題, 2:正解文, 3:誤1, 4:誤2, 5:誤3, 6:解説...]
        correct_ans = str(row[2])
        final_choices = [str(row[2]), str(row[3]), str(row[4]), str(row[5])]
        hint_text = [item for item in row if pd.notna(item)][-2]

    random.shuffle(final_choices)
    st.session_state.current_question = {
        'index': idx, 'year': row[0], 'text': row[1],
        'correct_ans': correct_ans, 'choices': final_choices, 'hint': hint_text
    }

# --- 6. クイズ画面表示 ---
if st.session_state.current_question:
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
        
        # 解説を表示
        st.info(f"💡 解説：{q['hint']}")
        
        if st.button("次の問題へ"):
            st.session_state.current_question = None
            st.rerun()
