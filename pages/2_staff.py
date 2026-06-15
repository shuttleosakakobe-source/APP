import streamlit as st
import os
import base64
import urllib.request
import csv
import io
import json
import re
from datetime import datetime, timedelta, timezone

# ページ設定（サイドバーを非表示にする）
st.set_page_config(page_title="スタッフ画面", page_icon="icon.png", layout="centered")
st.markdown("<style>[data-testid='stSidebarNav'] {display: none;} header {visibility: hidden;}</style>", unsafe_allow_html=True)

# セッションが切れていたらログイン画面へ戻す安全装置
if 'login_status' not in st.session_state or not st.session_state.login_status:
    st.switch_page("app.py")

GAS_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwHh3IFsieR8xL5PTTjS6id2slofK-cAVRPOwo0UljCATHHvYjBiXG_YJaNewAcyF-F/exec"

def get_jst_today(): 
    return datetime.now(timezone(timedelta(hours=9))).date()

@st.cache_data(ttl=0)
def load_sheet_data(gid="0"):
    try:
        res = urllib.request.urlopen(f"https://docs.google.com/spreadsheets/d/1cPgQ3Ej3P7JZPaxprFQnbnDkCatQ15lEHyF9C9tMgZ4/export?format=csv&gid={gid}", timeout=10)
        return list(csv.reader(io.StringIO(res.read().decode('utf-8'))))
    except: return None

def parse_flexible_date(s):
    if not s: return None
    c = str(s).strip().split(" ")[0].replace("-", "/")
    m = re.match(r'^(\d{4})/(\d{1,2})/(\d{1,2})', c)
    if m:
        try: return datetime(*map(int, m.groups())).date()
        except: return None
    return None

def get_visit_data(user_code):
    rows = load_sheet_data(gid="370581902")
    if not rows or len(rows) < 3: return {}, "データなし"
    col_idx = -1
    for idx, col in enumerate(rows[0]):
        if str(col).strip().lower().split('.')[0] == str(user_code).strip().lower().split('.')[0]:
            col_idx = idx; break
    if col_idx == -1: return {}, "未登録"
    
    today = get_jst_today()
    today_sched = "なし"
    all_s = []
    for row in rows[2:]:
        if len(row) <= col_idx or not row[col_idx].strip(): continue
        rd = parse_flexible_date(row[0])
        if not rd: continue
        if rd == today: today_sched = row[col_idx].strip()
        all_s.append({"date": rd, "val": row[col_idx].strip(), "type": row[col_idx].strip()[0].upper()})
        
    all_s.sort(key=lambda x: x["date"])
    base_type = next((s["type"] for s in all_s if s["date"] >= today), "A")
    order = ["A", "B", "C", "D"]
    b_idx = order.index(base_type) if base_type in order else 0
    
    v = {"1W": "--/--", "2W": "--/--", "4W": "--/--", "8W": "--/--"}
    f_d = lambda s: f"{s['date'].strftime('%m/%d')}({s['val'][1:]})" if len(s['val']) > 1 else s['date'].strftime('%m/%d')
    
    w1 = next((s for s in all_s if s["date"] >= today and s["type"] == order[(b_idx+1)%4]), None)
    if w1: v["1W"] = f_d(w1)
    w2 = next((s for s in all_s if s["date"] >= today and s["type"] == order[(b_idx+2)%4]), None)
    if w2: v["2W"] = f_d(w2)
    w4 = next((s for s in all_s if (s["date"] > w2["date"] if w2 else s["date"] >= today) and s["type"] == base_type), None)
    if w4:
        v["4W"] = f_d(w4)
        w8 = next((s for s in all_s if s["date"] >= w4["date"] + timedelta(days=14) and s["type"] == base_type), None)
        if w8: v["8W"] = f_d(w8)
    return v, today_sched

def get_img_html(file_name, emoji, alert=False):
    border = "5px solid red" if alert else "5px solid transparent"
    if os.path.exists(file_name):
        with open(file_name, "rb") as f: data = base64.b64encode(f.read()).decode()
        return f'<img src="data:image/png;base64,{data}" style="width:100%; aspect-ratio:1/1; object-fit:contain; border-radius:15px; border:{border}; display: block; margin: 0 auto;">'
    return f'<div style="width:100%; aspect-ratio:1/1; background:#f0f2f6; border-radius:15px; display:flex; align-items:center; justify-content:center; font-size:40px; border:{border}; margin: 0 auto;">{emoji}</div>'

# メイン表示
st.write(f"👤 **{st.session_state.user_name} さん**")
if os.path.exists("1.png"): st.image("1.png", use_container_width=True)

