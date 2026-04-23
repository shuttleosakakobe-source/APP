import streamlit as st
import os
import base64
import urllib.request
import csv
import io

# --- ページ設定 ---
st.set_page_config(
    page_title="ダスキンシャトル北大阪 業務アプリ",
    page_icon="1.png",
    layout="centered"
)

# --- 1. スプレッドシートからデータを取得する関数 ---
def load_sheet_data(url):
    try:
        # スプレッドシートURLをCSVエクスポート用に変換
        if 'export?format=csv' not in url:
            if '/edit' in url:
                csv_url = url.split('/edit')[0] + '/export?format=csv'
                if 'gid=' in url:
                    csv_url += '&gid=' + url.split('gid=')[1].split('&')[0]
            else:
                csv_url = url.rstrip('/') + '/export?format=csv'
        else:
            csv_url = url
            
        response = urllib.request.urlopen(csv_url)
        content = response.read().decode('utf-8')
        f = io.StringIO(content)
        # 1行目を見出しとして読み込み
        reader = csv.reader(f)
        return list(reader)
    except Exception as e:
        return None

# --- 2. 未処理データがあるかチェックする関数 ---
def check_unprocessed_data(sheet_url):
    rows = load_sheet_data(sheet_url)
    if not rows or len(rows) < 2:
        return False
    
    # 2行目以降（データ行）をループ
    for row in rows[1:]:
        # 列数が足りているか確認
        if len(row) >= 12:
            b_val = row[1].strip()  # B列 (インデックス1)
            l_val = row[11].strip() # L列 (インデックス11)
            
            # 「B列に入力があり」かつ「L列が空」の場合
            if b_val != "" and l_val == "":
                return True # 1つでも見つかれば赤枠フラグを立てる
    return False

# --- 3. 画像ボタン用関数（赤枠対応） ---
def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

def clickable_image(img_path, url, fallback_emoji, alert=False):
    img_base64 = get_base64_of_bin_file(img_path)
    # 未処理あり(alert=True)なら太い赤枠、なしなら透明な枠（サイズを合わせるため）
    border_style = "border: 6px solid red;" if alert else "border: 6px solid transparent;"
    
    if img_base64:
        html = f'''
            <a href="{url}" target="_blank" style="text-decoration: none;">
                <img src="data:image/png;base64,{img_base64}" style="width: 100%; aspect-ratio: 1/1; object-fit: contain; cursor: pointer; border-radius: 20px; {border_style}">
            </a>
        '''
    else:
        html = f'''
            <a href="{url}" target="_blank" style="text-decoration: none;">
                <div style="width: 100%; aspect-ratio: 1/1; background-color: #f0f2f6; border-radius: 20px; display: flex; align-items: center; justify-content: center; font-size: 50px; {border_style}">
                    {fallback_emoji}
                </div>
            </a>
        '''
    st.markdown(html, unsafe_allow_html=True)

# --- セッション情報の初期化 ---
if 'login_status' not in st.session_state:
    st.session_state.login_status = False
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""
if 'user_url' not in st.session_state:
    st.session_state.user_url = ""

# --- 4. ログイン画面 ---
def login_screen():
    if os.path.exists("1.png"):
        st.image("1.png", use_container_width=True)
    st.markdown("<h2 style='text-align: center;'>ログイン</h2>", unsafe_allow_html=True)
    user_code = st.text_input("担当者コード")
    password = st.text_input("パスワード", type="password")
    
    if st.button("ログイン", use_container_width=True):
        login_sheet_url = "https://docs.google.com/spreadsheets/d/1cPgQ3Ej3P7JZPaxprFQnbnDkCatQ15lEHyF9C9tMgZ4/export?format=csv&gid=0"
        data = load_sheet_data(login_sheet_url)
        if data:
            # A列(0)がコード、C列(2)がパスワード
            for row in data[1:]:
                if len(row) >= 3 and row[0] == user_code and row[2] == password:
                    st.session_state.login_status = True
                    st.session_state.user_name = row[1] # B列:名前
                    st.session_state.user_url = row[3]  # D列:URL
                    st.rerun()
            st.error("担当者コードまたはパスワードが正しくありません")

# --- 5. メイン画面 ---
def main_screen():
    st.markdown("""
        <style>
        .stApp { background-color: white; }
        .user-label { text-align: right; font-size: 14px; color: #666; font-weight: bold; }
        .info-container {
            background-color: #fffbe6;
            border: 2px solid #ffe58f;
            padding: 10px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"<p class='user-label'>ログイン中：{st.session_state.user_name} さん</p>", unsafe_allow_html=True)

    if os.path.exists("1.png"):
        st.image("1.png", use_container_width=True)

    # お知らせ取得（ログインシートの1行目・E列[4]から）
    login_sheet_url = "https://docs.google.com/spreadsheets/d/1cPgQ3Ej3P7JZPaxprFQnbnDkCatQ15lEHyF9C9tMgZ4/export?format=csv&gid=0"
    sheet_rows = load_sheet_data(login_sheet_url)
    announcement = "今日も一日安全運転で頑張りましょう！"
    if sheet_rows and len(sheet_rows) > 1 and len(sheet_rows[1]) >= 5:
        announcement = sheet_rows[1][4]

    st.markdown(f'''
        <div class="info-container">
            <span style="font-size: 20px; margin-right: 10px;">🔔</span>
            <marquee scrollamount="5" style="color: red; font-weight: bold; font-size: 18px;">{announcement}</marquee>
        </div>
    ''', unsafe_allow_html=True)

    st.write("---")

    # 未処理チェック実行
    has_alert = check_unprocessed_data(st.session_state.user_url)

    col3, col4, col5, col7 = st.columns(4)
    
    with col3:
        form_url = "https://docs.google.com/forms/d/e/1FAIpQLSc4E3L_UJkVxMMSTOYgcw3SJyoBixHoJfhe0WC-x1wbK6lsHw/viewform?usp=sharing"
        clickable_image("3.png", form_url, "📄")
        st.markdown("<p style='text-align:center; font-size:12px; font-weight:bold;'>メンテナンス入力</p>", unsafe_allow_html=True)

    with col4:
        # alert=has_alert で赤枠を制御
        clickable_image("4.png", st.session_state.user_url, "📋", alert=has_alert)
        st.markdown("<p style='text-align:center; font-size:12px; font-weight:bold;'>メンテナンス確認</p>", unsafe_allow_html=True)

    with col5:
        clickable_image("5.png", "https://www.google.com", "📢")
        st.markdown("<p style='text-align:center; font-size:12px; font-weight:bold;'>キャンペーン入力</p>", unsafe_allow_html=True)

    with col7:
        study_url = "https://drive.google.com/drive/folders/1vZE__7Th8RuVtkNQpG-rAZSBtAvG7cTX"
        clickable_image("7.png", study_url, "🎓")
        st.markdown("<p style='text-align:center; font-size:12px; font-weight:bold;'>勉強会資料</p>", unsafe_allow_html=True)

    if os.path.exists("6.png"):
        st.image("6.png", width=180)

    if st.sidebar.button("ログアウト"):
        st.session_state.login_status = False
        st.rerun()

# --- 実行 ---
if st.session_state.login_status:
    main_screen()
else:
    login_screen()
