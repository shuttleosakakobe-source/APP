import streamlit as st
import urllib.request
import csv
import io
import os
import base64
import json
import re
from datetime import datetime, timedelta, timezone

# 1. ページ設定（ナビゲーションやヘッダーを完全に隠す）
st.set_page_config(page_title="ダスキンシャトル 業務アプリ", page_icon="icon.png", layout="centered")
st.markdown("<style>[data-testid='stSidebarNav'] {display: none;} header {visibility: hidden;}</style>", unsafe_allow_html=True)

GAS_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwHh3IFsieR8xL5PTTjS6id2slofK-cAVRPOwo0UljCATHHvYjBiXG_YJaNewAcyF-F/exec"

def get_jst_today(): 
    return datetime.now(timezone(timedelta(hours=9))).date()

# PWA風のブロック処理
if os.path.exists("icon.png"):
    with open("icon.png", "rb") as f: icon_data = base64.b64encode(f.read()).decode()
    st.components.v1.html(f'<script>let appleLink = parent.document.querySelector("link[rel=\'apple-touch-icon\']"); if (!appleLink) {{ appleLink = parent.document.createElement("link"); appleLink.rel = "apple-touch-icon"; parent.document.head.appendChild(appleLink); }} appleLink.href = "data:image/png;base64,{icon_data}";</script>', height=0, width=0)

# スプレッドシートデータ取得（キャッシュ0で常に最新）
@st.cache_data(ttl=0)
def load_sheet_data(gid="0", custom_url=None):
    url = custom_url if custom_url else f"https://docs.google.com/spreadsheets/d/1cPgQ3Ej3P7JZPaxprFQnbnDkCatQ15lEHyF9C9tMgZ4/export?format=csv&gid={gid}"
    if gid == "1552856942":
        url = "https://docs.google.com/spreadsheets/d/1EofzMjd3dAq8sRCdQXpxw3_-T1VDWpd-aDrvxWD4fYc/export?format=csv&gid=1552856942"
    try:
        res = urllib.request.urlopen(url, timeout=10)
        return list(csv.reader(io.StringIO(res.read().decode('utf-8'))))
    except: return None

def post_to_gas(payload):
    try:
        req = urllib.request.Request(GAS_WEBAPP_URL, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=10) as r: return json.loads(r.read().decode('utf-8'))
    except: return {"status": "error"}

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

def get_img_html(file_name, emoji, alert=False, width="100%"):
    border = "5px solid red" if alert else "5px solid transparent"
    if os.path.exists(file_name):
        with open(file_name, "rb") as f: data = base64.b64encode(f.read()).decode()
        return f'<img src="data:image/png;base64,{data}" style="width:{width}; aspect-ratio:1/1; object-fit:contain; border-radius:15px; border:{border}; display: block; margin: 0 auto;">'
    return f'<div style="width:{width}; aspect-ratio:1/1; background:#f0f2f6; border-radius:15px; display:flex; align-items:center; justify-content:center; font-size:40px; border:{border}; margin: 0 auto;">{emoji}</div>'

@st.dialog("⚠️ 業務完了の確認")
def confirm_task_dialog(task_name):
    st.write(f"**「{task_name}」** を完了にしますか？")
    if st.button("👍 はい（完了）", type="primary", use_container_width=True):
        with st.status("送信中...") as s:
            res = post_to_gas({"status": "COMPLETE_TASK", "code": st.session_state.user_code, "name": st.session_state.user_name, "task": task_name})
            if res.get("status") == "success":
                s.update(label="完了！", state="complete")
                st.session_state["task_completed_trigger"] = task_name
                st.rerun()
            else: s.update(label="エラー", state="error")

def logout_action():
    from streamlit_javascript import st_javascript 
    st_javascript("sessionStorage.clear(); localStorage.clear();")
    st.session_state.login_status = False
    st.rerun()

# ログインセッションの管理
if 'login_status' not in st.session_state: st.session_state.login_status = False

if not st.session_state.login_status:
    from streamlit_javascript import st_javascript 
    local_name = st_javascript("sessionStorage.getItem('shuttle_user_name');")
    local_role = st_javascript("sessionStorage.getItem('shuttle_user_role');")
    local_code = st_javascript("sessionStorage.getItem('shuttle_user_code');")
    local_url = st_javascript("sessionStorage.getItem('shuttle_user_url');")
    if local_name and local_role and local_code:
        st.session_state.user_name, st.session_state.user_role, st.session_state.user_code, st.session_state.user_url = str(local_name), str(local_role), str(local_code), (str(local_url) if local_url else "")
        st.session_state.login_status = True

