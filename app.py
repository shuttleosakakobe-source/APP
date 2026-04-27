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

# --- 2. 画像のBase64変換（ファイルがない場合はNoneを返す） ---
def get_image_base64(file_name):
    # GitHub上のファイル名と一致しているか確認してください
    if os.path.exists(file_name):
        with open(file_name, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

# --- 3. メイン画面の表示 ---
def main_screen():
    st.markdown("""
        <style>
        .stApp { background-color: white; }
        .user-label { text-align: right; font-size: 14px; color: #666; font-weight: bold; }
        .button-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin-top: 15px;
        }
        @media (max-width: 600px) {
            .button-grid { grid-template-columns: repeat(2, 1fr); }
        }
        .btn-item { text-align: center; text-decoration: none; display: block; }
        .btn-content {
            width: 100%;
            aspect-ratio: 1/1;
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            background-color: #f0f2f6;
        }
        .btn-image { width: 100%; height: 100%; object-fit: contain; }
        .btn-text { color: black; font-size: 12px; font-weight: bold; margin-top: 5px; line-height: 1.2; }
        .alert-style { border: 5px solid red; box-shadow: 0 0 10px red; }
        .no-border { border: 5px solid transparent; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"<p class='user-label'>👤 {st.session_state.user_name} さん</p>", unsafe_allow_html=True)

    # ロゴ（1.pngがない場合はテキスト表示）
    if os.path.exists("1.png"):
        st.image("1.png", use_container_width=True)
    else:
        st.title("ダスキンシャトル北大阪")

    # お知らせ
    data = load_sheet_data()
    announcement = data[0].get('お知らせ', '安全運転でお願いします') if data else "安全運転でお願いします"
    st.markdown(f'''
        <div style="background-color: #fffbe6; border: 2px solid #ffe58f; padding: 10px; border-radius: 10px; display: flex; align-items: center; margin-bottom: 10px;">
            <span style="font-size: 20px; margin-right: 10px;">🔔</span>
            <marquee scrollamount="5" style="color: red; font-weight: bold; font-size: 18px;">{announcement}</marquee>
        </div>
    ''', unsafe_allow_html=True)

    # 画像の取得（ファイル名は実際のGitHub上のものと合わせてください）
    img3 = get_image_base64("3.png")
    img4 = get_image_base64("4.png")
    img5 = get_image_base64("5.png")
    # 勉強会ロゴ：アップロードした実際のファイル名に書き換えてください
    img7 = get_image_base64("image_d3349a.png") or get_image_base64("7.png")

    def render_button(img_base64, fallback_emoji, label, url, is_alert=False):
        border = "alert-style" if is_alert else "no-border"
        content = f'<img src="data:image/png;base64,{img_base64}" class="btn-image">' if img_base64 else f'<span style="font-size:40px;">{fallback_emoji}</span>'
        return f'''
            <a class="btn-item" href="{url}" target="_blank">
                <div class="btn-content {border}">{content}</div>
                <p class="btn-text">{label}</p>
            </a>
        '''

    # ボタン配置
    st.markdown(f'''
        <div class="button-grid">
            {render_button(img3, "📄", "メンテナンス<br>入力", "https://docs.google.com/forms/d/e/1FAIpQLSc4E3L_UJkVxMMSTOYgcw3SJyoBixHoJfhe0WC-x1wbK6lsHw/viewform?usp=sharing")}
            {render_button(img4, "📋", "メンテナンス<br>確認", st.session_state.user_url, st.session_state.needs_alert)}
            {render_button(img5, "📢", "キャンペーン<br>入力", "https://www.google.com")}
            {render_button(img7, "🎓", "勉強会<br>資料", "https://drive.google.com/drive/folders/1vZE__7Th8RuVtkNQpG-rAZSBtAvG7cTX")}
        </div>
    ''', unsafe_allow_html=True)

    st.write("---")
    if os.path.exists("6.png"): st.image("6.png", width=150)
    if st.sidebar.button("ログアウト"):
        st.session_state.login_status = False
        st.rerun()

# --- ログイン画面 ---
def login_screen():
    if os.path.exists("1.png"): st.image("1.png", use_container_width=True)
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
                f_val = list(user_match.values())[5] if len(user_match) >= 6 else "0"
                try: st.session_state.needs_alert = float(f_val) != 0
                except: st.session_state.needs_alert = str(f_val).strip() != "" and str(f_val).strip() != "0"
                st.rerun()
            else: st.error("コードまたはパスワードが正しくありません")

if 'login_status' not in st.session_state: st.session_state.login_status = False
if st.session_state.login_status: main_screen()
else: login_screen()
