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
    except:
        return None

# --- 2. 画像のBase64変換 ---
def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

# --- 3. メイン画面の表示 ---
def main_screen():
    # PCは4列、スマホは2列にするための独自CSS
    st.markdown("""
        <style>
        .stApp { background-color: white; }
        .user-label { text-align: right; font-size: 14px; color: #666; font-weight: bold; }
        
        /* ボタンを囲むコンテナ */
        .button-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr); /* デフォルト（PC）は4列 */
            gap: 15px;
            margin-top: 20px;
        }

        /* スマホ画面（幅600px以下）の時の設定 */
        @media (max-width: 600px) {
            .button-grid {
                grid-template-columns: repeat(2, 1fr); /* スマホは2列 */
            }
        }

        .btn-item { text-align: center; text-decoration: none; }
        .btn-image { width: 100%; aspect-ratio: 1/1; object-fit: contain; border-radius: 15px; }
        .btn-text { color: black; font-size: 12px; font-weight: bold; margin-top: 5px; line-height: 1.2; }
        
        /* 赤枠アラート */
        .alert-style { border: 5px solid red; box-shadow: 0 0 10px red; }
        .no-border { border: 5px solid transparent; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"<p class='user-label'>👤 {st.session_state.user_name} さん</p>", unsafe_allow_html=True)

    if os.path.exists("1.png"):
        st.image("1.png", use_container_width=True)

    # お知らせ（ログインシートから取得）
    data = load_sheet_data()
    announcement = data[0].get('お知らせ', '安全運転でお願いします') if data else "安全運転でお願いします"

    st.markdown(f'''
        <div style="background-color: #fffbe6; border: 2px solid #ffe58f; padding: 10px; border-radius: 10px; display: flex; align-items: center; margin-bottom: 10px;">
            <span style="font-size: 20px; margin-right: 10px;">🔔</span>
            <marquee scrollamount="5" style="color: red; font-weight: bold; font-size: 18px;">{announcement}</marquee>
        </div>
    ''', unsafe_allow_html=True)

    # 各画像のBase64化
    img3 = get_base64_of_bin_file("3.png")
    img4 = get_base64_of_bin_file("4.png")
    img5 = get_base64_of_bin_file("5.png")
    img7 = get_base64_of_bin_file("image_d3349a.png") # 勉強会ロゴ

    # アラートの枠線クラス判定
    alert_class = "alert-style" if st.session_state.needs_alert else "no-border"

    # カスタムHTMLグリッドで表示（これがPC/スマホ切り替えの肝）
    st.markdown(f'''
        <div class="button-grid">
            <a class="btn-item" href="https://docs.google.com/forms/d/e/1FAIpQLSc4E3L_UJkVxMMSTOYgcw3SJyoBixHoJfhe0WC-x1wbK6lsHw/viewform?usp=sharing" target="_blank">
                <img src="data:image/png;base64,{img3}" class="btn-image no-border">
                <p class="btn-text">メンテナンス<br>入力</p>
            </a>
            <a class="btn-item" href="{st.session_state.user_url}" target="_blank">
                <img src="data:image/png;base64,{img4}" class="btn-image {alert_class}">
                <p class="btn-text">メンテナンス<br>確認</p>
            </a>
            <a class="btn-item" href="https://www.google.com" target="_blank">
                <img src="data:image/png;base64,{img5}" class="btn-image no-border">
                <p class="btn-text">キャンペーン<br>入力</p>
            </a>
            <a class="btn-item" href="https://drive.google.com/drive/folders/1vZE__7Th8RuVtkNQpG-rAZSBtAvG7cTX" target="_blank">
                <img src="data:image/png;base64,{img7}" class="btn-image no-border">
                <p class="btn-text">勉強会<br>資料</p>
            </a>
        </div>
    ''', unsafe_allow_html=True)

    st.write("---")
    if os.path.exists("6.png"):
        st.image("6.png", width=150)
    
    if st.sidebar.button("ログアウト"):
        st.session_state.login_status = False
        st.rerun()

# --- ログイン画面 ---
def login_screen():
    if os.path.exists("1.png"):
        st.image("1.png", use_container_width=True)
    st.markdown("<h2 style='text-align: center;'>ログイン</h2>", unsafe_allow_html=True)
    
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
                
                # F列(index 5)のチェック
                f_val = list(user_match.values())[5] if len(user_match) >= 6 else "0"
                try:
                    st.session_state.needs_alert = float(f_val) != 0
                except:
                    st.session_state.needs_alert = str(f_val).strip() != "" and str(f_val).strip() != "0"
                st.rerun()
            else:
                st.error("コードまたはパスワードが正しくありません")

# --- 実行 ---
if 'login_status' not in st.session_state: st.session_state.login_status = False
if st.session_state.login_status:
    main_screen()
else:
    login_screen()