# --- 2. ログインに成功している場合の画面出し分け処理 ---
if st.session_state.login_status:
    role = st.session_state.user_role
    
    # ----------------------------------------
    # 【権限 0：最上位管理者画面】
    # ----------------------------------------
    if role == "0":
        st.write(f"👤 **{st.session_state.user_name} 管理者 (権限0)**")
        if os.path.exists("1.png"): st.image("1.png", use_container_width=True)
        
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
            post_to_gas({"status": "TIMECARD", "code": st.session_state.user_code, "name": st.session_state.user_name, "timecard_status": click})
            st.toast(f"{click}を記録しました")
            
        st.write("### 🛠️ メンテナンス管理メニュー")
        r1 = load_sheet_data(custom_url="https://docs.google.com/spreadsheets/d/16JhXHMdYPoOIQmPBgd2sVclYkdYip6arRHtr86hr9hg/export?format=csv&gid=1365103622")
        r2 = load_sheet_data(custom_url="https://docs.google.com/spreadsheets/d/1DShHig4iOhNXOkxMfALTRhyH0P5dtVpdBkNXvVQPC3g/export?format=csv&gid=1365103622")
        r3 = load_sheet_data(custom_url="https://docs.google.com/spreadsheets/d/1kk9vFlE6LiBDMp6B4phUtnGs8CZfV8uhgkS-atdbBG0/export?format=csv&gid=1365103622")
        if (r1 and len(r1) >= 2 and any(c.strip()!="" for c in r1[1][:15])) or (r2 and len(r2) >= 2 and any(c.strip()!="" for c in r2[1][:15])) or (r3 and len(r3) >= 2 and any(c.strip()!="" for c in r3[1][:15])):
            st.error("⚠️ 未処理のデータがあります")
            
        col1, col2, col3 = st.columns(3)
        with col1: st.markdown(f'<a href="https://docs.google.com/spreadsheets/d/16JhXHMdYPoOIQmPBgd2sVclYrapYkdYip6arRHtr86hr9hg/edit?gid=1365103622" target="_blank">{get_img_html("3.png","⚙️",False,"75px")}<p style="font-size:11px; text-align:center;">1.処理</p></a>', unsafe_allow_html=True)
        with col2: st.markdown(f'<a href="https://docs.google.com/spreadsheets/d/1DShHig4iOhNXOkxMfALTRhyH0P5dtVpdBkNXvVQPC3g/edit?gid=1365103622" target="_blank">{get_img_html("8.png","🔍",False,"75px")}<p style="font-size:11px; text-align:center;">2.チェック</p></a>', unsafe_allow_html=True)
        with col3: st.markdown(f'<a href="https://docs.google.com/spreadsheets/d/1kk9vFlE6LiBDMp6B4phUtnGs8CZfV8uhgkS-atdbBG0/edit?gid=1365103622" target="_blank">{get_img_html("4.png","𖖨️",False,"75px")}<p style="font-size:11px; text-align:center;">3.印刷用</p></a>', unsafe_allow_html=True)
        
        st.write("### 📅 業務チェックリスト")
        if "task_completed_trigger" in st.session_state: st.toast(f"✅ 「{st.session_state.pop('task_completed_trigger')}」を記録しました！")
        am_items = ["【データ抽出】 データ抽出 (38)...", "【実績管理】 日次確認...", "【実績管理】 日次締...", "【実績管理】 実績送信...", "【発注】 クローバー返却...", "【レンタルサービス準備】 出庫表...", "【帳票出力】 1400...", "【発注状況一覧照会】 TAN1D...", "【入出庫・在庫管理】 担当者別出庫...", "【棚卸調査票】...", "【メンテ終了後】 追加発注...", "【メンテ終了後】 実績表出力...", "【メンテ終了後】 納品書...", "【メンテ終了後】 帳票出力..."]
        res = post_to_gas({"status": "GET_CHECKLIST", "date": get_jst_today().strftime("%Y-%m-%d")})
        completed_tasks = set(res.get("completed", [])) if res.get("status") == "success" else set()
        t1, t2 = st.tabs(["🌅 AM業務", "🌇 PM業務"])
        with t1:
            for i in [x for x in am_items if x not in completed_tasks]:
                if st.button(f"⬜ {i}", key=f"am_{i}", use_container_width=True): confirm_task_dialog(i)
        with t2:
            for i in [x for x in ["【メンテチェック終了後】 定期発注...", "【メンテチェック終了後】 追加発注..."] if x not in completed_tasks]:
                if st.button(f"⬜ {i}", key=f"pm_{i}", use_container_width=True): confirm_task_dialog(i)
                
        st.write("---")
        if st.button("🚪 ログアウト", use_container_width=True): logout_action()

    # ----------------------------------------
    # 【権限 1：管理者・チーフ画面】
    # ----------------------------------------
    elif role == "1":
        st.write(f"👤 **{st.session_state.user_name} さん (権限1)**")
        check_rows = load_sheet_data(gid="1552856942")
        check_alert = check_rows and len(check_rows) >= 2 and any(c.strip() != "" for c in check_rows[1][:10])
        col1, col2 = st.columns(2)
        with col1: st.markdown(f'<div style="text-align:center;"><a href="https://docs.google.com/spreadsheets/d/1EofzMjd3dAq8sRCdQXpxw3_-T1VDWpd-aDrvxWD4fYc/edit?gid=1552856942" target="_blank">{get_img_html("8.png","🔍",check_alert,"90px")}<p style="font-size:12px; font-weight:bold; margin-top:8px;">メンテナンス<br>チェック</p></a></div>', unsafe_allow_html=True)
        with col2: st.markdown(f'<div style="text-align:center;"><a href="https://docs.google.com/spreadsheets/d/1CUviW0AH8UdG4ZdF2CkuHh9NJKVM2NAYfXi8omQb3xE/edit?gid=0" target="_blank">{get_img_html("5.png","📊",False,"90px")}<p style="font-size:12px; font-weight:bold; margin-top:8px;">スポンジ<br>キャンペーンチェック</p></a></div>', unsafe_allow_html=True)
        
        master = load_sheet_data(gid="0")
        if master:
            alert_rows = [{"name": str(r[1]), "url": str(r[3])} for r in master[1:] if len(r) >= 6 and str(r[5]).strip() not in ["0", "", "None"]]
            if alert_rows:
                st.write("---")
                st.error("⚠️ メンテナンス未処理のスタッフがいます")
                sel = st.selectbox("対象を選択", [f"{r['name']} さん" for r in alert_rows], label_visibility="collapsed")
                st.link_button(f"👉 確認を開く", alert_rows[[f"{r['name']} さん" for r in alert_rows].index(sel)]['url'], use_container_width=True)
                
        st.write("---")
        if st.button("🚪 ログアウト", use_container_width=True): logout_action()

    # ----------------------------------------
    # 【権限 3：メンテナンス専用画面】
    # ----------------------------------------
    elif role == "3":
        st.write(f"👤 **{st.session_state.user_name} さん (権限3)**")
        st.write("### 🛠️ メンテナンス管理メニュー")
        r1 = load_sheet_data(custom_url="https://docs.google.com/spreadsheets/d/16JhXHMdYPoOIQmPBgd2sVclYkdYip6arRHtr86hr9hg/export?format=csv&gid=1365103622")
        r2 = load_sheet_data(custom_url="https://docs.google.com/spreadsheets/d/1DShHig4iOhNXOkxMfALTRhyH0P5dtVpdBkNXvVQPC3g/export?format=csv&gid=1365103622")
        r3 = load_sheet_data(custom_url="https://docs.google.com/spreadsheets/d/1kk9vFlE6LiBDMp6B4phUtnGs8CZfV8uhgkS-atdbBG0/export?format=csv&gid=1365103622")
        if (r1 and len(r1) >= 2 and any(c.strip()!="" for c in r1[1][:15])) or (r2 and len(r2) >= 2 and any(c.strip()!="" for c in r2[1][:15])) or (r3 and len(r3) >= 2 and any(c.strip()!="" for c in r3[1][:15])):
            st.error("⚠️ 未処理のデータがあります")
        col1, col2, col3 = st.columns(3)
        with col1: st.markdown(f'<a href="https://docs.google.com/spreadsheets/d/16JhXHMdYPoOIQmPBgd2sVclYkdYip6arRHtr86hr9hg/edit?gid=1365103622" target="_blank">{get_img_html("3.png","⚙️",False)}<p style="font-size:12px; text-align:center; font-weight:bold; color:black; margin-top:8px;">1. 処理</p></a>', unsafe_allow_html=True)
        with col2: st.markdown(f'<a href="https://docs.google.com/spreadsheets/d/1DShHig4iOhNXOkxMfALTRhyH0P5dtVpdBkNXvVQPC3g/edit?gid=1365103622" target="_blank">{get_img_html("8.png","🔍",False)}<p style="font-size:12px; text-align:center; font-weight:bold; color:black; margin-top:8px;">2. チェック</p></a>', unsafe_allow_html=True)
        with col3: st.markdown(f'<a href="https://docs.google.com/spreadsheets/d/1kk9vFlE6LiBDMp6B4phUtnGs8CZfV8uhgkS-atdbBG0/edit?gid=1365103622" target="_blank">{get_img_html("4.png","𖖨️",False)}<p style="font-size:12px; text-align:center; font-weight:bold; color:black; margin-top:8px;">3. 印刷用</p></a>', unsafe_allow_html=True)
        
        st.write("---")
        if st.button("🚪 ログアウト", use_container_width=True): logout_action()

    # ----------------------------------------
    # 【権限 2：一般スタッフ画面（超軽量・メイン）】
    # ----------------------------------------
    else:
        st.write(f"👤 **{st.session_state.user_name} さん**")
        if os.path.exists("1.png"): st.image("1.png", use_container_width=True)
        
        # 🔔 お知らせ表示
        master = load_sheet_data(gid="0")
        announcement = master[1][7] if master and len(master) > 1 and len(master[1]) > 7 else "安全運転でお願いします"
        st.markdown(f'<div style="background-color:#fffbe6; border:2px solid #ffe58f; padding:10px; border-radius:10px; display:flex; align-items:center;"><marquee scrollamount="5" style="color:red; font-weight:bold; font-size:16px;">🔔 {announcement}</marquee></div>', unsafe_allow_html=True)
        
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
        st.markdown(f'''<div style="background:#f4f6f9; padding:12px; border-radius:10px; margin: 10px 0;"><div style="font-size:12px; font-weight:bold; color:#409eff;">📅 次回訪問日</div><div style="display:grid; grid-template-columns:repeat(4,1fr); gap:6px; text-align:center; margin: 6px 0;"><div style="background:white; padding:4px; border-radius:6px;"><b style="font-size:10px; color:#909399;">1W</b><br><b>{visit.get("1W")}</b></div><div style="background:white; padding:4px; border-radius:6px;"><b style="font-size:10px; color:#909399;">2W</b><br><b>{visit.get("2W")}</b></div><div style="background:white; padding:4px; border-radius:6px;"><b style="font-size:10px; color:#909399;">4W</b><br><b>{visit.get("4W")}</b></div><div style="background:white; padding:4px; border-radius:6px;"><b style="font-size:10px; color:#909399;">8W</b><br><b>{visit.get("8W")}</b></div></div><div style="background:#eef7fe; padding:6px; border-radius:6px; display:flex; justify-content:between;"><span style="font-size:11px; font-weight:bold;">📌 本日の予定:</span> <span style="font-size:12px; font-weight:bold; color:red; margin-left:auto;">{today_sched}</span></div></div>''', unsafe_allow_html=True)
        
        needs_alert = False
        if master:
            user_row = next((r for r in master if r[0] == st.session_state.user_code), None)
            if user_row and len(user_row) >= 6: needs_alert = user_row[5].strip() not in ["0", "", "None"]
            
        b1, b2, b4, b5 = get_img_html("3.png","📄"), get_img_html("4.png","📋",needs_alert), get_img_html("5.png","🧽"), get_img_html("image_d3349a.png","🎓")
        st.markdown(f'<div style="display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin:15px 0;"><a href="https://docs.google.com/forms/d/e/1FAIpQLSc4E3L_UJkVxMMSTOYgcw3SJyoBixHoJfhe0WC-x1wbK6lsHw/viewform" target="_blank">{b1}<p style="font-size:10px; text-align:center; font-weight:bold; color:black;">メンテ入力</p></a><a href="{st.session_state.user_url}" target="_blank">{b2}<p style="font-size:10px; text-align:center; font-weight:bold; color:black;">メンテ確認</p></a><a href="https://docs.google.com/forms/d/1t_3QDu1sOFXdBvwRzIuwdI1yT0Ez_AunIEXKz_Bds3c/viewform" target="_blank">{b4}<p style="font-size:10px; text-align:center; font-weight:bold; color:black;">スポンジ入力</p></a><a href="https://drive.google.com/drive/folders/1vZE__7Th8RuVtkNQpG-rAZSBtAvG7cTX" target="_blank">{b5}<p style="font-size:10px; text-align:center; font-weight:bold; color:black;">勉強会資料</p></a></div>', unsafe_allow_html=True)
        
        st.write("---")
        if st.button("🚪 ログアウト", use_container_width=True): logout_action()

# --- 3. ログインしていない場合の画面（最初のログイン画面） ---
else:
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
                st.session_state.user_name = user.get('担当者名')
                st.session_state.user_url = user.get('URL') or ""
                st.session_state.user_role = str(vals[6]).strip() if len(vals) >= 7 else "2"
                st.session_state.user_code = u_code
                st.session_state.login_status = True
                
                from streamlit_javascript import st_javascript 
                st_javascript(f"sessionStorage.setItem('shuttle_user_name', '{st.session_state.user_name}'); sessionStorage.setItem('shuttle_user_url', '{st.session_state.user_url}'); sessionStorage.setItem('shuttle_user_role', '{st.session_state.user_role}'); sessionStorage.setItem('shuttle_user_code', '{u_code}');")
                st.rerun()
            else: st.error("担当者コードまたはパスワードが違います")
        else: st.error("マスターデータの読み込みに失敗しました")
