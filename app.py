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
@st.cache_data(ttl=600)
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
        img_code = f'data:image/png;base64,{data}'
        return f'<img src="{img_code}" style="width:100%; aspect-ratio:1/1; object-fit:contain; border-radius:15px; border:{border}; {shadow}">'
    return f'<div style="width:100%; aspect-ratio:1/1; background:#f0f2f6; border-radius:15px; display:flex; align-items:center; justify-content:center; font-size:40px; border:{border}; {shadow}">{emoji}</div>'

# --- 4. ログイン維持用関数 ---
def set_login_storage(name, url, alert, role):
    st_javascript(f"localStorage.setItem('shuttle_user_name', '{name}');")
    st_javascript(f"localStorage.setItem('shuttle_user_url', '{url}');")
    st_javascript(f"localStorage.setItem('shuttle_needs_alert', '{alert}');")
    st_javascript(f"localStorage.setItem('shuttle_user_role', '{role}');")

def get_login_storage():
    # JavaScript経由で取得
    name = st_javascript("localStorage.getItem('shuttle_user_name');")
    url = st_javascript("localStorage.getItem('shuttle_user_url');")
    alert = st_javascript("localStorage.getItem('shuttle_needs_alert');")
    role = st_javascript("localStorage.getItem('shuttle_user_role');")
    return name, url, alert, role

# --- 5. メイン画面 ---
def main_screen():
    st.markdown("""
        <style>
        header {visibility: hidden; height: 0px !important;}
        .block-container { padding-top: 0rem !important; padding-bottom: 0rem !important; max-width: 500px; }
        [data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
        .user-label { text-align: right; font-size: 13px; color: #666; font-weight: bold; margin-top: 5px; margin-bottom: 15px; }
        .button-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 5px; }
        @media (max-width: 600px) { .button-grid { grid-template-columns: repeat(2, 1fr); } }
        .btn-item { text-align: center; text-decoration: none; display: block; color: black !important; }
        .btn-text { font-size: 12px; font-weight: bold; margin-top: 3px; line-height: 1.2; }
        footer {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

    # ユーザー名表示
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

    # ボタン生成
    b1 = get_img_html("3.png", "📄")
    b2 = get_img_html("4.png", "📋", alert=st.session_state.needs_alert)
    b3 = get_img_html("5.png", "📢")
    b4 = get_img_html("image_d3349a.png", "🎓")

    grid_html = f'''
        <div class="button-grid">
            <a class="btn-item" href="https://docs.google.com/forms/d/e/1FAIpQLSc4E3L_UJkVxMMSTOYgcw3SJyoBixHoJfhe0WC-x1wbK6lsHw/viewform?usp=sharing" target="_blank">{b1}<p class="btn-text">メンテナンス<br>入力</p></a>
            <a class="btn-item" href="{st.session_state.user_url}" target="_blank">{b2}<p class="btn-text">メンテナンス<br>確認</p></a>
            <a class="btn-item" href="https://www.google.com" target="_blank">{b3}<p class="btn-text">キャンペーン<br>入力</p></a>
            <a class="btn-item" href="https://drive.google.com/drive/folders/1vZE__7Th8RuVtkNQpG-rAZSBtAvG7cTX" target="_blank">{b4}<p class="btn-text">勉強会<br>資料</p></a>
        </div>
    '''
    st.markdown(grid_html, unsafe_allow_html=True)

    # 管理者メニュー
    if st.session_state.user_role == "1" and data:
        st.write("---")
        st.markdown("<p style='font-size:12px; font-weight:bold; color:red;'>⚠️ 管理者メニュー</p>", unsafe_allow_html=True)
        alert_rows = []
        for row in data:
            vals = list(row.values())
            if len(vals) >= 6 and str(vals[5]).strip() != "0" and str(vals[5]).strip() != "":
                alert_rows.append({"name": str(vals[1]), "url": str(vals[3])})
        if alert_rows:
            opts = [f"{r['name']} さんの異常を確認" for r in alert_rows]
            sel = st.selectbox("対象者選択", opts, label_visibility="collapsed")
            st.link_button(f"👉 {sel}を開く", alert_rows[opts.index(sel)]['url'], use_container_width=True)

    st.write("---")
    c1, c2 = st.columns([1, 1])
    with c1:
        if os.path.exists("6.png"): st.image("6.png", width=110)
    with c2:
        if st.button("🚪 ログアウト", use_container_width=True):
            # 完全に消去
            st_javascript("localStorage.clear();")
            st.session_state.clear()
            st.rerun()

# --- 6. ログインロジック ---
if 'login_status' not in st.session_state:
    st.session_state.login_status = False

# ブラウザデータの取得
stored = get_login_storage()

# 【重要】データが "0" や "null" の場合は無視するガード
if stored and not st.session_state.login_status:
    s_name = str(stored[0])
    # 名前が 0, null, None 以外の場合のみ自動ログイン
    if s_name not in ["None", "null", "0", "undefined", ""]:
        st.session_state.user_name = s_name
        st.session_state.user_url = str(stored[1])
        st.session_state.needs_alert = (str(stored[2]) == 'True')
        st.session_state.user_role = str(stored[3])
        st.session_state.login_status = True
        st.rerun()

if st.session_state.login_status:
    main_screen()
else:
    # ログイン画面
    st.markdown("<style>header {visibility: hidden;}</style>", unsafe_allow_html=True)
    if os.path.exists("1.png"): st.image("1.png", use_container_width=True)
    u_code = st.text_input("担当者コード").strip()
    u_pass = st.text_input("パスワード", type="password").strip()
    if st.button("ログイン", use_container_width=True):
        data = load_sheet_data()
        user = next((r for r in data if str(r.get('担当者コード')).strip() == u_code and str(r.get('パスワード')).strip() == u_pass), None) if data else None
        if user:
            vals = list(user.values())
            st.session_state.user_name = user.get('担当者名')
            st.session_state.user_url = user.get('URL')
            st.session_state.needs_alert = (str(vals[5]).strip() != "0")
            st.session_state.user_role = str(vals[6]).strip() if len(vals) >= 7 else "2"
            st.session_state.login_status = True
            # 保存
            set_login_storage(st.session_state.user_name, st.session_state.user_url, st.session_state.needs_alert, st.session_state.user_role)
            st.rerun()
        else:
            st.error("認証失敗")
