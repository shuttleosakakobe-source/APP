import streamlit as st
import os
import base64
import urllib.request
import csv
import io

# --- ページ設定 ---
st.set_page_config(
    page_title="ダスキンシャトル北大阪 業務アプリ",
    page_icon="icon.png",
    layout="centered"
)

# --- 1. スプレッドシートからデータを取得する関数 ---
def load_sheet_data():
    sheet_url = "https://docs.google.com/spreadsheets/d/1cPgQ3Ej3P7JZPaxprFQnbnDkCatQ15lEHyF9C9tMgZ4/export?format=csv&gid=0"
    try:
        response = urllib.request.urlopen(sheet_url)
        content = response.read().decode('utf-8')
        f = io.StringIO(content)
        reader = csv.DictReader(f)
        return list(reader)
    except Exception as e:
        st.error("データの読み込みに失敗しました。")
        return None

# --- 2. セッション情報の初期化 ---
if 'login_status' not in st.session_state:
    st.session_state.login_status = False
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""
if 'user_url' not in st.session_state:
    st.session_state.user_url = ""
if 'needs_alert' not in st.session_state:
    st.session_state.needs_alert = False

# --- 3. 画像ボタン用関数（スマホ最適化版） ---
def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

def clickable_image(img_path, url, fallback_emoji, alert=False):
    img_base64 = get_base64_of_bin_file(img_path)
    border_style = "border: 6px solid red; box-shadow: 0 0 15px red;" if alert else "border: 6px solid transparent;"
    
    if img_base64:
        html = f'''
            <a href="{url}" target="_blank" style="text-decoration: none;">
                <img src="data:image/png;base64,{img_base64}" style="width: 100%; aspect-ratio: 1/1; object-fit: contain; cursor: pointer; border-radius: 25px; {border_style}">
            </a>
        '''
    else:
        html = f'''
            <a href="{url}" target="_blank" style="text-decoration: none;">
                <div style="width: 100%; aspect-ratio: 1/1; background-color: #f0f2f6; border-radius: 25px; display: flex; align-items: center; justify-content: center; font-size: 50px; {border_style}">
                    {fallback_emoji}
                </div>
            </a>
        '''
    st.markdown(html, unsafe_allow_html=True)

# --- 4. ログイン画面 ---
def login_screen():
    if os.path.exists("1.png"):
        st.image("1.png", use_container_width=True)
    st.markdown("<h2 style='text-align: center; font-size: 24px;'>ログイン</h2>", unsafe_allow_html=True)
    
    user_code = st.text_input("担当者コード").strip()
    password = st.text_input("パスワード", type="password").strip()
    
    if st.button("ログイン", use_container_width=True):
        data = load_sheet_data()
        if data:
            user_match = next((row for row in data if str(row.get('担当者コード')).strip() == user_code and str(row.get('パスワード')).strip() == password), None)
            if user_match:
                st.session_state.login_status = True
                st.session_state.user_name = user_match.get('担当者名')
                st.session_state.user_url = user_match.get('URL')
                f_val = list(user_match.values())[5] if len(user_match) >= 6 else "0"
                try:
                    st.session_state.needs_alert = float(f_val) != 0
                except:
                    st.session_state.needs_alert = str(f_val).strip() != "" and str(f_val).strip() != "0"
                st.rerun()
            else:
                st.error("担当者コードまたはパスワードが正しくありません")

# --- 5. メイン画面 ---
def main_screen():
    # スマホ向けCSS調整
    st.markdown("""
        <style>
        .stApp { background-color: white; }
        .user-label { text-align: right; font-size: 14px; color: #666; font-weight: bold; margin-bottom: 0px; }
        .info-container {
            background-color: #fffbe6;
            border: 2px solid #ffe58f;
            padding: 12px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            margin-top: 10px;
            margin-bottom: 20px;
        }
        .btn-text { text-align:center; font-size:14px; font-weight:bold; color:black; margin-top: 5px; margin-bottom: 20px; line-height: 1.2; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"<p class='user-label'>👤 {st.session_state.user_name} さん</p>", unsafe_allow_html=True)

    if os.path.exists("1.png"):
        st.image("1.png", use_container_width=True)

    # お知らせエリア
    data = load_sheet_data()
    announcement = "今日も一日安全運転で頑張りましょう！"
    if data:
        announcement = data[0].get('お知らせ', announcement)

    st.markdown(f'''
        <div class="info-container">
            <span style="font-size: 20px; margin-right: 10px;">🔔</span>
            <marquee scrollamount="5" style="color: red; font-weight: bold; font-size: 18px;">{announcement}</marquee>
        </div>
    ''', unsafe_allow_html=True)

    # --- ボタン配置 (2列 × 2段) ---
    col_left, col_right = st.columns(2)
    
    with col_left:
        form_url = "https://docs.google.com/forms/d/e/1FAIpQLSc4E3L_UJkVxMMSTOYgcw3SJyoBixHoJfhe0WC-x1wbK6lsHw/viewform?usp=sharing"
        clickable_image("3.png", form_url, "📄")
        st.markdown("<p class='btn-text'>メンテナンス<br>入力</p>", unsafe_allow_html=True)

        clickable_image("5.png", "https://www.google.com", "📢")
        st.markdown("<p class='btn-text'>キャンペーン<br>入力</p>", unsafe_allow_html=True)

    with col_right:
        clickable_image("4.png", st.session_state.user_url, "📋", alert=st.session_state.needs_alert)
        st.markdown("<p class='btn-text'>メンテナンス<br>確認</p>", unsafe_allow_html=True)

        study_url = "https://drive.google.com/drive/folders/1vZE__7Th8RuVtkNQpG-rAZSBtAvG7cTX"
        clickable_image("7.png", study_url, "🎓")
        st.markdown("<p class='btn-text'>勉強会<br>資料</p>", unsafe_allow_html=True)

    st.write("---")
    
    if os.path.exists("6.png"):
        st.image("6.png", width=150)
    
    if st.sidebar.button("ログアウト"):
        st.session_state.login_status = False
        st.rerun()

# --- 実行 ---
if st.session_state.login_status:
    main_screen()
else:
    login_screen()
