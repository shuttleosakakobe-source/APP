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

    if st.session_state.user_role != "3":
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

        if st.button("🚀 ナビゲーションシステムを開く", type="primary", use_container_width=True):
            st.session_state.current_page = "nav"
            st.rerun()

    if st.session_state.user_role in ["0", "3"]:
        st.write("---")
        st.write("### 🛠️ メンテナンス管理メニュー")

        url_sheet1 = "https://docs.google.com/spreadsheets/d/16JhXHMdYPoOIQmPBgd2sVclYkdYip6arRHtr86hr9hg/export?format=csv&gid=1365103622"
        url_sheet2 = "https://docs.google.com/spreadsheets/d/1DShHig4iOhNXOkxMfALTRhyH0P5dtVpdBkNXvVQPC3g/export?format=csv&gid=1365103622"
        url_sheet3 = "https://docs.google.com/spreadsheets/d/1kk9vFlE6LiBDMp6B4phUtnGs8CZfV8uhgkS-atdbBG0/export?format=csv&gid=1365103622"

        rows1 = load_sheet_data(custom_url=url_sheet1)
        rows2 = load_sheet_data(custom_url=url_sheet2)
        rows3 = load_sheet_data(custom_url=url_sheet3)

        alert1 = rows1 and len(rows1) >= 2 and any(cell.strip() != "" for cell in rows1[1][:15])
        alert2 = rows2 and len(rows2) >= 2 and any(cell.strip() != "" for cell in rows2[1][:15])
        alert3 = rows3 and len(rows3) >= 2 and any(cell.strip() != "" for cell in rows3[1][:15])

        if alert1 or alert2 or alert3:
            st.markdown('<span class="alert-text">⚠️ 管理メニューに未処理のデータがあります</span>', unsafe_allow_html=True)

        btn_img1 = get_img_html("3.png", "⚙️", alert=alert1, width="85px")
        btn_img2 = get_img_html("8.png", "🔍", alert=alert2, width="85px")
        btn_img3 = get_img_html("4.png", "𖖨️", alert=alert3, width="85px")

        grid_html_3 = f'''
            <div class="button-grid-3">
                <a class="btn-item" href="https://docs.google.com/spreadsheets/d/16JhXHMdYPoOIQmPBgd2sVclYkdYip6arRHtr86hr9hg/edit?gid=1365103622#gid=1365103622" target="_blank">
                    {btn_img1}<p class="btn-text" style="margin-top:8px;">1. メンテナンス処理</p>
                </a>
                <a class="btn-item" href="https://docs.google.com/spreadsheets/d/1DShHig4iOhNXOkxMfALTRhyH0P5dtVpdBkNXvVQPC3g/edit?gid=1365103622#gid=1365103622" target="_blank">
                    {btn_img2}<p class="btn-text" style="margin-top:8px;">2. メンテナンスチェック</p>
                </a>
                <a class="btn-item" href="https://docs.google.com/spreadsheets/d/1kk9vFlE6LiBDMp6B4phUtnGs8CZfV8uhgkS-atdbBG0/edit?gid=1365103622#gid=1365103622" target="_blank">
                    {btn_img3}<p class="btn-text" style="margin-top:8px;">3. 印刷用</p>
                </a>
            </div>
        '''
        st.markdown(grid_html_3, unsafe_allow_html=True)
        
        render_daily_checklist()

    st.write("---")
    if st.button("🚪 ログアウト / ユーザー切替", key="footer_logout_btn", type="secondary", use_container_width=True):
        process_logout()

    if os.path.exists("6.png"): st.image("6.png", width=110)

# --- 7. 実行ロジック ---
if 'login_status' not in st.session_state: st.session_state.login_status = False
if 'logout_requested' not in st.session_state: st.session_state.logout_requested = False
if 'current_page' not in st.session_state: st.session_state.current_page = "main"
if 'selected_route_nodes' not in st.session_state: st.session_state.selected_route_nodes = [{"名前": "📌 現在地", "住所": "現在地"}]
if 'moved_to_bottom_names' not in st.session_state: st.session_state.moved_to_bottom_names = []
if 'needs_alert' not in st.session_state: st.session_state.needs_alert = False

if not st.session_state.login_status and not st.session_state.logout_requested:
    from streamlit_javascript import st_javascript 
    local_name = st_javascript("sessionStorage.getItem('shuttle_user_name');")
    local_role = st_javascript("sessionStorage.getItem('shuttle_user_role');")
    local_code = st_javascript("sessionStorage.getItem('shuttle_user_code');")
    local_url = st_javascript("sessionStorage.getItem('shuttle_user_url');")
    
    if local_name and local_role and local_code:
        st.session_state.user_name = str(local_name)
        st.session_state.user_role = str(local_role)
        st.session_state.user_code = str(local_code)
        st.session_state.user_url = str(local_url) if local_url else ""
        st.session_state.login_status = True

if st.session_state.login_status:
    if st.session_state.current_page in ["navi", "nav"]:
        route_navigation_screen()
    else:
        main_screen()
else:
    inject_pwa_blocker() 
    if os.path.exists("1.png"): st.image("1.png", use_container_width=True)
    u_code = st.text_input("担当者コード").strip()
    u_pass = st.text_input("パスワード", type="password").strip()
    
    if st.button("ログイン", type="primary", use_container_width=True):
        raw = load_sheet_data(gid="0")
        if raw:
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
                st.session_state.current_page = "main"
                
                set_login_storage(st.session_state.user_name, st.session_state.user_url, st.session_state.needs_alert, st.session_state.user_role, st.session_state.user_code)
                st.rerun()
            else:
                st.error("認証失敗")
        else:
            st.error("マスターデータの読み込みに失敗しました")
