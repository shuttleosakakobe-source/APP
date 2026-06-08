import streamlit as st
import os
import base64
import urllib.request
import csv
import io
import json
import re  # 正規表現を追加
from datetime import datetime
from streamlit_javascript import st_javascript 

# --- 1. ページ設定 ---
st.set_page_config(
    page_title="ダスキンシャトル北大阪 業務アプリ",
    page_icon="icon.png", 
    layout="centered"
)

# --- 【直接連携】GASのウェブアプリURL ---
GAS_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwMUBZHk4bIrpNmopGkk2huKLdkhdzFynxqSuDxfRD_9mcIFet_osyQIg4V-CKovfQu/exec"

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

# --- 【超強化・日付解析関数】 ---
def parse_flexible_date(date_str):
    """スプレッドシートのあらゆる日付形式をdatetime.date型に安全に変換する"""
    if not date_str:
        return None
    # 余分な空白や時間を除去
    cleaned = str(date_str).strip().split(" ")[0]
    # ハイフン区切り、スラッシュ区切り両方に対応
    cleaned = cleaned.replace("-", "/")
    
    # yyyy/mm/dd の形式になっているかチェック
    match = re.match(r'^(\d{4})/(\d{1,2})/(\d{1,2})', cleaned)
    if match:
        try:
            year, month, day = map(int, match.groups())
            return datetime(year, month, day).date()
        except:
            return None
    return None

# --- 【超強化版】次回訪問日および本日の予定を取得する関数 ---
def get_visit_schedule_data(user_code):
    rows = load_sheet_data(gid="370581902")
    if not rows or len(rows) < 2:
        return {}, "データなし"
        
    header = rows[0]
    user_col_idx = -1
    
    # 担当者コードの一致チェック (文字列、数値、前後の空白、ゼロ埋めを考慮)
    target_code = str(user_code).strip().lower()
    
    for idx, col in enumerate(header):
        col_str = str(col).strip().lower()
        if col_str == target_code or col_str.split('.')[0] == target_code.split('.')[0]:
            user_col_idx = idx
            break
            
    if user_col_idx == -1:
        try:
            target_int = int(float(user_code))
            for idx, col in enumerate(header):
                try:
                    if int(float(col)) == target_int:
                        user_col_idx = idx
                        break
                except:
                    continue
        except:
            pass

    # 見つからない場合は「未登録」
    if user_col_idx == -1:
        return {}, "未登録"
        
    today = datetime.now().date()
    today_schedule = "なし"
    
    visit_dates = {"1W": None, "2W": None, "4W": None, "8W": None}
    type_map = {"A": "1W", "B": "2W", "C": "4W", "D": "8W"}
    
    for row in rows[1:]:
        if len(row) <= user_col_idx:
            continue
        
        date_str = row[0]
        cell_val = row[user_col_idx].strip()
        
        # 日付を安全にパース
        row_date = parse_flexible_date(date_str)
        if not row_date:
            continue
                
        # 1. 本日の予定チェック
        if row_date == today:
            if cell_val:
                today_schedule = cell_val
                
        # 2. 次回訪問日の計算（今日以降を対象）
        if row_date >= today:
            if cell_val:
                first_char = cell_val[0].upper()
                if first_char in type_map:
                    week_key = type_map[first_char]
                    if visit_dates[week_key] is None or row_date < visit_dates[week_key]["date"]:
                        visit_dates[week_key] = {
                            "date": row_date,
                            "display": f"{row_date.strftime('%m/%d')}({cell_val[1:]})" if len(cell_val) > 1 else f"{row_date.strftime('%m/%d')}"
                        }
                        
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

def get_login_storage():
    name = st_javascript("localStorage.getItem('shuttle_user_name');")
    url = st_javascript("localStorage.getItem('shuttle_user_url');")
    alert = st_javascript("localStorage.getItem('shuttle_needs_alert');")
    role = st_javascript("localStorage.getItem('shuttle_user_role');")
    code = st_javascript("localStorage.getItem('shuttle_user_code');")
    return name, url, alert, role, code

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

