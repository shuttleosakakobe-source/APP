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
        # CSV形式で取得するための変換
        csv_url = url.replace('/edit?usp=sharing', '/export?format=csv').replace('/edit#gid=', '/export?format=csv&gid=')
        if '/export?format=csv' not in csv_url:
            csv_url = url.rstrip('/') + '/export?format=csv'
            
        response = urllib.request.urlopen(csv_url)
        content = response.read().decode('utf-8')
        f = io.StringIO(content)
        reader = csv.DictReader(f)
        return list(reader)
    except Exception as e:
        return None

# --- 2. 未処理データがあるかチェックする関数 ---
def check_unprocessed_data(sheet_url):
    # 個別URLから「未処理確認」シートを特定して読み込む
    # ※URLに特定のgid（シートID）が含まれていない場合は、URLを調整する必要があります
    # ここでは、D列に貼られたURLの「未処理確認」シートをチェックします
    data = load_sheet_data(sheet_url)
    if data:
        for row in data:
            # B列にデータがあり、かつL列が空（またはNone）の場合をチェック
            # row.get('列名') の部分は、実際のシートの1行目の見出し名に合わせてください
            # ここでは「B列」「L列」という見出し名、もしくは左から2番目、12番目として判定します
            vals = list(row.values())
            if len(vals) >= 12:
                b_val = vals[1]  # B列
                l_val = vals[11] # L列
                if b_val and (not l_val or str(l_val).strip() == ""):
                    return True # 未処理あり
    return False

# --- 3. 画像ボタン用関数（赤枠対応版） ---
def clickable_image(img_path, url, fallback_emoji, alert=False):
    img_base64 = get_base64_of_bin_file(img_path)
    # alertがTrueなら赤枠、Falseならなし
    border_style = "border: 5px solid red;" if alert else "border: none;"
    
    if img_base64:
        html = f'''
            <a href="{url}" target="_blank" style="text-decoration: none;">
                <img src="data:image/png;base64,{img_base64}" style="width: 100%; aspect-ratio: 1/1; object-fit: contain; cursor: pointer; border-radius: 15px; {border_style}">
            </a>
        '''
    else:
        html = f'''
            <a href="{url}" target="_blank" style="text-decoration: none;">
                <div style="width: 100%; aspect-ratio: 1/1; background-color: #f0f2f6; border-radius: 15px; display: flex; align-items: center; justify-content: center; font-size: 50px; {border_style}">
                    {fallback_emoji}
                </div>
            </a>
        '''
    st.markdown(html, unsafe_allow_html=True)

def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

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
        # ログイン管理シートURL
        login_sheet_url = "https://docs.google.com/spreadsheets/d/1cPgQ3Ej3P7JZPaxprFQnbnDkCatQ15lEHyF9C9tMgZ4/export?format=csv&gid=0"
        data = load_sheet_data(login_sheet_url)
        if data:
            user_match = next((row for row in data if str(row['担当者コード']) == user_code and str(row['パスワード']) == password), None)
            if user_match:
                st.session_state.login_status = True
                st.session_state.user_name = user_match['担当者名']
                st.session_state.user_url = user_match['URL']
                st.rerun()
            else:
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

    # お知らせ取得
    login_sheet_url = "https://docs.google.com/spreadsheets/d/1cPgQ3Ej3P7JZPaxprFQnbnDkCatQ15lEHyF9C9tMgZ4/export?format=csv&gid=0"
    sheet_data = load_sheet_data(login_sheet_url)
    announcement = sheet_data[0].get('お知らせ', '安全運転でお願いします') if sheet_data else "お知らせはありません"

    st.markdown(f'''
        <div class="info-container">
            <span style="font-size: 20px; margin-right: 10px;">🔔</span>
            <marquee scrollamount="5" style="color: red; font-weight: bold; font-size: 18px;">{announcement}</marquee>
        </div>
    ''', unsafe_allow_html=True)

    st.write("---")

    # 未処理チェック（④のボタン用）
    has_alert = check_unprocessed_data(st.session_state.user_url)

    col3, col4, col5, col7 = st.columns(4)
    
    with col3:
        clickable_image("3.png", "https://docs.google.com/forms/...", "📄")
        st.markdown("<p style='text-align:center; font-size:12px; font-weight:bold;'>メンテナンス入力</p>", unsafe_allow_html=True)

    with col4:
        # alert=has_alert で、未処理があれば赤枠がつく
        clickable_image("4.png", st.session_state.user_url, "📋", alert=has_alert)
        st.markdown("<p style='text-align:center; font-size:12px; font-weight:bold;'>メンテナンス確認</p>", unsafe_allow_html=True)

    with col5:
        clickable_image("5.png", "https://www.google.com", "📢")
        st.markdown("<p style='text-align:center; font-size:12px; font-weight:bold;'>キャンペーン入力</p>", unsafe_allow_html=True)

    with col7:
        clickable_image("7.png", "https://drive.google.com/drive/folders/...", "🎓")
        st.markdown("<p style='text-align:center; font-size:12px; font-weight:bold;'>勉強会資料</p>", unsafe_allow_html=True)

    if os.path.exists("6.png"):
        st.image("6.png", width=180)

# --- 実行 ---
if st.session_state.login_status:
    main_screen()
else:
    login_screen()
