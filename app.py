        .today-val { font-size: 14px; font-weight: bold; color: #cd1212; }
        
        div.stButton > button {
            width: 100% !important;
            height: auto !important;
            min-height: 46px !important;
            padding: 10px 14px !important;
            border-radius: 10px !important;
            font-weight: bold !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important; 
        }
        
        div.stButton > button p {
            text-align: left !important;
            width: 100% !important;
            display: block !important;
            white-space: normal !important; 
            word-break: break-all !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        div[data-testid="stModal"] { transition: none !important; animation: none !important; }
        div[role="dialog"] { transition: none !important; animation: none !important; }
        div[data-testid="stToast"] { transition: none !important; animation: none !important; }
        </style>
    """, unsafe_allow_html=True)

    data_raw = load_sheet_data(gid="0")
    if not data_raw or len(data_raw) < 2:
        st.error("マスターデータの読み込みに失敗しました。スプレッドシートの公開設定と通信状況を確認してください。")
        return

    header = data_raw[0]
    data = [dict(zip(header, row)) for row in data_raw[1:]]
    
    current_user_data = next((r for r in data if r.get('担当者名') == st.session_state.user_name), None)
    if current_user_data:
        vals = list(current_user_data.values())
        st.session_state.needs_alert = (len(vals) > 5 and str(vals[5]).strip() not in ["0", "", "None"])

    st.markdown('<div class="user-label-btn">', unsafe_allow_html=True)
    if st.button(f"👤 {st.session_state.user_name} さん", key="hidden_toggle"):
        if st.session_state.user_role != "0" and st.session_state.user_role != "3":
            st.session_state.show_timecard = not st.session_state.get('show_timecard', False)
    st.markdown('</div>', unsafe_allow_html=True)

    if os.path.exists("1.png"): st.image("1.png", use_container_width=True)

    announcement = data[0].get('お知らせ', '安全運転でお願いします')
    st.markdown(f'''
        <div style="background-color:#fffbe6; border:2px solid #ffe58f; padding:10px; border-radius:10px; display:flex; align-items:center; margin-top: 5px;">
            <span style="font-size:16px; margin-right:8px;">🔔</span>
            <marquee scrollamount="5" style="color:red; font-weight:bold; font-size:16px;">{h(announcement)}</marquee>
        </div>
    ''', unsafe_allow_html=True)

    if st.session_state.user_role == "0":
        st.session_state.show_timecard = True

    if st.session_state.user_role != "3" and st.session_state.get('show_timecard', False):
        st.write("")
        st.write("### 🕒 勤怠・所在打刻")
        att_col1, att_col2, att_col3 = st.columns(3)
        
        status_click = None
        with att_col1:
            if st.button("🌅 出社", key="time_in_btn", use_container_width=True): status_click = "出社"
        with att_col2:
            if st.button("🚗 帰社", key="time_mid_btn", use_container_width=True): status_click = "帰社"
        with att_col3:
            if st.button("🌃 退社", key="time_out_btn", use_container_width=True): status_click = "退社"
            
        if status_click:
            with st.spinner("タイムカード記録中..."):
                res = post_to_gas({
                    "status": "TIMECARD",
                    "code": st.session_state.get('user_code', ''),
                    "name": st.session_state.get('user_name', ''),
                    "timecard_status": status_click
                })
                if res.get("status") == "success":
                    st.toast(f"🎉 {status_click} を記録しました！", icon="✅")
                else:
                    st.error(f"通信に失敗しました: {res.get('message')}")
            st.rerun()
        st.write("---")

    if st.session_state.user_role != "3":
        visit_info, today_sched = get_visit_schedule_data(st.session_state.get('user_code', ''))
        w1_disp = visit_info.get("1W", {}).get("display", "--/--")
        w2_disp = visit_info.get("2W", {}).get("display", "--/--")
        w4_disp = visit_info.get("4W", {}).get("display", "--/--")
        w8_disp = visit_info.get("8W", {}).get("display", "--/--")
        
        today_str = get_jst_today().strftime('%m/%d')
        hide_keywords = ["勉強会", "空き日", "休", "チーフ出勤"]
        should_hide = any(kw in today_sched for kw in hide_keywords)

        if should_hide:
            st.markdown(f'''
                <div class="visit-container">
                    <div class="today-schedule-box">
                        <span class="today-title">📌 本日の予定 ({today_str})</span>
                        <span class="today-val">{h(today_sched)}</span>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown(f'''
                <div class="visit-container">
                    <div class="visit-title">📅 次回訪問日</div>
                    <div class="visit-grid">
                        <div class="visit-box"><div class="visit-label">1W</div><div class="visit-date">{h(w1_disp)}</div></div>
                        <div class="visit-box"><div class="visit-label">2W</div><div class="visit-date">{h(w2_disp)}</div></div>
                        <div class="visit-box"><div class="visit-label">4W</div><div class="visit-date">{h(w4_disp)}</div></div>
                        <div class="visit-box"><div class="visit-label">8W</div><div class="visit-date">{h(w8_disp)}</div></div>
                    </div>
                    <div class="today-schedule-box">
                        <span class="today-title">📌 本日の予定 ({today_str})</span>
                        <span class="today-val">{h(today_sched)}</span>
                    </div>
                </div>
            ''', unsafe_allow_html=True)

    if st.session_state.user_role in ["0", "1"]:
        check_sheet_rows = load_sheet_data(gid="1552856942")
        check_alert = False
        if check_sheet_rows and len(check_sheet_rows) >= 2:
            target_cells = check_sheet_rows[1][:10]
            if any(cell.strip() != "" for cell in target_cells):
                check_alert = True
        
        alert_rows = []
        for row in data:
            vals = list(row.values())
            if len(vals) >= 6 and str(vals[5]).strip() not in ["0", "", "None"]:
                alert_rows.append({"name": str(vals[1]), "url": str(vals[3])})

        st.write("") 
        col_admin1, col_admin2 = st.columns([1, 1])
        with col_admin1:
            c_btn = get_img_html("8.png", "🔍", alert=check_alert, width="90px")
            check_url = "https://docs.google.com/spreadsheets/d/1EofzMjd3dAq8sRCdQXpxw3_-T1VDWpd-aDrvxWD4fYc/edit?gid=1552856942#gid=1552856942"
            st.markdown(f'''
                <div class="admin-box">
                    <a href="{check_url}" target="_blank" style="text-decoration:none; color:black;">
                        {c_btn}
                        <p class="btn-text" style="margin-top: 12px;">メンテナンス<br>チェック</p>
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
