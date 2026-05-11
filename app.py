# --- サイドバー設定（ここを微調整） ---
st.sidebar.title("🛠️ 設定")

# 1. 年度選択
all_years = sorted(df['year_group'].unique().tolist(), reverse=True)
selected_years = st.sidebar.multiselect("解きたい年度を選択", options=all_years, default=all_years)

# 2. 学習モード選択
# モードを変えたときに現在の問題をリセットする仕組み
selected_mode = st.sidebar.radio("学習モード", ["通常", "復習"])

# モードが切り替わったら現在の問題をリセットして次にいく
if "last_mode" not in st.session_state:
    st.session_state.last_mode = selected_mode

if st.session_state.last_mode != selected_mode:
    st.session_state.last_mode = selected_mode
    st.session_state.current_question = None
    st.rerun()

st.session_state.mode = selected_mode

# 3. 復習対象の件数を表示（やる気を出すため！）
wrong_count = len(st.session_state.wrong_indices)
st.sidebar.write(f"現在の復習対象: **{wrong_count}** 問")

if st.sidebar.button("学習記録をリセット"):
    st.session_state.solved_indices = []
    st.session_state.wrong_indices = []
    st.session_state.current_question = None
    st.rerun()

# --- フィルタリングロジック（ここも重要） ---
filtered_df = df[df['year_group'].isin(selected_years)]

# 復習モードのときは「間違えた問題」かつ「選択された年度」に絞る
if st.session_state.mode == "復習":
    # 全データの中から間違えたインデックス、かつ選択年度に含まれるもの
    current_wrong_indices = [i for i in st.session_state.wrong_indices if i in filtered_df.index]
    
    if not current_wrong_indices:
        st.sidebar.warning("⚠️ 選択年度に復習対象がありません")
        # 復習対象がない場合は強制的に通常モードの動きにするか、警告を出す
    else:
        # 復習モード用の表示フィルタ
        filtered_df = df.loc[current_wrong_indices]
