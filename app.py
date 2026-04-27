import streamlit as st
import os
import base64
import urllib.request
import csv
import io
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

# --- 画像をHTML化 ---
def get_img_html(file_name, emoji, alert=False):
    border = "5px solid red" if alert else "5px solid transparent"
    shadow = "box-shadow: 0 0 10px red;" if alert else ""
    if os.path.exists(file_name):
        with open(file_name, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        return f'<img src="data:image/png;base64,{data}" style="width:100%; aspect-ratio:1/1; object-fit:contain; border-radius:15px; border:{border}; {shadow}">'
    return f'<div style="width:100%; aspect-ratio:1/1; background:#f0f2f6; border-radius:15px; display:flex; align-items:center; justify-content:center; font-size:40px; border:{border}; {shadow}">{emoji}</div>'

# --- ログイン維持 ---
def set_login_storage(name, url, alert):
    st_javascript(f"localStorage.setItem('shuttle_user_name', '{name}');")
    st_javascript(f"localStorage.setItem('shuttle_user_url', '{url}');")
    st_javascript(f"localStorage.setItem('shuttle_needs_alert', '{alert}');")

def get_login_storage():
    name = st_javascript("localStorage.getItem('shuttle_user_name');")
    url = st_javascript("localStorage.getItem('shuttle_user_url');")
    alert = st_javascript("localStorage.getItem('shuttle_needs_alert');")
    return name, url, alert

# --- メイン画面 ---
def main_screen():
    # CSS調整：最上部を詰め、名前の下に余白を作る
    st.markdown("""
        <style>
        header {visibility: hidden; height: 0px !important;}
        .block-container {
            padding-top: 0rem !important;
            padding-bottom: 0rem !important;
            max-width: 500px;
        }
        [data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
        .stApp { background-color: white; }
        
        /* ユーザー名のラベル：下に少し余白(margin-bottom)を追加 */
        .user-label { 
            text-align: right; 
            font-size: 13px; 
            color: #666; 
            font-weight: bold; 
            margin-top: 5px;
            margin-bottom: 15px; 
        }
        
        .button-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 5px; }
        @media (max-width: 600px) { .button-grid { grid-template-columns: repeat(2, 1fr); } }
        .btn-item { text-align: center; text-decoration: none; display: block; }
        .btn-text { color: black; font-size: 12px; font-weight: bold; margin-top: 3px; line-height: 1.2; }
        footer {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

    # 1. ユーザー名（一番上）
    st.markdown(f"<p class='user-label'>👤 {st.session_state.user_name} さん</p>", unsafe_allow_html=True)
    
    # 2. メインロゴ（1.png）
    if os.path.exists("1.png"):
        st.image("1.png", use_container_width=True)

    # 3. お知らせ
    data = load_sheet_data()
    announcement = data[0].get('お知らせ', '安全運転でお願いします') if data else "安全運転でお願いします"
    st.markdown(f'''
        <div style="background-color:#fffbe6; border:2px solid #ffe58f; padding:6px; border-radius:10px; display:flex; align-items:center; margin-bottom:5px;">
            <span style="font-size:16px; margin-right:8px;">🔔</span>
            <marquee scrollamount="5" style="color:red; font-weight:bold; font-size:16px;">{announcement}</marquee>
        </div>
    ''', unsafe_allow_html=True)

    # 4. ボタン生成
    html_btn1 = get_img_html("3.png", "📄")
    html_btn2 = get_img_html("4.png", "📋", alert=st.session_state.needs_alert)
    html_btn3 = get_img_html("5.png", "📢")
    html_btn4 = get_img_html("image_d3349a.png", "🎓")

    full_html = f'''
        <div class="button-grid">
            <a class="btn-item" href="https://docs.google.com/forms/d/e/1FAIpQLSc4E3L_UJkVxMMSTOYgcw3SJyoBixHoJfhe0WC-x1wbK6lsHw/viewform?usp=sharing" target="_blank">{html_btn1}<p class="btn-text">メンテナンス<br>入力</p></a>
            <a class="btn-item" href="{st.session_state.user_url}" target="_blank">{html_btn2}<p class="btn-text">メンテナンス<br>確認</p></a>
            <a class="btn-item" href="https://www.google.com" target="_blank">{html_btn3}<p class="btn-text">キャンペーン<br>入力</p></a>
            <a class="btn-item" href="https
