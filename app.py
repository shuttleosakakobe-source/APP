import streamlit as st
import os
import base64
import urllib.request
import csv
import io
import json
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

# --- 【機能拡張】次回訪問日および本日の予定を取得する関数 ---
def get_visit_schedule_data(user_code):
    rows = load_sheet_data(gid="370581902")
    if not rows or len(rows) < 2:
        return {}, "データなし"
        
    header = rows[0]
    user_col_idx = -1
    for idx, col in enumerate(header):
        if str(col).strip() == str(user_code).strip():
            user_col_idx = idx
            break
            
    if user_col_idx == -1:
        return {}, "未登録"
        
    today = datetime.now().date()
    
    # 本日の予定用変数
    today_schedule = "なし"
    
    # 次回訪問日用
    visit_dates = {"1W": None, "2W": None, "4W": None, "8W": None}
    type_map = {"A": "1W", "B": "2W", "C": "4W", "D": "8W"}
    
    for row in rows[1:]:
        if len(row) <= user_col_idx:
            continue
        
        date_str = row[0].strip()
        cell_val = row[user_col_idx].strip()
        
        if not date_str:
            continue
            
        try:
            date_cleaned = date_str.split(" ")[0]
            row_date = datetime.strptime(date_cleaned, "%Y/%m/%d").date()
        except:
            try:
                row_date = datetime.strptime(date_cleaned, "%Y-%m-%d").date()
            except:
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
        .btn-
