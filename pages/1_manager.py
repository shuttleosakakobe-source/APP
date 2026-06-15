import streamlit as st
import os
import base64
import urllib.request
import csv
import io

st.set_page_config(page_title="管理者画面(1)", page_icon="icon.png", layout="centered")
st.markdown("<style>[data-testid='stSidebarNav'] {display: none;} header {visibility: hidden;}</style>", unsafe_allow_html=True)

if 'login_status' not in st.session_state or not st.session_state.login_status or st.session_state.user_role != "1":
    st.switch_page("app.py")

@st.cache_data(ttl=0)
def load_sheet_data(gid="0"):
    url = f"https://docs.google.com/spreadsheets/d/1cPgQ3Ej3P7JZPaxprFQnbnDkCatQ15lEHyF9C9tMgZ4/export?format=csv&gid={gid}"
    if gid == "1552856942":
        url = "https://docs.google.com/spreadsheets/d/1EofzMjd3dAq8sRCdQXpxw3_-T1VDWpd-aDrvxWD4fYc/export?format=csv&gid=1552856942"
    try:
        res = urllib.request.urlopen(url, timeout=10)
        return list(csv.reader(io.StringIO(res.read().decode('utf-8'))))
    except: return None

def get_img_html(file_name, emoji, alert=False, width="90px"):
    border = "5px solid red" if alert else "5px solid transparent"
    if os.path.exists(file_name):
        with open(file_name, "rb") as f: data = base64.b64encode(f.read()).decode()
        return f'<img src="data:image/png;base64,{data}" style="width:{width}; aspect-ratio:1/1; object-fit:contain; border-radius:15px; border:{border}; display: block; margin: 0 auto;">'
    return f'<div style="width:{width}; aspect-ratio:1/1; background:#f0f2f6; border-radius:15px; display:flex; align-items:center; justify-content:center; font-size:40px; border:{border}; margin: 0 auto;">{emoji}</div>'

st.write(f"👤 **{st.session_state.user_name} さん (権限1)**")

check_rows = load_sheet_data(gid="1552856942")
check_alert = check_rows and len(check_rows) >= 2 and any(c.strip() != "" for c in check_rows[1][:10])

col1, col2 = st.columns(2)
with col1:
    st.markdown(f'<div style="text-align:center;"><a href="https://docs.google.com/spreadsheets/d/1EofzMjd3dAq8sRCdQXpxw3_-T1VDWpd-aDrvxWD4fYc/edit?gid=1552856942" target="_blank">{get_img_html("8.png","🔍",check_alert)}<p style="font-size:12px; font-weight:bold; margin-top:8px;">メンテナンス<br>チェック</p></a></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div style="text-align:center;"><a href="https://docs.google.com/spreadsheets/d/1CUviW0AH8UdG4ZdF2CkuHh9NJKVM2NAYfXi8omQb3xE/edit?gid=0" target="_blank">{get_img_html("5.png","📊",False)}<p style="font-size:12px; font-weight:bold; margin-top:8px;">スポンジ<br>キャンペーンチェック</p></a></div>', unsafe_allow_html=True)

master = load_sheet_data(gid="0")
if master:
    h = master[0]
    alert_rows = []
    for r in [dict(zip(h, row)) for row in master[1:]]:
        vals = list(r.values())
        if len(vals) >= 6 and str(vals[5]).strip() not in ["0", "", "None"]:
            alert_rows.append({"name": str(vals[1]), "url": str(vals[3])})
    if alert_rows:
        st.write("---")
        st.error("⚠️ メンテナンス未処理のスタッフがいます")
        opts = [f"{r['name']} さん" for r in alert_rows]
        sel = st.selectbox("対象を選択", opts, label_visibility="collapsed")
        st.link_button(f"👉 確認を開く", alert_rows[opts.index(sel)]['url'], use_container_width=True)

st.write("---")
if st.button("🚪 ログアウト", use_container_width=True):
    from streamlit_javascript import st_javascript
    st_javascript("sessionStorage.clear(); localStorage.clear();")
    st.session_state.login_status = False
    st.switch_page("app.py")
