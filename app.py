import streamlit as st
import main 
import re
import os
import mcp_helper
import time
import datetime
from database import log_email_action  # 🟢 Naya Database Import

# ==========================================
# 1. PAGE CONFIGURATION & CUSTOM CSS
# ==========================================
st.set_page_config(page_title="AI Email Agent", page_icon="📧", layout="wide")

st.markdown("""
<style>
    /* Background color aur text visibility fix */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* General text ko dark blue/grey rakhna taaki white background par dikhe */
    .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, label {
        color: #2c3e50 !important; 
    }
    
    /* Heading Gradient Animation */
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .main-header {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background: linear-gradient(45deg, #1e3c72, #2a5298, #00C9FF);
        background-size: 200% 200%;
        animation: gradientShift 4s ease infinite;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0px;
        padding-top: 20px;
    }
    .sub-header {
        text-align: center;
        color: #6c757d !important;
        font-size: 1.1rem;
        margin-bottom: 30px;
        font-style: italic;
    }

    /* Glowing Buttons */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(45deg, #00C9FF, #92FE9D);
        color: #1e3c72 !important;
        border: none;
        border-radius: 25px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    div.stButton > button[kind="primary"]:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 15px rgba(0, 201, 255, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# 🎨 Animated Header
st.markdown('<p class="main-header">✉️ SmartMail AI</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Review, edit, and approve AI-generated actions before execution.</p>', unsafe_allow_html=True)

# ==========================================
# 2. SESSION STATE SETUP
# ==========================================
if 'service' not in st.session_state:
    st.session_state.service = None
if 'emails_data' not in st.session_state:
    st.session_state.emails_data = []

# ==========================================
# 3. SIDEBAR: AUTH & CONTROLS
# ==========================================
with st.sidebar:
    st.header("⚙️ System Controls")
    
    is_logged_in = os.path.exists('token.json')
    
    if is_logged_in:
        st.success("✅ Account Connected")
        if st.button("🔌 Logout / Switch Account", use_container_width=True):
            mcp_helper.run_mcp_tool("trigger_logout")
            st.session_state.service = None
            st.session_state.emails_data = []
            st.rerun()
    else:
        if st.button("🔑 Connect Your Gmail", type="primary", use_container_width=True):
            with st.spinner("Connecting via MCP Server..."):
                mcp_helper.run_mcp_tool("trigger_authentication") 
                st.session_state.service = main.authenticate()
            st.rerun()

    st.divider()
    
    fetch_limit = st.slider("📥 Emails to fetch", 1, 10, 5)
    
    if st.button("🚀 Fetch New Emails", type="primary", use_container_width=True):
        if st.session_state.service is None:
            st.error("Please connect to Gmail first!")
        else:
            with st.spinner("🧠 Llama is classifying emails & drafting replies..."):
                service = st.session_state.service
                results = service.users().messages().list(userId='me', maxResults=fetch_limit).execute()
                messages = results.get('messages', [])
                
                fetched_emails = []
                for msg in messages:
                    msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
                    payload = msg_data.get('payload', {})
                    headers = payload.get('headers', [])
                    
                    sender, subject = "Unknown", "No Subject"
                    for header in headers:
                        if header['name'].lower() == 'from':
                            sender = header['value']
                        elif header['name'].lower() == 'subject':
                            subject = header['value']
                            
                    email_text = main.get_email_body(payload)
                    if not email_text:
                        email_text = msg_data.get('snippet', '')
                        
                    category = main.classify_email(email_text)
                    
                    if category == "Spam":
                        continue
                        
                    match = re.search(r'<([^>]+)>', sender)
                    to_email = match.group(1) if match else sender
                    
                    reply_draft = main.generate_reply(email_text)
                    
                    fetched_emails.append({
                        "id": msg['id'],
                        "sender": sender,
                        "to_email": to_email,
                        "subject": subject,
                        "body": email_text,
                        "category": category,
                        "draft": reply_draft
                    })
                
                st.session_state.emails_data = fetched_emails
            st.success(f"Fetched {len(fetched_emails)} important emails!")

# ==========================================
# 4. MAIN DASHBOARD TABS
# ==========================================
tab1, tab2, tab3 = st.tabs(["📥 Inbox & AI Drafts", "🔍 Search Emails", "📅 Schedule Meeting"])

# --- TAB 1: INBOX & AI DRAFTS ---
with tab1:
    if st.session_state.emails_data:
        st.subheader(f"Inbox: {len(st.session_state.emails_data)} Pending Replies")
        
        for index, email in enumerate(st.session_state.emails_data):
            if email['category'] == 'Priority':
                tag = "🔴 **PRIORITY**"
            else:
                tag = "🔵 **NORMAL**"
                
            with st.expander(f"{tag} | From: {email['sender']} | Sub: {email['subject']}", expanded=False):
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown("### 📥 Original Email")
                    st.info(email['body'])
                    
                with col2:
                    st.markdown("### ✍️ AI Draft (Editable)")
                    edited_reply = st.text_area(
                        "Edit your reply before sending:", 
                        value=email['draft'], 
                        height=200, 
                        key=f"draft_{index}"
                    )
                    
                    btn_col1, btn_col2, btn_col3 = st.columns(3)
                    with btn_col1:
                        if st.button("🚀 Send Email", key=f"send_{index}", type="primary"):
                            with st.spinner("Sending via MCP..."):
                                main.send_email(st.session_state.service, email['to_email'], f"Re: {email['subject']}", edited_reply)
                                
                                # 🟢 NAYA CODE: Save to PostgreSQL
                                log_email_action(email['to_email'], email['subject'], edited_reply, "Sent")
                                
                            st.balloons()
                            st.success("Email Sent & Logged in Database!")
                    with btn_col2:
                        if st.button("💾 Save as Draft", key=f"save_{index}"):
                            main.save_draft(st.session_state.service, email['to_email'], f"Re: {email['subject']}", edited_reply)
                            
                            # 🟢 NAYA CODE: Save to PostgreSQL
                            log_email_action(email['to_email'], email['subject'], edited_reply, "Draft Saved")
                            
                            st.toast("Draft Saved in Gmail & DB!", icon='💾')
                    with btn_col3:
                        if st.button("📎 Get Attachments", key=f"dl_{index}"):
                            with st.spinner("Downloading..."):
                                dl_result = mcp_helper.run_mcp_tool("download_attachments", {"message_id": email['id']})
                                if "✅" in dl_result:
                                    st.success(dl_result)
                                else:
                                    st.warning(dl_result)
    else:
        st.info("No pending emails. Click 'Fetch New Emails' from the sidebar to start.")

# --- TAB 2: AI SEARCH ---
with tab2:
    st.subheader("🔍 Search Emails via AI")
    search_query = st.text_input("Find emails (e.g., 'invoice', 'urgent'):")
    
    if st.button("Search via MCP", type="primary"):
        if st.session_state.service is None:
            st.error("Please connect to Gmail first!")
        elif not search_query:
            st.warning("Please enter a keyword to search.")
        else:
            with st.spinner(f"Searching for '{search_query}'..."):
                search_results = mcp_helper.run_mcp_tool(
                    "search_emails", 
                    {"query": search_query, "max_results": 5}
                )
                st.markdown("**Search Results:**")
                st.info(search_results)

# --- TAB 3: CALENDAR SCHEDULING ---
with tab3:
    st.subheader("📅 Schedule Meeting via MCP")
    
    meeting_title = st.text_input("Meeting Title (e.g., Code Review):")
    
    col_start, col_end = st.columns(2)
    
    with col_start:
        st.markdown("**🟢 Start Details**")
        start_date = st.date_input("Start Date:", datetime.date.today())
        start_time = st.time_input("Start Time:", datetime.time(10, 0))
        
    with col_end:
        st.markdown("**🔴 End Details**")
        end_date = st.date_input("End Date:", datetime.date.today())
        end_time = st.time_input("End Time:", datetime.time(11, 0))
        
    st.markdown("<br>", unsafe_allow_html=True)
        
    if st.button("Schedule Event", type="primary"):
        if st.session_state.service is None:
            st.error("Please connect to Gmail first!")
        elif not meeting_title:
            st.warning("Please enter a meeting title.")
        else:
            with st.spinner("Scheduling Event..."):
                # Background mein proper Google format generate hoga (IST timezone ke sath)
                formatted_start = f"{start_date}T{start_time.strftime('%H:%M:%S')}+05:30"
                formatted_end = f"{end_date}T{end_time.strftime('%H:%M:%S')}+05:30"
                
                cal_result = mcp_helper.run_mcp_tool(
                    "schedule_calendar_event",
                    {
                        "summary": meeting_title,
                        "start_time": formatted_start,
                        "end_time": formatted_end,
                        "description": "Scheduled autonomously via SmartMail AI & MCP Server."
                    }
                )
                
                if "✅" in cal_result:
                    st.toast("Event Scheduled!", icon='📅')
                    st.success(cal_result)
                else:
                    st.error(cal_result)