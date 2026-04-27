import streamlit as st
import os
import base64
import urllib.request
import csv
import io
# 追加ライブラリ（標準搭載されています）
from streamlit_javascript import st_javascript 

# --- ページ設定 ---
st.set_page_config(
    page_title="ダスキンシャトル北大阪 業務アプリ",
    page_icon="icon.png",
    layout="centered"
)

# --- スプレッドシート取得 ---
def load_sheet_data():
    sheet_url = "https://docs.google.com/spreadsheets/d/1cPgQ3Ej3P7JZPaxprFQnbnDkCatQ15lEHyF9C9tMgZ4/export?format=csv&gid=0"
    try:
        response = urllib.request.urlopen(sheet_url)
        content = response.read().decode('utf-8')
        f = io.StringIO(content)
        reader = csv.DictReader(f)
        return list(reader)
    except:
        return None

def get_img_html(file_name, emoji, alert=False):
    border = "5px solid red" if alert else "5px solid transparent"
    shadow = "box-shadow: 0 0 10px red;" if alert else ""
    if os.path.exists(file_name):
        with open(file_name, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        return f'<img src="data:image/png;base64,{data}" style="width:100%; aspect-ratio:1/1; object-fit:contain; border-radius:15px; border:{border}; {shadow}">'
    return f'<div style="width:100%; aspect-ratio:1/1; background:#f0f2f6; border-radius:15px; display:flex; align-items:center; justify-content:center; font-size:40px; border:{border}; {shadow}">{emoji}</div>'

# --- ログイン維持のための関数 ---
def set_login_storage(name, url, alert):
    # ブラウザ側に保存
    st_javascript(f"localStorage.setItem('shuttle_user_name', '{name}');")
    st_javascript(f"localStorage.setItem('shuttle_user_url', '{url}');")
    st_javascript(f"localStorage.setItem('shuttle_needs_alert', '{alert}');")

def get_login_storage():
    # ブラウザ側から読み込み
    name = st_javascript("localStorage.getItem('shuttle_user_name');")
    url = st_javascript("localStorage.getItem('shuttle_user_url');")
    alert = st_javascript("localStorage.getItem('shuttle_needs_alert');")
    return name, url, alert

# --- メイン画面 ---
def main_screen():
    st.markdown("""
        <style>
        .stApp { background-color: white; }
        .user-label { text-align: right; font-size: 14px; color: #666; font-weight: bold; }
        .button-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 10px; }
        @media (max-width: 600px) { .button-grid { grid-template-columns: repeat(2, 1fr); } }
        .btn-item { text-align: center; text-decoration: none; display: block; }
        .btn-text { color: black; font-size: 12px; font-weight: bold; margin-top: 5px; line-height: 1.2; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"<p class='user-label'>👤 {st.session_state.user_name} さん</p>", unsafe_allow_html=True)
    if os.path.exists("1.png"): st.image("1.png", use_container_width=True)

    data = load_sheet_data()
    announcement = data[0].get('お知らせ', '安全運転で！') if data else "安全運転で！"
    st.markdown(f'<div style="background:#fffbe6; border:2px solid #ffe58f; padding:10px; border-radius:10px; display:flex; align-items:center; margin-bottom:10px;"><span style="font-size:20px; margin-right:10px;">🔔</span><marquee scrollamount="5" style="color:red; font-weight:bold; font-size:18px;">{announcement}</marquee></div>', unsafe_allow_html=True)

    html_btn1 = get_img_html("3.png", "📄")
    html_btn2 = get_img_html("4.png", "📋", alert=st.session_state.needs_alert)
    html_btn3 = get_img_html("5.png", "📢")
    html_btn4 = get_img_html("image_d3349a.png", "🎓")

    full_html = f'''
        <div class="button-grid">
            <a class="btn-item" href="https://docs.google.com/forms/d/e/1FAIpQLSc4E3L_UJkVxMMSTOYgcw3SJyoBixHoJfhe0WC-x1wbK6lsHw/viewform?usp=sharing" target="_blank">{html_btn1}<p class="btn-text">メンテナンス<br>入力</p></a>
            <a class="btn-item" href="{st.session_state.user_url}" target="_blank">{html_btn2}<p class="btn-text">メンテナンス<br>確認</p></a>
            <a class="btn-item" href="https://www.google.com" target="_blank">{html_btn3}<p class="btn-text">キャンペーン<br>入力</p></a>
            <a class="btn-item" href="https://drive.google.com/drive/folders/1vZE__7Th8RuVtkNQpG-rAZSBtAvG7cTX" target="_blank">{html_btn4}<p class="btn-text">勉強会<br>資料</p></a>
        </div>
    '''
    st.markdown(full_html, unsafe_allow_html=True)

    if st.sidebar.button("ログアウト"):
        st_javascript("localStorage.clear();") # ブラウザ保存を消去
        st.session_state.login_status = False
        st.rerun()

# --- ログイン・自動ログイン確認 ---
if 'login_status' not in st.session_state:
    st.session_state.login_status = False

# 自動ログインの試行
stored_name, stored_url, stored_alert = get_login_storage()
if stored_name and not st.session_state.login_status:
    st.session_state.login_status = True
    st.session_state.user_name = stored_name
    st.session_state.user_url = stored_url
    st.session_state.needs_alert = (stored_alert == 'True')

if st.session_state.login_status:
    main_screen()
else:
    # ログイン画面
    if os.path.exists("1.png"): st.image("1.png", use_container_width=True)
    st.markdown("<h2 style='text-align: center;'>ログイン</h2>", unsafe_allow_html=True)
    user_code = st.text_input("担当者コード").strip()
    password = st.text_input("パスワード", type="password").strip()
    if st.button("ログイン", use_container_width=True):
        data = load_sheet_data()
        if data:
            user_match = next((row for row in data if str(row.get('担当者コード')).strip() == user_code and str(row.get('パスワード')).strip() == password), None)
            if user_match:
                st.session_state.login_status = True
                st.session_state.user_name = user_match.get('担当者名')
                st.session_state.user_url = user_match.get('URL')
                
                f_val = list(user_match.values())[5] if len(user_match) >= 6 else "0"
                alert_flag = (str(f_val).strip() != "0" and str(f_val).strip() != "")
                st.session_state.needs_alert = alert_flag
                
                # ブラウザにログイン情報を保存
                set_login_storage(st.session_state.user_name, st.session_state.user_url, alert_flag)
                st.rerun()
            else:
                st.error("コードまたはパスワードが違います")
