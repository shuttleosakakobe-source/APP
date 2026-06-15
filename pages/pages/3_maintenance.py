import streamlit as st
import os
import base64
import urllib.request
import csv
import io

st.set_page_config(page_title="メンテナンス管理(3)", page_icon="icon.png", layout="centered")
st.markdown("<style>[data-testid='stSidebarNav'] {display: none;} header {visibility: hidden;}</style>", unsafe_allow_html=True)

if 'login_status' not in st.session_state or not st.session_state.login_status or st.session_state.user_role != "3":
    st.switch_page("app.py")

@st.cache_data(ttl=0)
def load_sheet_data(custom_url):
    try:
        res = urllib.request.urlopen(custom_url, timeout=10)
        return list(csv.reader(io.StringIO(res.read().decode('utf-8'))))
    except: return None

def get_img_html(file_name, emoji, alert=False):
    border = "5px solid red" if alert else "5px solid transparent"
    if os.path.exists(file_name):
        with open(file_name, "rb") as f: data = base64.b64encode(f.read()).decode()
        return f'<img src="data:image/png;base64,{data}" style="width:85px; aspect-ratio:1/1; object-fit:contain; border-radius:15px; border:{border}; display: block; margin: 0 auto;">'
    return f'<div style="width:85px; aspect-ratio:1/1; background:#f0f2f6; border-radius:15px; display:flex; align-items:center; justify-content:center; font-size:40px; border:{border}; margin: 0 auto;">{emoji}</div>'

st.write(f"👤 **{st.session_state.user_name} さん (権限3)**")
st.write("### 🛠️ メンテナンス管理メニュー")

url1 = "https://docs.google.com/spreadsheets/d/16JhXHMdYPoOIQmPBgd2sVclYkdYip6arRHtr86hr9hg/export?format=csv&gid=1365103622"
url2 = "https://docs.google.com/spreadsheets/d/1DShHig4iOhNXOkxMfALTRhyH0P5dtVpdBkNXvVQPC3g/export?format=csv&gid=1365103622"
url3 = "https://docs.google.com/spreadsheets/d/1kk9vFlE6LiBDMp6B4phUtnGs8CZfV8uhgkS-atdbBG0/export?format=csv&gid=1365103622"

r1, r2, r3 = load_sheet_data(url1), load_sheet_data(url2), load_sheet_data(url3)
a1 = r1 and len(r1) >= 2 and any(c.strip() != "" for c in r1[1][:15])
a2 = r2 and len(r2) >= 2 and any(c.strip() != "" for c in r2[1][:15])
a3 = r3 and len(r3) >= 2 and any(c.strip() != "" for c in r3[1][:15])

if a1 or a2 or a3: st.error("⚠️ 未処理のデータがあります")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f'<a href="https://docs.google.com/spreadsheets/d/16JhXHMdYPoOIQmPBgd2sVclYkdYip6arRHtr86hr9hg/edit?gid=1365103622" target="_blank">{get_img_html("3.png","⚙️",a1)}<p style="font-size:12px; text-align:center; font-weight:bold; color:black; margin-top:8px;">1. 処理</p></a>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<a href="https://docs.google.com/spreadsheets/d/1DShHig4iOhNXOkxMfALTRhyH0P5dtVpdBkNXvVQPC3g/edit?gid=1365103622" target="_blank">{get_img_html("8.png","🔍",a2)}<p style="font-size:12px; text-align:center; font-weight:bold; color:black; margin-top:8px;">2. チェック</p></a>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<a href="https://docs.google.com/spreadsheets/d/1kk9vFlE6LiBDMp6B4phUtnGs8CZfV8uhgkS-atdbBG0/edit?gid=1365103622" target="_blank">{get_img_html("4.png","𖖨️",a3)}<p style="font-size:12px; text-align:center; font-weight:bold; color:black; margin-top:8px;">3. 印刷用</p></a>', unsafe_allow_html=True)

st.write("---")
if st.button("🚪 ログアウト", use_container_width=True):
    from streamlit_javascript import st_javascript
    st_javascript("sessionStorage.clear(); localStorage.clear();")
    st.session_state.login_status = False
    st.switch_page("app.py")
