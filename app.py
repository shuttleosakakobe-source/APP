import streamlit as st
import os
import base64
import urllib.request
import csv
import io
import json
import re
from datetime import datetime, timedelta
from streamlit_javascript import st_javascript 

# --- 1. ページ設定 ---
st.set_page_config(
    page_title="ダスキンシャトル 業務アプリ",
    page_icon="icon.png", 
    layout="centered"
)

# --- GASウェブアプリURL ---
GAS_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwDvTJlbULcKSYKx-Hyp6tU-Gh4ua7j-tglY9VWx2UqyyLxTPv8EgAb5vdQpq3Auxu9/exec"

# --- 2. スプレッドシート取得関数 ---
@st.cache_data(ttl=0)
def load_sheet_data(gid="0", custom_url=None):
    if custom_url:
        target_url = custom_url
    else:
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

# --- 日付解析関数 ---
def parse_flexible_date(date_str):
    if not date_str:
        return None
    cleaned = str(date_str).strip().split(" ")[0]
    match_jp = re.match(r'^(\d{4})年(\d{1,2})月(\d{1,2})日', cleaned)
    if match_jp:
        try:
            year, month, day = map(int, match_jp.groups())
            return datetime(year, month, day).date()
        except:
            return None
    cleaned = cleaned.replace("-", "/")
    match_slash = re.match(r'^(\d{4})/(\d{1,2})/(\d{1,2})', cleaned)
    if match_slash:
        try:
            year, month, day = map(int, match_slash.groups())
            return datetime(year, month, day).date()
        except:
            return None
    return None

# --- 次回訪問日および本日の予定を取得する関数 ---
def get_visit_schedule_data(user_code):
    rows = load_sheet_data(gid="370581902")
    if not rows or len(rows) < 3:
        return {}, "データなし"
        
    code_row = rows[0]
    user_col_idx = -1
    target_code = str(user_code).strip().lower()
    
    for idx, col in enumerate(code_row):
        col_str = str(col).strip().lower()
        if col_str == target_code or col_str.split('.')[0] == target_code.split('.')[0]:
            user_col_idx = idx
            break
            
    if user_col_idx == -1:
        try:
            target_int = int(float(user_code))
            for idx, col in enumerate(code_row):
                try:
                    if int(float(col)) == target_int:
                        user_col_idx = idx
                        break
                except:
                    continue
        except:
            pass

    if user_col_idx == -1:
        return {}, "未登録"
        
    today = datetime.now().date()
    today_schedule = "なし"
    all_schedules = []
    
    for row in rows[2:]:
        if len(row) <= user_col_idx:
            continue
        date_str = row[0]
        cell_val = row[user_col_idx].strip()
        row_date = parse_flexible_date(date_str)
        if not row_date:
            continue
        if row_date == today and cell_val:
            today_schedule = cell_val
        if cell_val:
            all_schedules.append({
                "date": row_date,
                "val": cell_val,
                "type": cell_val[0].upper()
            })
            
    all_schedules.sort(key=lambda x: x["date"])
    current_base_type = "A" 
    for sched in all_schedules:
        if sched["date"] >= today:
            current_base_type = sched["type"]
            break

    cycle_order = ["A", "B", "C", "D"]
    try:
        base_idx = cycle_order.index(current_base_type)
    except:
        base_idx = 0
        
    w1_target = cycle_order[(base_idx + 1) % 4]
    w2_target = cycle_order[(base_idx + 2) % 4]
    w4_target = current_base_type
    w8_target = current_base_type

    visit_dates = {"1W": None, "2W": None, "4W": None, "8W": None}
    
    def get_disp_str(sched_obj):
        d = sched_obj["date"]
        v = sched_obj["val"]
        return f"{d.strftime('%m/%d')}({v[1:]})" if len(v) > 1 else f"{d.strftime('%m/%d')}"

    w1_obj = None
    for sched in all_schedules:
        if sched["date"] >= today and sched["type"] == w1_target:
            w1_obj = sched
            visit_dates["1W"] = {"display": get_disp_str(sched)}
            break
            
    w2_obj = None
    for sched in all_schedules:
        if sched["date"] >= today and sched["type"] == w2_target:
            w2_obj = sched
            visit_dates["2W"] = {"display": get_disp_str(sched)}
            break

    w4_obj = None
    if w2_obj:
        for sched in all_schedules:
            if sched["date"] > w2_obj["date"] and sched["type"] == w4_target:
                w4_obj = sched
                visit_dates["4W"] = {"display": get_disp_str(sched)}
                break
    else:
        for sched in all_schedules:
            if sched["date"] >= today and sched["type"] == w4_target:
                w4_obj = sched
                visit_dates["4W"] = {"display": get_disp_str(sched)}
                break

    if w4_obj:
        target_after_2w = w4_obj["date"] + timedelta(days=14)
        for sched in all_schedules:
            if sched["date"] >= target_after_2w and sched["type"] == w8_target:
                visit_dates["8W"] = {"display": get_disp_str(sched)}
                break

    for k in visit_dates:
        if visit_dates[k] is None:
            visit_dates[k] = {"display": "--/--"}

    return visit_dates, today_schedule

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
def set_login_storage(name, url, alert, role, code):
    st_javascript(f"localStorage.setItem('shuttle_user_name', '{name}');")
    st_javascript(f"localStorage.setItem('shuttle_user_url', '{url}');")
    st_javascript(f"localStorage.setItem('shuttle_needs_alert', '{alert}');")
    st_javascript(f"localStorage.setItem('shuttle_user_role', '{role}');")
    st_javascript(f"localStorage.setItem('shuttle_user_code', '{code}');")

