import streamlit as st
import os
import base64
import urllib.request
import csv
import io
import json
import re
from datetime import datetime, timedelta, timezone

# ページ設定（サイドバーとヘッダーを非表示にする）
st.set_page_config(page_title="管理者メニュー(0)", page_icon="icon.png", layout="centered")
st.markdown("<style>[data-testid='stSidebarNav'] {display: none;} header {visibility: hidden;}</style>", unsafe_allow_html=True)

# セッションまたは権限がなければログインへ強制送還（リロード対策）
if 'login_status' not in st.session_state or not st.session_state.login_status or st.session_state.user_role != "0":
    st.switch_page("app.py")

GAS_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwHh3IFsieR8xL5PTTjS6id2slofK-cAVRPOwo0UljCATHHvYjBiXG_YJaNewAcyF-F/exec"

def get_jst_today():
    return datetime.now(timezone(timedelta(hours=9))).date()

@st.cache_data(ttl=0)
def load_sheet_data(gid="0", custom_url=None):
    target_url = custom_url if custom_url else f"https://docs.google.com/spreadsheets/d/1cPgQ3Ej3P7JZPaxprFQnbnDkCatQ15lEHyF9C9tMgZ4/export?format=csv&gid={gid}"
    if gid == "1552856942":
        target_url = "https://docs.google.com/spreadsheets/d/1EofzMjd3dAq8sRCdQXpxw3_-T1VDWpd-aDrvxWD4fYc/export?format=csv&gid=1552856942"
    try:
        res = urllib.request.urlopen(target_url, timeout=10)
        return list(csv.reader(io.StringIO(res.read().decode('utf-8'))))
    except: return None

def post_to_gas(payload):
    try:
        req = urllib.request.Request(GAS_WEBAPP_URL, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=10) as r: return json.loads(r.read().decode('utf-8'))
    except: return {"status": "error"}

def get_img_html(file_name, emoji, alert=False, width="100%"):
    border = "5px solid red" if alert else "5px solid transparent"
    if os.path.exists(file_name):
        with open(file_name, "rb") as f: data = base64.b64encode(f.read()).decode()
        return f'<img src="data:image/png;base64,{data}" style="width:{width}; aspect-ratio:1/1; object-fit:contain; border-radius:15px; border:{border}; display: block; margin: 0 auto;">'
    return f'<div style="width:{width}; aspect-ratio:1/1; background:#f0f2f6; border-radius:15px; display:flex; align-items:center; justify-content:center; font-size:40px; border:{border}; margin: 0 auto;">{emoji}</div>'

def process_logout():
    from streamlit_javascript import st_javascript 
    st_javascript("sessionStorage.clear(); localStorage.clear();")
    st.session_state.login_status = False
    st.switch_page("app.py")

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

