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
@st.cache_data(ttl=0)
def load_sheet_data(gid="0"):
    base_url = "https://docs.google.com/spreadsheets/d/1cPgQ3Ej3P7JZPaxprFQnbnDkCatQ15lEHyF9C9tMgZ4/export?format=csv&gid="
    check_sheet_url = "https://docs.google.com/spreadsheets/d/1EofzMjd3dAq8sRCdQXpxw3_-T1VDWpd-aDrvxWD4fYc/export?format=csv&gid=1552856942"
    
    target_url = check_sheet_url if gid == "1552856942" else f"{base_url}{gid}"
    
    try:
        response = urllib.request.urlopen(target_url)
        content = response.read().decode('utf-8')
        f = io.StringIO(content)
        reader = csv.reader(f)
        return list(reader)
    except:
        return None

# --- 3. 画像をHTML化する関数 ---
def get_img_html(file_name, emoji, alert=False, width="100%"):
    border = "5px solid red" if alert else "5px solid transparent"
    shadow = "box-shadow: 0 0 15px red; filter: drop-shadow(0 0 5px red);" if alert else ""
    if os.path.exists(file_name):
        with open(file_name, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        img_code = f'data:image/png;base64,{data}'
        return f'<img src="{img_code}" style="width:{width}; aspect-ratio:1/1; object-fit:contain; border-radius:15px; border:{border}; {shadow}; display: block; margin: 0 auto;">'
    return f'<div style="width:{width}; aspect-ratio:1/1; background:#f0f2f6; border-radius:15px; display:flex; align-items:center; justify-content:center; font-size:40px; border:{border}; {shadow}; margin: 0 auto;">{emoji}</div>'

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

# --- 5. メイン画面 ---
def main_screen():
    st.markdown("""
        <style>
        header {visibility: hidden; height: 0px !important;}
        .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; max-width: 500px; }
        [data-testid="stVerticalBlock"] { gap: 1.2rem !important; }
        .user-label { text-align: right; font-size: 13px; color: #666; font-weight: bold; margin-bottom: 5px; }
        .button-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 15px 0; }
        @media (max-width: 600px) { .button-grid { grid-template-columns: repeat(2, 1fr); } }
        .btn-item { text-align: center; text-decoration: none; display: block; color: black !important; }
        .btn-text { font-size: 12px; font-weight: bold; line-height: 1.2; text-align: center; width: 100%; }
        footer {visibility: hidden;}
        hr { margin: 1.2rem 0 !important; }
        .alert-text { color: red; font-weight: bold; font-size: 14px; margin-bottom: 8px; display: block; text-align: center; }
        .admin-box { display: flex; flex-direction: column; align-items: center; justify-content: flex-start; }
        </style>
    """, unsafe_allow_html=True)

    data_raw = load_sheet_data(gid="0")
    header = data_raw[0]
    data = [dict(zip(header, row)) for row in data_raw[1:]]
    
    current_user_data = next((r for r in data if r.get('担当者名') == st.session_state.user_name), None)
    if current_user_data:
        vals = list(current_user_data.values())
        st.session_state.needs_alert = (str(vals[5]).strip() not in ["0", "", "None"])

    st.markdown(f"<p class='user-label'>👤 {st.session_state.user_name} さん</p>", unsafe_allow_html=True)
    if os.path.exists("1.png"): st.image("1.png", use_container_width=True)

    announcement = data[0].get('お知らせ', '安全運転でお願いします')
    st.markdown(f'''
        <div style="background-color:#fffbe6; border:2px solid #ffe58f; padding:10px; border-radius:10px; display:flex; align-items:center; margin-top: 5px;">
            <span style="font-size:16px; margin-right:8px;">🔔</span>
            <marquee scrollamount="5" style="color:red; font-weight:bold; font-size:16px;">{announcement}</marquee>
        </div>
    ''', unsafe_allow_html=True)

    # 管理者エリア
    if st.session_state.user_role == "1":
        check_sheet_rows = load_sheet_data(gid="1552856942")
        check_alert = False
        if check_sheet_rows and len(check_sheet_rows) >= 2:
            target_cells = check_sheet_rows[1][:10]
            if any(cell.strip() != "" for cell in target_cells):
                check_alert = True
        
        alert_rows = []
        for row in data:
            vals = list(row.values())
            if len(vals) >= 6 and str(vals[5]).strip() not in ["0", "", "None"]:
                alert_rows.append({"name": str(vals[1]), "url": str(vals[3])})

        if check_alert or alert_rows:
            st.write("") 
            col_admin1, col_admin2 = st.columns([1.2, 2])
            
            with col_admin1:
                c_btn = get_img_html("8.png", "🔍", alert=check_alert, width="90px")
                check_url = "https://docs.google.com/spreadsheets/d/1EofzMjd3dAq8sRCdQXpxw3_-T1VDWpd-aDrvxWD4fYc/edit?gid=1552856942#gid=1552856942"
                st.markdown(f'''
                    <div class="admin-box">
                        <a href="{check_url}" target="_blank" style="text-decoration:none; color:black;">
                            {c_btn}
                            <p class="btn-text" style="margin-top: 12px;">メンテナンス<br>チェック</p>
                        </a>
                    </div>
                ''', unsafe_allow_html=True)
            
            with col_admin2:
                if alert_rows:
                    st.markdown('<span class="alert-text">⚠️ メンテナンス未処理</span>', unsafe_allow_html=True)
                    opts = [f"{r['name']} さん" for r in alert_rows]
                    sel = st.selectbox("対象を選択", opts, label_visibility="collapsed")
                    st.link_button(f"👉 確認を開く", alert_rows[opts.index(sel)]['url'], use_container_width=True)

    # 🔘 メインボタン 4つ
    b1 = get_img_html("3.png", "📄")
    b2 = get_img_html("4.png", "📋", alert=st.session_state.needs_alert)
    b3 = get_img_html("5.png", "📢")
    b4 = get_img_html("image_d3349a.png", "🎓")

    # 元の状態：hrefに{st.session_state.user_url}を使用する形に戻しました
    grid_html = f'''
        <div class="button-grid">
            <a class="btn-item" href="https://docs.google.com/forms/d/e/1FAIpQLSc4E3L_UJkVxMMSTOYgcw3SJyoBixHoJfhe0WC-x1wbK6lsHw/viewform?usp=sharing" target="_blank">{b1}<p class="btn-text" style="margin-top:6px;">メンテナンス<br>入力</p></a>
            <a class="btn-item" href="{st.session_state.user_url}" target="_blank">{b2}<p class="btn-text" style="margin-top:6px;">メンテナンス<br>確認</p></a>
            <a class="btn-item" href="https://www.google.com" target="_blank">{b3}<p class="btn-text" style="margin-top:6px;">キャンペーン<br>入力</p></a>
            <a class="btn-item" href="https://drive.google.com/drive/folders/1vZE__7Th8RuVtkNQpG-rAZSBtAvG7cTX" target="_blank">{b4}<p class="btn-text" style="margin-top:6px;">勉強会<br>資料</p></a>
        </div>
    '''
    st.markdown(grid_html, unsafe_allow_html=True)

    st.write("---")
    col1, col2 = st.columns([1, 1])
    with col1:
        if os.path.exists("6.png"): st.image("6.png", width=110)
    with col2:
        if st.button("🚪 ログアウト", use_container_width=True):
            st_javascript("localStorage.clear();")
            st.session_state.login_status = False
            st.session_state.logout_requested = True
            st.rerun()

# --- 6. 実行ロジック ---
if 'login_status' not in st.session_state: st.session_state.login_status = False
if 'logout_requested' not in st.session_state: st.session_state.logout_requested = False

if not st.session_state.login_status and not st.session_state.logout_requested:
    stored = get_login_storage()
    if stored and str(stored[0]) not in ["None", "null", "0", "undefined", ""]:
        st.session_state.user_name = str(stored[0])
        st.session_state.user_url = str(stored[1])
        st.session_state.needs_alert = (str(stored[2]) == 'True')
        st.session_state.user_role = str(stored[3])
        st.session_state.login_status = True
        st.rerun()

if st.session_state.login_status:
    main_screen()
else:
    if os.path.exists("1.png"): st.image("1.png", use_container_width=True)
    u_code = st.text_input("担当者コード").strip()
    u_pass = st.text_input("パスワード", type="password").strip()
    if st.button("ログイン", use_container_width=True):
        raw = load_sheet_data(gid="0")
        h = raw[0]
        rows = [dict(zip(h, r)) for r in raw[1:]]
        user = next((r for r in rows if str(r.get('担当者コード')).strip() == u_code and str(r.get('パスワード')).strip() == u_pass), None)
        if user:
            vals = list(user.values())
            st.session_state.user_name = user.get('担当者名')
            st.session_state.user_url = user.get('URL')
            st.session_state.needs_alert = (str(vals[5]).strip() not in ["0", ""])
            st.session_state.user_role = str(vals[6]).strip() if len(vals) >= 7 else "2"
            st.session_state.login_status = True
            st.session_state.logout_requested = False
            set_login_storage(st.session_state.user_name, st.session_state.user_url, st.session_state.needs_alert, st.session_state.user_role)
            st.rerun()
        else: st.error("認証失敗")
