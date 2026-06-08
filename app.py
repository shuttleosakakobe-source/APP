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

# --- 次回訪問日および本日の予定を取得する関数 ---
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
    today_schedule = "なし"
    
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