@st.fragment(run_every=10)
def render_daily_checklist():
    st.write("### 📅 業務チェックリスト")
    if "task_completed_trigger" in st.session_state:
        st.toast(f"✅ 「{st.session_state.pop('task_completed_trigger')}」を記録しました！")
    
    am_items = ["【データ抽出】 データ抽出 (38) ※※※代行手数料27%、32%と異なる実績抽出→検索", "【実績管理】 日次確認 [700→790→78] (①→F1→F9 / ②→F1→F8)", "【実績管理】 日次締 [700→792] (①→入金合計のみ / ②→実績日と以降の休日分)", "【実績管理】 実績送信 [700→734] (①→②表示しない → 全選択①→F1)", "【発注】 クローバー返却 [F1] (出力なし)", "【レンタルサービス準備】 出庫表・ピッキングリスト [300→333] (①→出庫表[翌日日付] / ②→ピッキング表[発注済最終日付])", "【帳票出力】 1400→ (1.日次→Ent→Ent→1印刷 / 1.出庫表 / 1.ピッキング表 [店舗合計] / 1.ピッキング表→F1)", "【発注状況一覧照会】 TAN1D引当数 [400→411] (③売切商品→出庫予定日[発注済最終日付] → 商品[TAN1D]→F1→F7印刷)", "【入出庫・在庫管理】 担当者別出庫 [500→511] (1.全て選択→F1 ※紙は出ない)", "【棚卸調査票】 [500→582] (1：日時→2：RFDIアプリ →F1印刷)", "【**メンテ終了後**】 追加発注 [400→422] (①→F1)", "【**メンテ終了後**】 実績表出力 [指定店のみ] (売上納品実績→日にち[実績日]→検索・決定→検索→画面印刷) ※プレイヤーズ", "【**メンテ終了後**】 納品書 [300→331] (日付[前日発送分]→F1)", "【**メンテ終了後**】 帳票出力 [1400→] (1.日次→Ent→Ent→1印刷 / 1.納品書)"]
    pm_items = ["【**メンテチェック終了後**】 定期発注 [400→421] 日付（発注済翌日〜発注日） Ｆ１→定期発注実行確認→Ｆ１", "【**メンテチェック終了後**】 追加発注 [400→422] ①→Ｆ１ 【あればその都度】"]
    
    res = post_to_gas({"status": "GET_CHECKLIST", "date": get_jst_today().strftime("%Y-%m-%d")})
    completed_tasks = set(res.get("completed", [])) if res.get("status") == "success" else set()
    
    t1, t2 = st.tabs(["🌅 AM業務", "🌇 PM業務"])
    with t1:
        rem = [i for i in am_items if i not in completed_tasks]
        if not rem: st.success("AM業務完了！")
        for i in rem:
            if st.button(f"⬜ {i}", key=f"am_{i}", use_container_width=True): confirm_task_dialog(i)
    with t2:
        rem = [i for i in pm_items if i not in completed_tasks]
        if not rem: st.success("PM業務完了！")
        for i in rem:
            if st.button(f"⬜ {i}", key=f"pm_{i}", use_container_width=True): confirm_task_dialog(i)

# --- 画面描画 ---
st.write(f"👤 **{st.session_state.user_name} 管理者 (権限0)**")
if os.path.exists("1.png"): st.image("1.png", use_container_width=True)

# タイムカード
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

# 管理メニュー
st.write("### 🛠️ メンテナンス管理メニュー")
url1 = "https://docs.google.com/spreadsheets/d/16JhXHMdYPoOIQmPBgd2sVclYkdYip6arRHtr86hr9hg/export?format=csv&gid=1365103622"
url2 = "https://docs.google.com/spreadsheets/d/1DShHig4iOhNXOkxMfALTRhyH0P5dtVpdBkNXvVQPC3g/export?format=csv&gid=1365103622"
url3 = "https://docs.google.com/spreadsheets/d/1kk9vFlE6LiBDMp6B4phUtnGs8CZfV8uhgkS-atdbBG0/export?format=csv&gid=1365103622"

r1, r2, r3 = load_sheet_data(custom_url=url1), load_sheet_data(custom_url=url2), load_sheet_data(custom_url=url3)
a1 = r1 and len(r1) >= 2 and any(c.strip() != "" for c in r1[1][:15])
a2 = r2 and len(r2) >= 2 and any(c.strip() != "" for c in r2[1][:15])
a3 = r3 and len(r3) >= 2 and any(c.strip() != "" for c in r3[1][:15])

if a1 or a2 or a3: st.error("⚠️ 未処理のデータがあります")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f'<a href="https://docs.google.com/spreadsheets/d/16JhXHMdYPoOIQmPBgd2sVclYrapYkdYip6arRHtr86hr9hg/edit?gid=1365103622" target="_blank">{get_img_html("3.png","⚙️",a1,"75px")}<p style="font-size:11px; text-align:center;">1.処理</p></a>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<a href="https://docs.google.com/spreadsheets/d/1DShHig4iOhNXOkxMfALTRhyH0P5dtVpdBkNXvVQPC3g/edit?gid=1365103622" target="_blank">{get_img_html("8.png","🔍",a2,"75px")}<p style="font-size:11px; text-align:center;">2.チェック</p></a>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<a href="https://docs.google.com/spreadsheets/d/1kk9vFlE6LiBDMp6B4phUtnGs8CZfV8uhgkS-atdbBG0/edit?gid=1365103622" target="_blank">{get_img_html("4.png","𖖨️",a3,"75px")}<p style="font-size:11px; text-align:center;">3.印刷用</p></a>', unsafe_allow_html=True)

render_daily_checklist()

st.write("---")
if st.button("🚪 ログアウト", use_container_width=True): process_logout()