# --- 直接スプレッドシート（GAS）にデータをPOST送信する関数 ---
def submit_attendance_direct(status):
    user_code = st.session_state.get('user_code', '')
    user_name = st.session_state.get('user_name', '')
    
    payload = {
        "code": user_code,
        "name": user_name,
        "status": status
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        GAS_WEBAPP_URL, 
        data=data, 
        headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            res_body = json.loads(response.read().decode('utf-8'))
            if res_body.get("status") == "success":
                st.toast(f"🎉 {status} を記録しました！", icon="✅")
            else:
                st.error(f"記録失敗: {res_body.get('message')}")
    except Exception as e:
        st.error("スプレッドシートとの直接通信に失敗しました。")

# --- 6. メイン画面 ---
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
        @media (max-width: 600px) { .button-grid { grid-template-columns: repeat(2, 1fr); } }
        .btn-item { text-align: center; text-decoration: none; display: block; color: black !important; }
        .btn-text { font-size: 12px; font-weight: bold; line-height: 1.2; text-align: center; width: 100%; }
        footer {visibility: hidden;}
        hr { margin: 1.2rem 0 !important; }
        .alert-text { color: red; font-weight: bold; font-size: 14px; margin-bottom: 8px; display: block; text-align: center; }
        .admin-box { display: flex; flex-direction: column; align-items: center; justify-content: flex-start; text-align: center; }
        
        /* 次回訪問日・本日の予定のデザイン */
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

    # 👤 名前の部分をボタン化（隠しスイッチ）
    st.markdown('<div class="user-label-btn">', unsafe_allow_html=True)
    if st.button(f"👤 {st.session_state.user_name} さん", key="hidden_toggle"):
        st.session_state.show_timecard = not st.session_state.get('show_timecard', False)
    st.markdown('</div>', unsafe_allow_html=True)

    if os.path.exists("1.png"): st.image("1.png", use_container_width=True)

    # 🔔 お知らせ枠
    announcement = data[0].get('お知らせ', '安全運転でお願いします')
    st.markdown(f'''
        <div style="background-color:#fffbe6; border:2px solid #ffe58f; padding:10px; border-radius:10px; display:flex; align-items:center; margin-top: 5px;">
            <span style="font-size:16px; margin-right:8px;">🔔</span>
            <marquee scrollamount="5" style="color:red; font-weight:bold; font-size:16px;">{announcement}</marquee>
        </div>
    ''', unsafe_allow_html=True)

    # --- 📅 「次回訪問日」＆「本日の予定」表示 ---
    visit_info, today_sched = get_visit_schedule_data(st.session_state.get('user_code', ''))
    
    w1_disp = visit_info.get("1W", {}).get("display", "--/--") if visit_info.get("1W") else "--/--"
    w2_disp = visit_info.get("2W", {}).get("display", "--/--") if visit_info.get("2W") else "--/--"
    w4_disp = visit_info.get("4W", {}).get("display", "--/--") if visit_info.get("4W") else "--/--"
    w8_disp = visit_info.get("8W", {}).get("display", "--/--") if visit_info.get("8W") else "--/--"
    
    today_str = datetime.now().strftime('%m/%d')

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

    # --- 🕒 【隠し機能】スイッチONの時だけ表示される打刻エリア ---
    if st.session_state.get('show_timecard', False):
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

        if check_alert or alert_rows or st.session_state.user_role == "1":
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
                            <p class="btn-text" style="margin-top: 12px;">スポンジ<br>キャンペーンチェック</p>
                        </a>
                    </div>
                ''', unsafe_allow_html=True)
            
            if alert_rows:
                st.write("")
                st.markdown('<span class="alert-text">⚠️ メンテナンス未処理</span>', unsafe_allow_html=True)
                opts = [f"{r['name']} さん" for r in alert_rows]
                sel = st.selectbox("対象を選択", opts, label_visibility="collapsed")
                st.link_button(f"👉 確認を開く", alert_rows[opts.index(sel)]['url'], use_container_width=True)

    # 🔘 メインボタン 4つ
    b1 = get_img_html("3.png", "📄")
    b2 = get_img_html("4.png", "📋", alert=st.session_state.needs_alert)
    b4 = get_img_html("5.png", "🧽")
    b5 = get_img_html("image_d3349a.png", "🎓")

    grid_html = f'''
        <div class="button-grid">
            <a class="btn-item" href="https://docs.google.com/forms/d/e/1FAIpQLSc4E3L_UJkVxMMSTOYgcw3SJyoBixHoJfhe0WC-x1wbK6lsHw/viewform?usp=sharing" target="_blank">{b1}<p class="btn-text" style="margin-top:6px;">メンテナンス<br>入力</p></a>
            <a class="btn-item" href="{st.session_state.user_url}" target="_blank">{b2}<p class="btn-text" style="margin-top:6px;">メンテナンス<br>確認</p></a>
            <a class="btn-item" href="https://docs.google.com/forms/d/1t_3QDu1sOFXdBvwRzIuwdI1yT0Ez_AunIEXKz_Bds3c/edit#responses" target="_blank">{b4}<p class="btn-text" style="margin-top:6px;">スポンジ<br>キャンペーン入力</p></a>
            <a class="btn-item" href="https://drive.google.com/drive/folders/1vZE__7Th8RuVtkNQpG-rAZSBtAvG7cTX" target="_blank">{b5}<p class="btn-text" style="margin-top:6px;">勉強会<br>資料</p></a>
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
            st.session_state.show_timecard = False
            st.rerun()

# --- 7. 実行ロジック ---
if 'login_status' not in st.session_state: st.session_state.login_status = False
if 'logout_requested' not in st.session_state: st.session_state.logout_requested = False

if not st.session_state.login_status and not st.session_state.logout_requested:
    stored = get_login_storage()
    if stored and str(stored[0]) not in ["None", "null", "0", "undefined", ""]:
        st.session_state.user_name = str(stored[0])
        st.session_state.user_url = str(stored[1])
        st.session_state.needs_alert = (str(stored[2]) == 'True')
        st.session_state.user_role = str(stored[3])
        st.session_state.user_code = str(stored[4]) if len(stored) >= 5 else ""
        st.session_state.login_status = True
        st.rerun()

if st.session_state.login_status:
    main_screen()
else:
    inject_pwa_blocker() 
    if os.path.exists("1.png"): st.image("1.png", use_container_width=True)
    u_code = st.text_input("担当者コード").strip()
    u_pass = st.text_input("パスワード", type="password").strip()
    if st.button("ログイン", type="primary", use_container_width=True):
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
            st.session_state.user_code = u_code
            st.session_state.login_status = True
            st.session_state.logout_requested = False
            set_login_storage(st.session_state.user_name, st.session_state.user_url, st.session_state.needs_alert, st.session_state.user_role, st.session_state.user_code)
            st.rerun()
        else: st.error("認証失敗")