# 🔔 お知らせ（マスターのA2セルから取得）
master = load_sheet_data(gid="0")
announcement = master[1][7] if master and len(master) > 1 and len(master[1]) > 7 else "安全運転でお願いします"
st.markdown(f'<div style="background-color:#fffbe6; border:2px solid #ffe58f; padding:10px; border-radius:10px; display:flex; align-items:center;"><marquee scrollamount="5" style="color:red; font-weight:bold; font-size:16px;">🔔 {announcement}</marquee></div>', unsafe_allow_html=True)

# 🕒 打刻
st.write("### 🕒 勤怠・所在打刻")
c1, c2, c3 = st.columns(3)
click = None
with c1:
    if st.button("🌅 出社", use_container_width=True): click = "出社"
with c2:
    if st.button("🚗 帰社", use_container_width=True): click = "帰社"
with c3:
    if st.button("🌃 退社", use_container_width=True): click = "退社"
if click:
    urllib.request.urlopen(urllib.request.Request(GAS_WEBAPP_URL, data=json.dumps({"status": "TIMECARD", "code": st.session_state.user_code, "name": st.session_state.user_name, "timecard_status": click}).encode('utf-8')))
    st.toast(f"🎉 {click}を記録しました")

# 次回訪問日
visit, today_sched = get_visit_data(st.session_state.user_code)
st.markdown(f'''
    <div style="background:#f4f6f9; padding:12px; border-radius:10px; margin: 10px 0;">
        <div style="font-size:12px; font-weight:bold; color:#409eff;">📅 次回訪問日</div>
        <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:6px; text-align:center; margin: 6px 0;">
            <div style="background:white; padding:4px; border-radius:6px;"><b style="font-size:10px; color:#909399;">1W</b><br><b>{visit.get("1W")}</b></div>
            <div style="background:white; padding:4px; border-radius:6px;"><b style="font-size:10px; color:#909399;">2W</b><br><b>{visit.get("2W")}</b></div>
            <div style="background:white; padding:4px; border-radius:6px;"><b style="font-size:10px; color:#909399;">4W</b><br><b>{visit.get("4W")}</b></div>
            <div style="background:white; padding:4px; border-radius:6px;"><b style="font-size:10px; color:#909399;">8W</b><br><b>{visit.get("8W")}</b></div>
        </div>
        <div style="background:#eef7fe; padding:6px; border-radius:6px; display:flex; justify-content:between;">
            <span style="font-size:11px; font-weight:bold;">📌 本日の予定:</span> <span style="font-size:12px; font-weight:bold; color:red; margin-left:auto;">{today_sched}</span>
        </div>
    </div>
''', unsafe_allow_html=True)

# 未処理アラート確認
needs_alert = False
if master:
    user_row = next((r for r in master if r[0] == st.session_state.user_code), None)
    if user_row and len(user_row) >= 6: needs_alert = user_row[5].strip() not in ["0", "", "None"]

# ボタン4つ
b1, b2, b4, b5 = get_img_html("3.png","📄"), get_img_html("4.png","📋",needs_alert), get_img_html("5.png","🧽"), get_img_html("image_d3349a.png","🎓")
st.markdown(f'''
    <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin:15px 0;">
        <a href="https://docs.google.com/forms/d/e/1FAIpQLSc4E3L_UJkVxMMSTOYgcw3SJyoBixHoJfhe0WC-x1wbK6lsHw/viewform" target="_blank">{b1}<p style="font-size:10px; text-align:center; font-weight:bold; color:black;">メンテ入力</p></a>
        <a href="{st.session_state.user_url}" target="_blank">{b2}<p style="font-size:10px; text-align:center; font-weight:bold; color:black;">メンテ確認</p></a>
        <a href="https://docs.google.com/forms/d/1t_3QDu1sOFXdBvwRzIuwdI1yT0Ez_AunIEXKz_Bds3c/viewform" target="_blank">{b4}<p style="font-size:10px; text-align:center; font-weight:bold; color:black;">スポンジ入力</p></a>
        <a href="https://drive.google.com/drive/folders/1vZE__7Th8RuVtkNQpG-rAZSBtAvG7cTX" target="_blank">{b5}<p style="font-size:10px; text-align:center; font-weight:bold; color:black;">勉強会資料</p></a>
    </div>
''', unsafe_allow_html=True)

st.write("---")
if st.button("🚪 ログアウト", use_container_width=True):
    from streamlit_javascript import st_javascript
    st_javascript("sessionStorage.clear(); localStorage.clear();")
    st.session_state.login_status = False
    st.switch_page("app.py")
