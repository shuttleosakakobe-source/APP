import streamlit as st
st.write("### 🚀 マルチページのテスト画面")
st.write("pagesフォルダの中のファイルが正常に読み込まれました！")
if st.button("ログイン画面に戻る"):
    st.switch_page("app.py")
