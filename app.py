import streamlit as st
import os
import base64
import urllib.request
import csv
import io
from streamlit_javascript import st_javascript 

# --- 1. ページ設定 ---
st.set_page_config(
    page_title="ダスキンシャトル北大阪 業務アプリ",
    page_icon="icon.png",
    layout="centered"
)

# --- 2. スプレッドシート取得関数 ---
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

# --- 3. 画像をHTML化する関数 ---
def get_img_html(file_name, emoji, alert=False):
    border = "5px solid red" if alert else "5px solid transparent"
    shadow = "box-shadow: 0 0 10px red;" if alert else ""
    if os.path.exists(file_name):
        with open(file_name, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        return f'<img src="data:image/png;base64,{data}" style="width:100%; aspect-ratio:1/1; object-fit:contain; border-radius:15px; border:{border}; {shadow}">'
    return f'<div style="width:100%; aspect-ratio:1/1; background:#f0f2f6; border-radius:15px; display:flex; align-items:center; justify-content:center; font-size:40px; border:{border}; {shadow}">{emoji}</div>'

# --- 4. ログイン維持用関数 ---
def set_login_storage(name, url, alert, role):
    st_javascript(f"localStorage.setItem('shuttle_user_name', '{name}');")
    st_javascript(f"localStorage.setItem('shuttle_user_url', '{url}');")
    st_javascript(f"localStorage.setItem('shuttle_needs_alert', '{alert}');")
    st_javascript(f"localStorage.setItem('shuttle_user_role', '{role}');")

def get_login_storage():
    name = st_javascript("localStorage.getItem('shuttle_user_name');")
    url = st_javascript("localStorage.getItem('shuttle_user_url');")
    alert = st_javascript("localStorage.getItem('shuttle_needs_alert');")
    role = st_javascript("localStorage.getItem('shuttle_user_role');")
    return name, url, alert, role

# --- 5. メイン画面の表示 ---
def main_screen():
    st.markdown("""
        <style>
        header {visibility: hidden; height: 0px !important;}
        .block-container { padding-top: 0rem !important; padding-bottom: 0rem !important; max-width: 500px; }
        [data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
        .stApp { background-color: white; }
        .user-label { text-align: right; font-size: 13px; color: #666; font-weight: bold; margin-top: 5px; margin-bottom: 15px; }
        .button-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 5px; }
        @media (max-width: 600px) { .button-grid { grid-template-columns: repeat(2, 1fr); } }
        .btn-item { text-align: center; text-decoration: none; display: block; }
        .btn-text { color: black; font-size: 12px; font-weight: bold; margin-top: 3px; line-height: 1.2; }
        footer {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"<p class='user-label'>👤 {st.session_state.user_name} さん</p>", unsafe_allow_html=True)
    
    if os.path.exists("1.png"):
        st.image("1.png", use_container_width=True)

    data = load_sheet_data()
    announcement = data[0].get('お知らせ', '安全運転でお願いします') if data else "安全運転でお願いします"
    
    st.markdown(f'''
        <div style="background-color:#fffbe6; border:2px solid #ffe58f; padding:6px; border-radius:10px; display:flex; align-items:center; margin-bottom:5px;">
            <span style="font-size:16px; margin-right:8px;">🔔</span>
            <marquee scrollamount="5" style="color:red; font-weight:bold; font-size:16px;">{announcement}</marquee>
        </div>
    ''', unsafe_allow_html=True)

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

    if st.session_state.user_role == "1" and data:
        st.write("---")
        st.markdown("<p style='font-size:12px; font-weight:bold; color:red; margin-bottom:0px;'>⚠️ 管理者メニュー：メンテナンス異常一覧</p>", unsafe_allow_html=True)
        alert_rows = []
        for row in data:
            vals = list(row.values())
            if len(vals) >= 6:
                f_val = str(vals[5]).strip()
                d_url = str(vals[3]).strip()
                name = str(vals[1]).strip()
                if f_val != "0" and f_val != "" and d_url.startswith("http"):
                    alert_rows.append({"name": name, "url": d_url})
        if alert_rows:
            options = [f"{r['name']} さんの異常を確認" for r in alert_rows]
            selected = st.selectbox("対象者を選択してください", options, label_visibility="collapsed")
            target_url = alert_rows[options.index(selected)]['url']
            st.link_button(f"👉 {selected}を開く", target_url, use_container_width=True)
        else:
            st.info("現在、メンテナンス異常のスタッフはいません。")

    if os.path.exists("6.png"):
        st.image("6.png", width=110)
    
    if st.sidebar.button("ログアウト"):
        st_javascript("localStorage.clear();")
        st.session_state.clear()
        st.rerun()

# --- 6. ログインチェック・自動ログインロジック ---
if 'login_status' not in st.session_state:
    st.session_state.login_status = False

# ブラウザから情報を取得
stored_name, stored_url, stored_alert, stored_role = get_login_storage()

# 情報を読み込めた場合のセッション反映（PC版での不具合対策）
if stored_name and not st.session_state.login_status:
    # 読み込んだ瞬間にセッションを書き換え
    st.session_state.login_status = True
    st.session_state.user_name = str(stored_name)
    st.session_state.user_url = str(stored_url)
    st.session_state.needs_alert = (str(stored_alert) == 'True')
    st.session_state.user_role = str(stored_role)
    st.rerun() # ここで再起動させることでメイン画面を確実に出す

# 画面表示の分岐
if st.session_state.login_status:
    main_screen()
else:
    # ログイン画面
    st.markdown("<style>header {visibility: hidden;} .block-container {padding-top: 1rem !important;}</style>", unsafe_allow_html=True)
    if os.path.exists("1.png"): st.image("1.png", use_container_width=True)
    st.markdown("<h3 style='text-align: center;'>ログイン</h3>", unsafe_allow_html=True)
    u_code = st.text_input("担当者コード", key="login_code").strip()
    u_pass = st.text_input("パスワード", type="password", key="login_pass").strip()
    
    if st.button("ログイン", use_container_width=True):
        data = load_sheet_data()
        if data:
            user = next((row for row in data if str(row.get('担当者コード')).strip() == u_code and str(row.get('パスワード')).strip() == u_pass), None)
            if user:
                vals = list(user.values())
                st.session_state.login_status = True
                st.session_state.user_name = user.get('担当者名')
                st.session_state.user_url = user.get('URL')
                alert_flag = (str(vals[5]).strip() != "0" and str(vals[5]).strip() != "") if len(vals) >= 6 else False
                st.session_state.needs_alert = alert_flag
                role = str(vals[6]).strip() if len(vals) >= 7 else "2"
                st.session_state.user_role = role
                set_login_storage(st.session_state.user_name, st.session_state.user_url, alert_flag, role)
                st.rerun()
            else:
                st.error("ログイン情報が正しくありません")
