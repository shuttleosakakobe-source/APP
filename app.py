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

# --- スプレッドシートからデータを取得する関数 ---
def load_sheet_data(url):
    try:
        # CSVエクスポート形式に変換
        csv_url = url.split('/edit')[0] + '/export?format=csv'
        if 'gid=' in url:
            csv_url += '&gid=' + url.split('gid=')[1].split('&')[0]
            
        response = urllib.request.urlopen(csv_url)
        content = response.read().decode('utf-8')
        f = io.StringIO(content)
        reader = csv.reader(f)
        return list(reader)
    except Exception as e:
        st.error(f"スプレッドシートにアクセスできません。共有設定を確認してください。")
        return None

# --- 未処理データをチェックする関数 ---
def check_unprocessed_data(base_url):
    try:
        ss_id = base_url.split('/d/')[1].split('/')[0]
        # 「未処理確認」シートを狙い撃ち
        target_sheet_url = f"https://docs.google.com/spreadsheets/d/{ss_id}/gviz/tq?tqx=out:csv&sheet=未処理確認"
        rows = load_sheet_data(target_sheet_url)
        
        if not rows:
            rows = load_sheet_data(base_url)

        if rows and len(rows) > 1:
            for row in rows[1:]:
                if len(row) >= 12:
                    # B列(1)に入力があり、L列(11)が空
                    if row[1].strip() != "" and row[11].strip() == "":
                        return True
    except:
        pass
    return False

# --- 画像ボタン表示 ---
def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

def clickable_image(img_path, url, fallback_emoji, alert=False):
    img_base64 = get_base64_of_bin_file(img_path)
    border_style = "border: 8px solid red; box-shadow: 0 0 15px red;" if alert else "border: 8px solid transparent;"
    
    if img_base64:
        html = f'<a href="{url}" target="_blank"><img src="data:image/png;base64,{img_base64}" style="width: 100%; aspect-ratio: 1/1; object-fit: contain; cursor: pointer; border-radius: 20px; {border_style}"></a>'
    else:
        html = f'<a href="{url}" target="_blank"><div style="width: 100%; aspect-ratio: 1/1; background-color: #f0f2f6; border-radius: 20px; display: flex; align-items: center; justify-content: center; font-size: 50px; {border_style}">{fallback_emoji}</div></a>'
    st.markdown(html, unsafe_allow_html=True)

# --- セッション初期化 ---
if 'login_status' not in st.session_state:
    st.session_state.login_status = False

# --- ログイン画面 ---
def login_screen():
    if os.path.exists("1.png"):
        st.image("1.png", use_container_width=True)
    st.markdown("<h2 style='text-align: center;'>ログイン</h2>", unsafe_allow_html=True)
    
    user_code = st.text_input("担当者コード（半角）").strip()
    password = st.text_input("パスワード", type="password").strip()
    
    if st.button("ログイン", use_container_width=True):
        login_sheet_url = "https://docs.google.com/spreadsheets/d/1cPgQ3Ej3P7JZPaxprFQnbnDkCatQ15lEHyF9C9tMgZ4/export?format=csv&gid=0"
        data = load_sheet_data(login_sheet_url)
        
        if data:
            success = False
            for row in data[1:]: # 2行目からチェック
                if len(row) >= 4:
                    # A列(0):コード, C列(2):パスワード を照合
                    if str(row[0]).strip() == user_code and str(row[2]).strip() == password:
                        st.session_state.login_status = True
                        st.session_state.user_name = row[1] # B列:名前
                        st.session_state.user_url = row[3]  # D列:URL
                        success = True
                        break
            
            if success:
                st.rerun()
            else:
                st.error("担当者コードまたはパスワードが違います。スプレッドシートのA列とC列に正しく入力されているか確認してください。")

# --- メイン画面 ---
def main_screen():
    st.markdown(f"<p style='text-align: right; font-weight: bold;'>ログイン中：{st.session_state.user_name} さん</p>", unsafe_allow_html=True)
    if os.path.exists("1.png"): st.image("1.png", use_container_width=True)

    # お知らせ取得
    login_sheet_url = "https://docs.google.com/spreadsheets/d/1cPgQ3Ej3P7JZPaxprFQnbnDkCatQ15lEHyF9C9tMgZ4/export?format=csv&gid=0"
    sheet_rows = load_sheet_data(login_sheet_url)
    announcement = sheet_rows[1][4] if sheet_rows and len(sheet_rows) > 1 and len(sheet_rows[1]) >= 5 else "今日も一日安全運転で！"

    st.markdown(f'''
        <div style="background-color: #fffbe6; border: 2px solid #ffe58f; padding: 10px; border-radius: 10px; display: flex; align-items: center; margin-bottom: 20px;">
            <span style="font-size: 20px; margin-right: 10px;">🔔</span>
            <marquee scrollamount="5" style="color: red; font-weight: bold; font-size: 18px;">{announcement}</marquee>
        </div>
    ''', unsafe_allow_html=True)

    st.write("---")
    has_alert = check_unprocessed_data(st.session_state.user_url)

    col3, col4, col5, col7 = st.columns(4)
    with col3:
        clickable_image("3.png", "https://docs.google.com/forms/d/e/1FAIpQLSc4E3L_UJkVxMMSTOYgcw3SJyoBixHoJfhe0WC-x1wbK6lsHw/viewform?usp=sharing", "📄")
        st.markdown("<p style='text-align:center; font-size:12px; font-weight:bold;'>メンテナンス入力</p>", unsafe_allow_html=True)
    with col4:
        clickable_image("4.png", st.session_state.user_url, "📋", alert=has_alert)
        st.markdown("<p style='text-align:center; font-size:12px; font-weight:bold;'>メンテナンス確認</p>", unsafe_allow_html=True)
    with col5:
        clickable_image("5.png", "https://www.google.com", "📢")
        st.markdown("<p style='text-align:center; font-size:12px; font-weight:bold;'>キャンペーン入力</p>", unsafe_allow_html=True)
    with col7:
        clickable_image("7.png", "https://drive.google.com/drive/folders/1vZE__7Th8RuVtkNQpG-rAZSBtAvG7cTX", "🎓")
        st.markdown("<p style='text-align:center; font-size:12px; font-weight:bold;'>勉強会資料</p>", unsafe_allow_html=True)

    if os.path.exists("6.png"): st.image("6.png", width=180)
    if st.sidebar.button("ログアウト"):
        st.session_state.login_status = False
        st.rerun()

if st.session_state.login_status:
    main_screen()
else:
    login_screen()
