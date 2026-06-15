import streamlit as st
import urllib.request
import csv
import io
import os
import base64

# ページ設定
st.set_page_config(
    page_title="ダスキンシャトル 業務アプリ",
    page_icon="icon.png", 
    layout="centered"
)

# ナビゲーションを完全に隠す
st.markdown("<style>[data-testid='stSidebarNav'] {display: none;} header {visibility: hidden;}</style>", unsafe_allow_html=True)

# PWA風のブロック処理
if os.path.exists("icon.png"):
    with open("icon.png", "rb") as f:
        icon_data = base64.b64encode(f.read()).decode()
    block_html = f'''<script>
        let appleLink = parent.document.querySelector("link[rel='apple-touch-icon']");
        if (!appleLink) {{ appleLink = parent.document.createElement("link"); appleLink.rel = "apple-touch-icon"; parent.document.head.appendChild(appleLink); }}
        appleLink.href = "data:image/png;base64,{icon_data}";
    </script>'''
    st.components.v1.html(block_html, height=0, width=0)

# ログイン用ユーザーマスター取得（軽量化のため1分キャッシュ）
@st.cache_data(ttl=60)
def load_user_master():
    url = "https://docs.google.com/spreadsheets/d/1cPgQ3Ej3P7JZPaxprFQnbnDkCatQ15lEHyF9C9tMgZ4/export?format=csv&gid=0"
    try:
        response = urllib.request.urlopen(url, timeout=10)
        content = response.read().decode('utf-8')
        f = io.StringIO(content)
        return list(csv.reader(f))
    except:
        return None

def set_login_storage(name, url, role, code):
    from streamlit_javascript import st_javascript 
    st_javascript(f"sessionStorage.setItem('shuttle_user_name', '{name}');")
    st_javascript(f"sessionStorage.setItem('shuttle_user_url', '{url}');")
    st_javascript(f"sessionStorage.setItem('shuttle_user_role', '{role}');")
    st_javascript(f"sessionStorage.setItem('shuttle_user_code', '{code}');")

# セッション確認
if 'login_status' not in st.session_state: st.session_state.login_status = False

if not st.session_state.login_status:
    from streamlit_javascript import st_javascript 
    local_name = st_javascript("sessionStorage.getItem('shuttle_user_name');")
    local_role = st_javascript("sessionStorage.getItem('shuttle_user_role');")
    local_code = st_javascript("sessionStorage.getItem('shuttle_user_code');")
    local_url = st_javascript("sessionStorage.getItem('shuttle_user_url');")
    
    if local_name and local_role and local_code:
        st.session_state.user_name = str(local_name)
        st.session_state.user_role = str(local_role)
        st.session_state.user_code = str(local_code)
        st.session_state.user_url = str(local_url) if local_url else ""
        st.session_state.login_status = True

# --- 自動ページ割り振り機能 ---
if st.session_state.login_status:
    role = st.session_state.user_role
    if role == "1": 
        st.switch_page("pages/1_manager.py")
    else: 
        # 権限2（一般）およびその他のスタッフはすべてスタッフ画面へ
        st.switch_page("pages/2_staff.py")
else:
    # ログイン画面の表示
    if os.path.exists("1.png"): st.image("1.png", use_container_width=True)
    st.write("### 🔑 業務システム ログイン")
    u_code = st.text_input("担当者コード").strip()
    u_pass = st.text_input("パスワード", type="password").strip()
    
    if st.button("ログイン", type="primary", use_container_width=True):
        raw = load_user_master()
        if raw:
            h = raw[0]
            rows = [dict(zip(h, r)) for r in raw[1:]]
            user = next((r for r in rows if str(r.get('担当者コード')).strip() == u_code and str(r.get('パスワード')).strip() == u_pass), None)
            
            if user:
                vals = list(user.values())
                name = user.get('担当者名')
                url = user.get('URL') or ""
                role = str(vals[6]).strip() if len(vals) >= 7 else "2"
                
                st.session_state.user_name = name
                st.session_state.user_url = url
                st.session_state.user_role = role
                st.session_state.user_code = u_code
                st.session_state.login_status = True
                
                set_login_storage(name, url, role, u_code)
                st.rerun()
            else:
                st.error("担当者コードまたはパスワードが違います")
        else:
            st.error("マスターデータの読み込みに失敗しました")