# --- 5. 強制アイコン＆ダウンロードブロック関数 ---
def inject_pwa_blocker():
    if os.path.exists("icon.png"):
        with open("icon.png", "rb") as f:
            icon_data = base64.b64encode(f.read()).decode()
        
        block_html = f'''
            <script>
                const links = parent.document.getElementsByTagName("link");
                for (let link of links) {{
                    if (link.rel === "manifest" || link.href.includes("manifest")) {{
                        link.href = "data:application/json;base64,e30=";
                    }}
                }}
                let appleLink = parent.document.querySelector("link[rel='apple-touch-icon']");
                if (!appleLink) {{
                    appleLink = parent.document.createElement("link");
                    appleLink.rel = "apple-touch-icon";
                    parent.document.head.appendChild(appleLink);
                }}
                appleLink.href = "data:image/png;base64,{icon_data}";

                let iconLink = parent.document.querySelector("link[sizes='192x192']");
                if (!iconLink) {{
                    iconLink = parent.document.createElement("link");
                    iconLink.rel = "icon";
                    iconLink.sizes = "192x192";
                    parent.document.head.appendChild(iconLink);
                }}
                iconLink.href = "data:image/png;base64,{icon_data}";
            </script>
        '''
        st.components.v1.html(block_html, height=0, width=0)

# --- スプレッドシート（GAS）に通信する汎用関数 ---
def post_to_gas(payload):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        GAS_WEBAPP_URL, 
        data=data, 
        headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ⏰ 勤怠送信用の関数
def submit_attendance_direct(status):
    res = post_to_gas({
        "code": st.session_state.get('user_code', ''),
        "name": st.session_state.get('user_name', ''),
        "status": status
    })
    if res.get("status") == "success":
        st.toast(f"🎉 {status} を記録しました！", icon="✅")
    else:
        st.error("通信に失敗しました。")

# --- 🔄 新シートの列配置から本日の完了状況を同期する関数 ---
def sync_checklist_from_cloud():
    res = post_to_gas({
        "status": "GET_CHECKLIST",
        "date": datetime.now().strftime("%Y/%m/%d"),
        "name": st.session_state.get('user_name', '')
    })
    if res.get("status") == "success" and "completed" in res:
        return set(res["completed"])
    return set()

# --- ✍️ ボタンを押したタスクの列に完了時間を記録する関数 ---
def save_task_to_cloud(task_name):
    post_to_gas({
        "status": "COMPLETE_TASK",
        "code": st.session_state.get('user_code', ''),
        "name": st.session_state.get('user_name', ''),
        "task": task_name
    })

# --- 💬 ポップアップ（モーダルダイアログ） ---
@st.dialog("業務完了の確認")
def show_confirm_dialog(task_name):
    st.write(f"**「{task_name}」** を完了にしますか？")
    st.caption("※スプレッドシートの該当列に完了時刻が保存され、チェックリストから非表示になります。")
    st.write("")
    
    conf_col1, conf_col2 = st.columns(2)
    with conf_col1:
        if st.button("👍 はい（ログ記録）", key="dlg_yes", type="primary", use_container_width=True):
            save_task_to_cloud(task_name) 
            st.toast(f"✅ シートの専用列への時刻書き込みが完了しました！")
            st.rerun()
    with conf_col2:
        if st.button("❌ いいえ", key="dlg_no", use_container_width=True):
            st.rerun()

