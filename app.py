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

# --- スプレッドシート取得 ---
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

# --- 画像を読み込んでBase64化する関数 ---
def get_img_html(file_name, emoji, alert=False):
    border = "5px solid red" if alert else "5px solid transparent"
    shadow = "box-shadow: 0 0 10px red;" if alert else ""
    
    if os.path.exists(file_name):
        with open(file_name, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        return f'<img src="data:image/png;base64,{data}" style="width:100%; aspect-ratio:1/1; object-fit:contain; border-radius:15px; border:{border}; {shadow}">'
    else:
        # 画像がない場合は絵文字で代用
        return f'<div style="width:100%; aspect-ratio:1/1; background:#f0f2f6; border-radius:15px; display:flex; align-items:center; justify-content:center; font-size:40px; border:{border}; {shadow}">{emoji}</div>'

# --- メイン画面 ---
def main_screen():
    # PC/スマホの出し分け用CSS
    st.markdown("""
        <style>
        .stApp { background-color: white; }
        .user-label { text-align: right; font-size: 14px; color: #666; font-weight: bold; }
        
        /* ボタンのグリッド設定 */
        .button-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr); /* PCは4列 */
            gap: 10px;
            margin-top: 10px;
        }
        @media (max-width: 600px) {
            .button-grid {
                grid-template-columns: repeat(2, 1fr); /* スマホは2列 */
            }
        }
        .btn-item { text-align: center; text-decoration: none; display: block; }
        .btn-text { color: black; font-size: 12px; font-weight: bold; margin-top: 5px; line-height: 1.2; }
        </marquee>
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"<p class='user-label'>👤 {st.session_state.user_name} さん</p>", unsafe_allow_html=True)

    if os.path.exists("1.png"):
        st.image("1.png", use_container_width=True)

    # お知らせ（ログインシートから取得）
    data = load_sheet_data()
    announcement = data[0].get('お知らせ', '今日も一日安全運転で！') if data else "安全運転で！"

    st.markdown(f'''
        <div style="background-color: #fffbe6; border: 2px solid #ffe58f; padding: 10px; border-radius: 10px; display: flex; align-items: center; margin-bottom: 10px;">
            <span style="font-size: 20px; margin-right: 10px;">🔔</span>
            <marquee scrollamount="5" style="color: red; font-weight: bold; font-size: 18px;">{announcement}</marquee>
        </div>
    ''', unsafe_allow_html=True)

    # 各ボタンのHTMLを作成
    # ファイル名は大文字小文字まで正確に合わせてください（image_d3349a.pngなど）
    html_btn1 = get_img_html("3.png", "📄")
    html_btn2 = get_img_html("4.png", "📋", alert=st.session_state.needs_alert)
    html_btn3 = get_img_html("5.png", "📢")
    html_btn4 = get_img_html("image_d3349a.png", "🎓") # 新しい勉強会ロゴ

    # ★ ここが重要：全体をひとつの st.markdown で出力する
    full_html = f'''
        <div class="button-grid">
            <a class="btn-item" href="https://docs.google.com/forms/d/e/1FAIpQLSc4E3L_UJkVxMMSTOYgcw3SJyoBixHoJfhe0WC-x1wbK6lsHw/viewform?usp=sharing" target="_blank">
                {html_btn1}<p class="btn-text">メンテナンス<br>入力</p>
            </a>
            <a class="btn-item" href="{st.session_state.user_url}" target="_blank">
                {html_btn2}<p class="btn-text">メンテナンス<br>確認</p>
            </a>
            <a class="btn-item" href="https://www.google.com" target="_blank">
                {html_btn3}<p class="btn-text">キャンペーン<br>入力</p>
            </a>
            <a class="btn-item" href="https://drive.google.com/drive/folders/1vZE__7Th8RuVtkNQpG-rAZSBtAvG7cTX" target="_blank">
                {html_btn4}<p class="btn-text">勉強会<br>資料</p>
            </a>
        </div>
    '''
    st.markdown(full_html, unsafe_allow_html=True)

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
                # F列(0から数えて5番目)が「0」以外なら赤枠
                vals = list(user_match.values())
                f_val = vals[5] if len(vals) >= 6 else "0"
                try:
                    st.session_state.needs_alert = (float(f_val) != 0)
                except:
                    st.session_state.needs_alert = (str(f_val).strip() != "0" and str(f_val).strip() != "")
                st.rerun()
            else:
                st.error("コードまたはパスワードが違います")

# --- 実行 ---
if 'login_status' not in st.session_state: st.session_state.login_status = False
if st.session_state.login_status:
    main_screen()
else:
    login_screen()