# --- 【見出し・行管理完全連動】デイリータスクボタン ---
def render_daily_checklist():
    st.write("")
    st.write("### 📅 業務チェックリスト（マトリックスシート連動型）")
    
    # 1行目の見出しと1文字一句ズレがないよう定義
    am_items = [
        "【データ抽出】 データ抽出 (38) ※※※代行手数料27%、32%と異なる実績抽出→検索",
        "【実績管理】 日次確認 [700→790→78] (①→F1→F9 / ②→F1→F8)",
        "【実績管理】 日次締 [700→792] (①→入金合計のみ / ②→実績日と休日分)",
        "【実績管理】 実績送信 [700→734] (①→②表示しない → 全選択①→F1)",
        "【発注】 クローバー返却 [F1] (出力なし)",
        "【レンタル準備】 出庫表・ピッキングリスト [300→333] (①→翌日 / ②→最終)",
        "【帳票出力】 1400→ (日次 / 出庫表 / ピッキング表[店舗合計・F1])",
        "【発注状況照会】 TAN1D引当数 [400→411] (③売切→出庫予定[最終]→F1→F7)",
        "【入出庫・在庫】 担当者別出庫 [500→511] (1.全て選択→F1 ※紙なし)",
        "【棚卸調査票】 [500→582] (1：日時→2：RFDIアプリ →F1印刷)",
        "【メンテ終了後】 追加発注 [400→422] (①→F1)",
        "【メンテ終了後】 実績表出力 [指定店のみ] (決定→検索→画面印刷) ※プレイヤーズ",
        "【メンテ終了後】 納品書 [300→331] (日付[前日発送分]→F1)",
        "【メンテ終了後】 帳票出力 [1400→] (1.日次→Ent→Ent→1印刷 / 1.納品書)"
    ]
    
    pm_items = [
        "【メンテチェック終了後】 定期発注 [400→421] 日付 Ｆ１→定期発注実行確認→Ｆ１",
        "【メンテチェック終了後】 追加発注 [400→422] ①→Ｆ１ 【あればその都度】"
    ]
    
    # 自分の本日のタスク状況を取得
    completed_tasks = sync_checklist_from_cloud()

    tab_am, tab_pm = st.tabs(["🌅 AM（日次更新前必・メンテ終了後）", "🌇 PM（メンテチェック終了後）"])

    with tab_am:
        remaining_am = [item for item in am_items if item not in completed_tasks]
        if not remaining_am:
            st.success("🎉 本日のAM業務・更新タスクはすべて完了しています！")
        else:
            for item in remaining_am:
                if st.button(f"⬜ {item}", key=f"btn_am_{item}", use_container_width=True):
                    show_confirm_dialog(item)

    with tab_pm:
        remaining_pm = [item for item in pm_items if item not in completed_tasks]
        if not remaining_pm:
            st.success("🎉 本日のPM業務（定期・追加発注）はすべて完了しています！")
        else:
            for item in remaining_pm:
                if st.button(f"⬜ {item}", key=f"btn_pm_{item}", use_container_width=True):
                    show_confirm_dialog(item)

# --- 6. ユーザー選択（ログイン）画面 ---
def login_screen():
    inject_pwa_blocker()
    st.title("🔑 ユーザー選択")
    st.write("利用する担当者名を選択してください。")
    
    # スプレッドシートのメイン（gid=0）からユーザー一覧を取得
    data_raw = load_sheet_data(gid="0")
    if not data_raw or len(data_raw) < 2:
        st.error("ユーザーデータの読み込みに失敗しました。")
        return
        
    header = data_raw[0]
    user_list = []
    for row in data_raw[1:]:
        if len(row) > 1 and row[1].strip():
            user_list.append(row[1].strip())
            
    selected_name = st.selectbox("担当者名", user_list)
    
    if st.button("ログイン", type="primary", use_container_width=True):
        # 選択されたユーザーの詳細情報を取得してセッションに保存
        for row in data_raw[1:]:
            if len(row) > 1 and row[1].strip() == selected_name:
                user_dict = dict(zip(header, row))
                st.session_state.user_name = selected_name
                st.session_state.user_code = str(user_dict.get('コード', '')).split('.')[0]
                st.session_state.user_role = str(user_dict.get('権限', '3')).split('.')[0]
                st.session_state.show_timecard = False
                
                # ブラウザ保存
                set_login_storage(
                    st.session_state.user_name,
                    user_dict.get('個別URL', ''),
                    str(user_dict.get('要確認フラグ', '0')),
                    st.session_state.user_role,
                    st.session_state.user_code
                )
                st.rerun()

# --- 7. メイン画面 ---
def main_screen():
    inject_pwa_blocker() 

    st.markdown("""
        <style>
        header {visibility: hidden; height: 0px !important;}
        .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; max-width: 500px; }
        [data-testid="stVerticalBlock"] { gap: 1.2rem !important; }
        .user-label-btn { text-align: right; margin-bottom: 5px; }
        .user-label-btn button {
            background: none !important;
            border: none !important;
            color: #666 !important;
            font-size: 13px !important;
            font-weight: bold !important;
            padding: 0 !important;
            margin-left: auto !important;
            display: block !important;
            box-shadow: none !important;
        }
        .button-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 15px 0; }
        .button-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 15px 0; }
        @media (max-width: 600px) { 
            .button-grid { grid-template-columns: repeat(2, 1fr); }
            .button-grid-3 { grid-template-columns: repeat(1, 1fr); }
        }
        .btn-item { text-align: center; text-decoration: none; display: block; color: black !important; }
        .btn-text { font-size: 12px; font-weight: bold; line-height: 1.2; text-align: center; width: 100%; }
        footer {visibility: hidden;}
        hr { margin: 1.2rem 0 !important; }
        .alert-text { color: red; font-weight: bold; font-size: 14px; margin-bottom: 8px; display: block; text-align: center; }
        .admin-box { display: flex; flex-direction: column; align-items: center; justify-content: flex-start; text-align: center; }
        
        .visit-container {
            background-color: #f4f6f9;
            border: 1px solid #dcdfe6;
            padding: 10px;
            border-radius: 10px;
            margin-top: 8px;
        }
        .visit-title {
            font-size: 13px;
            font-weight: bold;
            color: #409eff;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
        }
        .visit-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 6px;
            text-align: center;
            margin-bottom: 10px;
        }
        .visit-box {
            background: white;
            padding: 4px;
            border-radius: 6px;
            border: 1px solid #e4e7ed;
        }
        .visit-label { font-size: 11px; color: #909399; font-weight: bold; }
        .visit-date { font-size: 13px; color: #303133; font-weight: bold; margin-top: 2px; }
        
        .today-schedule-box {
            background-color: #eef7fe;
            border: 1px solid #c6e2ff;
            border-radius: 6px;
            padding: 6px 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .today-title { font-size: 12px; font-weight: bold; color: #0056b3; }
        .today-val { font-size: 14px; font-weight: bold; color: #cd1212; }
        
        div.stButton > button {
            font-weight: bold !important;
            border-radius: 10px !important;
            height: 45px !important;
        }
        </style>
    """, unsafe_allow_html=True)

    data_raw = load_sheet_data(gid="0")
    header = data_raw[0]
    data = [dict(zip(header, row)) for row in data_raw[1:]]
    
    current_user_data = next((r for r in data if r.get('担当者名') == st.session_state.user_name), None)
    if current_user_data:
        vals = list(current_user_data.values())
        st.session_state.needs_alert = (str(vals[5]).strip() not in ["0", "", "None"])

    st.markdown('<div class="user-label-btn">', unsafe_allow_html=True)
    if st.button(f"👤 {st.session_state.user_name} さん", key="hidden_toggle"):
        if st.session_state.user_role != "0":
            st.session_state.show_timecard = not st.session_state.get('show_timecard', False)
    st.markdown('</div>', unsafe_allow_html=True)

    if os.path.exists("1.png"): st.image("1.png", use_container_width=True)

    announcement = data[0].get('お知らせ', '安全運転でお願いします')
    st.markdown(f'''
        <div style="background-color:#fffbe6; border:2px solid #ffe58f; padding:10px; border-radius:10px; display:flex; align-items:center; margin-top: 5px;">
            <span style="font-size:16px; margin-right:8px;">🔔</span>
            <marquee scrollamount="5" style="color:red; font-weight:bold; font-size:16px;">{announcement}</marquee>
        </div>
    ''', unsafe_allow_html=True)

    if st.session_state.user_role == "0":
        st.session_state.show_timecard = True

    if st.session_state.user_role != "3" and st.session_state.get('show_timecard', False):
        st.write("")
        st.write("### 🕒 勤怠・所在打刻")
        att_col1, att_col2, att_col3 = st.columns(3)
        with att_col1:
            if st.button("🌅 出社", use_container_width=True):
                submit_attendance_direct("出社")
        with att_col2:
            if st.button("🚗 帰社", use_container_width=True):
                submit_attendance_direct("帰社")
        with att_col3:
            if st.button("🌃 退社", use_container_width=True):
                submit_attendance_direct("退社")
        st.write("---")

    if st.session_state.user_role != "3":
        visit_info, today_sched = get_visit_schedule_data(st.session_state.get('user_code', ''))
        w1_disp = visit_info.get("1W", {}).get("display", "--/--")
        w2_disp = visit_info.get("2W", {}).get("display", "--/--")
        w4_disp = visit_info.get("4W", {}).get("display", "--/--")
        w8_disp = visit_info.get("8W", {}).get("display", "--/--")
        
        today_str = datetime.now().strftime('%m/%d')
        hide_keywords = ["勉強会", "空き日", "休", "チーフ出勤"]
        should_hide = any(kw in today_sched for kw in hide_keywords)

        if should_hide:
            st.markdown(f'''
                <div class="visit-container">
                    <div class="today-schedule-box">
                        <span class="today-title">📌 本日の予定 ({today_str})</span>
                        <span class="today-val">{today_sched}</span>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown(f'''
                <div class="visit-container">
                    <div class="visit-title">📅 次回訪問日</div>
                    <div class="visit-grid">
                        <div class="visit-box"><div class="visit-label">1W</div><div class="visit-date">{w1_disp}</div></div>
                        <div class="visit-box"><div class="visit-label">2W</div><div class="visit-date">{w2_disp}</div></div>
                        <div class="visit-box"><div class="visit-label">4W</div><div class="visit-date">{w4_disp}</div></div>
                        <div class="visit-box"><div class="visit-label">8W</div><div class="visit-date">{w8_disp}</div></div>
                    </div>
                    <div class="today-schedule-box">
                        <span class="today-title">📌 本日の予定 ({today_str})</span>
                        <span class="today-val">{today_sched}</span>
                    </div>
                </div>
            ''', unsafe_allow_html=True)

    if st.session_state.user_role in ["0", "1"]:
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

        st.write("") 
        col_admin1, col_admin2 = st.columns([1, 1])
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
            sponge_btn = get_img_html("5.png", "📊", alert=False, width="90px")
            sponge_url = "https://docs.google.com/spreadsheets/d/1CUviW0AH8UdG4ZdF2CkuHh9NJKVM2NAYfXi8omQb3xE/edit?gid=0#gid=0"
            st.markdown(f'''
                <div class="admin-box">
                    <a href="{sponge_url}" target="_blank" style="text-decoration:none; color:black;">
                        {sponge_btn}
                        <p class="btn-text" style="margin-top: 12px;">スポンジ管理<br>表</p>
                    </a>
                </div>
            ''', unsafe_allow_html=True)

    # 業務チェックリストを表示
    render_daily_checklist()

# --- アプリの起動 ---
if __name__ == "__main__":
    # 1. ローカルストレージ（自動ログイン）のチェックを試みる
    local_name = st_javascript("localStorage.getItem('shuttle_user_name');")
    local_role = st_javascript("localStorage.getItem('shuttle_user_role');")
    local_code = st_javascript("localStorage.getItem('shuttle_user_code');")
    
    if 'user_name' not in st.session_state:
        if local_name and local_role:
            # 端末の過去のログイン情報を引き継ぐ
            st.session_state.user_name = str(local_name)
            st.session_state.user_role = str(local_role)
            st.session_state.user_code = str(local_code) if local_code else ""
            st.session_state.show_timecard = False
            main_screen()
        else:
            # ログイン情報がない場合はユーザー選択（ログイン画面）を表示
            login_screen()
    else:
        # すでにログインセッションがある場合はメイン画面を表示
        main_screen()
