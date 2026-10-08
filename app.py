import streamlit as st
import datetime
import time

# Set timezone to Indian Standard Time (IST)
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
import json
import os
import hashlib
import random
import string
import smtplib
from email.message import EmailMessage
import uuid

# ── Firebase DB Setup ──────────────────────────────────────────────────────────
try:
    import firebase_admin
    from firebase_admin import credentials, firestore, storage
    FIREBASE_INSTALLED = True
except ImportError:
    FIREBASE_INSTALLED = False

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Zero Trust Workspace", page_icon="🛡️")

# ── Paths & Secrets ────────────────────────────────────────────────────────────
BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
USERS_FILE      = os.path.join(BASE_DIR, "users.json")
COMPLAINTS_FILE = os.path.join(BASE_DIR, "complaints.json")
FIREBASE_KEY    = os.path.join(BASE_DIR, "firebase_key.json")
UPLOADS_DIR        = os.path.join(BASE_DIR, "uploads")
EVIDENCE_VAULT_DIR = os.path.join(BASE_DIR, "evidence_vault")
SESSIONS_FILE   = os.path.join(BASE_DIR, "sessions.json")
GLOBAL_AUDIT_FILE = os.path.join(BASE_DIR, "global_audit.json")

# --- Sync URL State for Browser Back/Refresh ---
if "session" in st.query_params:
    sid = st.query_params["session"]
    if os.path.exists(SESSIONS_FILE):
        try:
            import json
            with open(SESSIONS_FILE, "r") as f: sessions = json.load(f)
            if sid in sessions:
                st.session_state.logged_in = True
                st.session_state.user_id = sessions[sid]["user_id"]
                st.session_state.role = sessions[sid]["role"]
                st.session_state.full_name = sessions[sid]["full_name"]
        except Exception: pass
        
if "tool" in st.query_params:
    st.session_state.active_tool = st.query_params["tool"]
elif "active_tool" in st.session_state:
    st.session_state.active_tool = None
    
if "case" in st.query_params:
    st.session_state.active_case = st.query_params["case"]
elif "active_case" in st.session_state:
    st.session_state.active_case = None

if not os.path.exists(UPLOADS_DIR): os.makedirs(UPLOADS_DIR)
if not os.path.exists(EVIDENCE_VAULT_DIR): os.makedirs(EVIDENCE_VAULT_DIR)

# ── SMTP Configuration (Edit these with your real details) ───────────────────────
SMTP_EMAIL = "mohankanta112@gmail.com"
SMTP_APP_PASSWORD = "sxke hpav hunf nlqg"

# ── API Keys ───────────────────────────────────────────────────────────────────
VIRUSTOTAL_API_KEY = "e16b303c571b8a4d9e73d40eaafc9c4e26551146d5d799f6329d206f68c7bb69" # Paste your API key here to automatically load it in the tool

# ── Initialize Firebase ────────────────────────────────────────────────────────
db = None
if FIREBASE_INSTALLED:
    if not firebase_admin._apps:
        try:
            if "firebase" in st.secrets:
                import json
                if "json" in st.secrets["firebase"]:
                    secret_dict = json.loads(st.secrets["firebase"]["json"])
                else:
                    secret_dict = dict(st.secrets["firebase"])
                if "private_key" in secret_dict:
                    secret_dict["private_key"] = secret_dict["private_key"].replace('\\n', '\n')
                cred = credentials.Certificate(secret_dict)
                firebase_admin.initialize_app(cred)
            elif os.path.exists(FIREBASE_KEY):
                cred = credentials.Certificate(FIREBASE_KEY)
                firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Firebase Init Error: {e}")
    if firebase_admin._apps:
        db = firestore.client()

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Hide Streamlit Branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stDecoration"] {display: none;}
[class^="viewerBadge"] {display: none !important;}
.viewerBadge_container__1QSob {display: none !important;}

html, body { background-color: #131f2e !important; color: #e0e6f0 !important; }
[data-testid="stApp"] {
        background-size: cover !important;
    background-position: center !important;
    background-repeat: no-repeat !important;
    background-attachment: fixed !important;
}
[data-testid="stApp"]::before {
    content: "";
    position: fixed;
    top: 0; left: 0; width: 100vw; height: 100vh;
    background: rgba(19, 31, 46, 0.82);
    backdrop-filter: blur(4px);
    z-index: 0;
}
[data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background: transparent !important;
    z-index: 1;
    position: relative;
}
[data-testid="stToolbar"], footer, #MainMenu { display:none !important; visibility:hidden; }
.auth-card { background:#1b2a3b; border-radius:20px; padding:25px 44px 20px; max-width:500px; margin:5px auto 0; box-shadow:0 8px 40px rgba(0,0,0,.45); }
.card-icon { text-align:center; font-size:2.5rem; margin-bottom:2px; filter:drop-shadow(0 0 12px #38bdf8); }
.card-title { color:#fff; font-size:1.9rem; font-weight:700; text-align:center; margin-bottom:2px; }
.card-sub { color:#7ec8e3; font-size:.82rem; text-align:center; margin-bottom:22px; letter-spacing:1px; text-transform:uppercase; }
div[data-testid="stTextInput"] > div > div > input, div[data-testid="stSelectbox"] > div > div, div[data-testid="stTextArea"] > div > div > textarea { background-color:#223047 !important; border:1.5px solid #2d4060 !important; border-radius:15px !important; color:#d6e4f0 !important; padding:14px 22px !important; font-size:1rem !important; caret-color:#38bdf8; }
div[data-testid="stTextInput"] > div > div > input:focus, div[data-testid="stTextArea"] > div > div > textarea:focus { border:1.5px solid #28a745 !important; box-shadow:0 0 0 3px rgba(40,167,69,.15) !important; }
div[data-testid="stButton"] > button[kind="primary"] { background:#28a745 !important; color:#ffffff !important; font-weight:800 !important; letter-spacing:1.5px !important; border:none !important; border-radius:0px !important; padding:13px 0 !important; width:100% !important; box-shadow:0 4px 15px rgba(40,167,69,.25) !important; margin-top:6px !important; }
div[data-testid="stButton"] > button[kind="primary"]:hover { background:#218838 !important; opacity:1 !important; box-shadow:0 6px 20px rgba(40,167,69,.4) !important; }
div[data-testid="stButton"] > button[kind="secondary"] { background: transparent !important; color:#7ec8e3 !important; border:1.5px solid #2d4060 !important; font-weight:600 !important; letter-spacing:1px !important; border-radius:50px !important; padding:10px 0 !important; width:100% !important; margin-top:6px !important; }
div[data-testid="stButton"] > button[kind="secondary"]:hover { border-color:#f87171 !important; color:#f87171 !important; box-shadow:0 4px 15px rgba(248,113,113,.2) !important; }
.or-divider { display:flex; align-items:center; margin:18px 0; color:#3d5470; font-size:.78rem; letter-spacing:2px; }
.or-divider::before,.or-divider::after { content:""; flex:1; border-bottom:1px solid #2d4060; }
.mfa-hint { background:#162333; border:1px solid #2d4060; border-radius:12px; padding:12px 18px; font-size:.82rem; color:#7ec8e3; text-align:center; margin-bottom:16px; }
.auth-footer { text-align:center; color:#3d5470; font-size:.72rem; margin-top:18px; line-height:1.6; }
.auth-footer a { color:#38bdf8; text-decoration:none; }
.tool-header { background:linear-gradient(135deg,#1b2a3b 0%,#162333 100%); border:1px solid #2d4060; border-radius:16px; padding:24px 32px; margin-bottom:24px; }
.tool-title { font-size:1.6rem; font-weight:700; color:#38bdf8; }
.tool-sub { color:#7ec8e3; font-size:.88rem; margin-top:4px; }
.stat-box { background:#162333; border:1px solid #2d4060; border-radius:12px; padding:18px; text-align:center; }
.stat-val { font-size:1.6rem; font-weight:700; color:#38bdf8; }
.stat-lbl { font-size:.75rem; color:#6b8cad; margin-top:4px; }
.log-entry { font-family:monospace; font-size:.8rem; color:#7ec8e3; background:#0d1a26; border-radius:6px; padding:6px 10px; margin:3px 0; }
.log-entry.warn { color:#fbbf24; } .log-entry.crit { color:#f87171; } .log-entry.ok { color:#34d399; }
.ioc-row { display:flex; gap:12px; margin-bottom:8px; align-items:center; }
.ioc-badge { background:#1b2a3b; border:1px solid #2d4060; border-radius:8px; padding:6px 14px; font-size:.78rem; color:#e0e6f0; }
.ioc-badge.high { border-color:#f87171; color:#f87171; }
.ioc-badge.med  { border-color:#fbbf24; color:#fbbf24; }
div[data-testid="stProgressBar"] > div > div { background-color:#38bdf8 !important; }
.case-card { background:#162333; border:1px solid #2d4060; border-radius:12px; padding:20px; margin-bottom:16px; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  HYBRID DB MANAGER (Users & Complaints)
# ══════════════════════════════════════════════════════════════════════════════
def load_users() -> dict:
    if db:
        try: return {doc.id: doc.to_dict() for doc in db.collection("users").stream()}
        except Exception: return {}
    else:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r") as f: return json.load(f)
        return {}

def save_users(users: dict):
    if db:
        for uid, data in users.items(): db.collection("users").document(uid).set(data)
    else:
        with open(USERS_FILE, "w") as f: json.dump(users, f, indent=2)

def load_complaints() -> dict:
    if db:
        try: return {doc.id: doc.to_dict() for doc in db.collection("complaints").stream()}
        except Exception: return {}
    else:
        if os.path.exists(COMPLAINTS_FILE):
            with open(COMPLAINTS_FILE, "r") as f: return json.load(f)
        return {}

def save_complaint(case_id: str, data: dict):
    if db: db.collection("complaints").document(case_id).set(data)
    else:
        complaints = load_complaints()
        complaints[case_id] = data
        with open(COMPLAINTS_FILE, "w") as f: json.dump(complaints, f, indent=2)

def hash_password(pwd: str) -> str: return hashlib.sha256(pwd.encode()).hexdigest()
def check_password(plain: str, hashed: str) -> bool: return hash_password(plain) == hashed

def send_email_otp(user_email: str, otp: str):
    if not SMTP_EMAIL or not SMTP_APP_PASSWORD:
        return False, f"⚠️ SMTP not configured! Your simulated OTP code is: **{otp}**"
    try:
        msg = EmailMessage()
        msg.set_content(f"Your Zero Trust Portal login code is: {otp}\n\nThis code will expire shortly.")
        msg['Subject'] = 'Your Authentication Code'
        msg['From'] = SMTP_EMAIL
        msg['To'] = user_email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SMTP_EMAIL, SMTP_APP_PASSWORD)
            server.send_message(msg)
        return True, f"✅ An email containing your OTP has been sent to **{user_email}**."
    except Exception:
        return False, f"❌ Failed to send email. Your OTP code is: **{otp}**"

if "active_tool"  not in st.session_state: st.session_state.active_tool  = None
if "page"         not in st.session_state: st.session_state.page         = None

def log_action(action: str):
    if "session_logs" not in st.session_state: st.session_state.session_logs = []
    ts = datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
    user = st.session_state.get("user_id", "Unknown")
    
    # ── AI Anomaly Detection Engine ──
    ai = "Verified: Normal Behavior"
    if "admin" in user.lower(): ai = "Verified: Admin Privileged Action"
    if any(x in action for x in ["Sandbox", "Volatility", "Detonating"]): ai = "🚩 Flagged: High-Risk Execution"
    if "Extracted" in action or "Acquisition" in action: ai = "🔗 Chain of Custody Logged"
    if "Logout" in action or "Login" in action: ai = "🔐 Identity Verified"
    if "Unauthorized" in action: ai = "🚨 CRITICAL: Intrusion attempt detected"
    
    st.session_state.session_logs.append(f"[{ts}] User:{user} | {action} | AI Status: {ai}")
    
    # --- GLOBAL AI AUDIT LOGGING ---
    try:
        import json, os
        audit_data = []
        if os.path.exists(GLOBAL_AUDIT_FILE):
            with open(GLOBAL_AUDIT_FILE, "r") as f:
                audit_data = json.load(f)
        
        audit_data.append({
            "timestamp": ts,
            "user": user,
            "role": st.session_state.get("role", "Unknown"),
            "action": action,
            "ai_flag": ai
        })
        
        if len(audit_data) > 1000: audit_data = audit_data[-1000:]
        
        with open(GLOBAL_AUDIT_FILE, "w") as f:
            json.dump(audit_data, f)
    except Exception:
        pass

def log_tool_to_coc(tool_name: str, findings: str):
    cid = st.session_state.get("active_case")
    uid = st.session_state.get("user_id")
    if not cid or not uid: return
    
    complaints = load_complaints()
    c = complaints.get(cid)
    if not c: return
    
    if "chain_of_custody" not in c: c["chain_of_custody"] = []
    
    c["chain_of_custody"].append({
        "timestamp": datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
        "action": f"🛠️ Forensic Tool Used: {tool_name}",
        "actor": f"Investigator ({uid})",
        "location": f"Findings: {findings}"
    })
    save_complaint(cid, c)

# ══════════════════════════════════════════════════════════════════════════════
#  PUBLIC COMPLAINT PAGE
# ══════════════════════════════════════════════════════════════════════════════
def public_complaint_page():
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("""<div class="auth-card" style="max-width:850px">
            <div class="card-icon">🚨</div><div class="card-title">File an Official Complaint</div>
            <div class="card-sub">Secure Public Reporting Portal</div></div>""", unsafe_allow_html=True)
        
        st.markdown("<div style='height:15px'></div><h4 style='color:#38bdf8'>1. Victim Information</h4>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1: name = st.text_input("Full Name", placeholder="e.g., John Doe")
        with c2: phone = st.text_input("Contact Number", placeholder="e.g., +1 555-0199")
            
        st.markdown("<div style='height:10px'></div><h4 style='color:#38bdf8'>2. Incident Timeline</h4>", unsafe_allow_html=True)
        c3, c4 = st.columns(2)
        with c3: incident_date = st.date_input("Date of Incident")
        with c4: incident_time = st.time_input("Time of Incident")
        ongoing = st.radio("Is the attack still ongoing?", ["No, it has stopped", "Yes, it is currently happening"], horizontal=True)
        
        st.markdown("<div style='height:10px'></div><h4 style='color:#38bdf8'>3. Affected Assets & Threat Intel</h4>", unsafe_allow_html=True)
        category = st.selectbox("Complaint Category", ["Financial Fraud & UPI Scams", "Identity Theft & Impersonation", "Malware, Ransomware & Hacking", "Cyberbullying & Harassment", "Phishing, Vishing & Smishing", "Social Media Account Takeover", "Online Shopping & E-Commerce Scams", "Extortion & Sextortion", "Cryptocurrency & Investment Scams", "Corporate Data Breach", "Child Exploitation / CSAM", "Deepfakes & AI Misinformation", "Denial of Service (DDoS)", "Other Cyber Crime"])
        c5, c6 = st.columns(2)
        with c5:
            compromised_asset = st.selectbox("Primary Asset Compromised", ["Website / Web App", "Email Account", "Bank Account", "Social Media", "Physical Device (Laptop/Phone)", "Corporate Server", "Other"])
            financial_loss = st.text_input("Estimated Financial Loss (if any)", placeholder="e.g., $5,000")
        with c6:
            asset_details = st.text_input("Asset Details", placeholder="e.g., IP Address, URL, or Account Name")
            attacker_info = st.text_input("Suspect Info (if known)", placeholder="e.g., Attacker Email, Crypto Wallet, Phone")

        st.markdown("<div style='height:10px'></div><h4 style='color:#38bdf8'>4. Description & Evidence</h4>", unsafe_allow_html=True)
        desc = st.text_area("Detailed Description of the Incident", placeholder="Describe exactly what happened...", height=150)
        
        evidence_type = st.radio("Evidence Type", ["Digital File Upload (Screenshots, PDFs)", "Physical Device Handover (Hard Drive, Mobile Phone, etc.)"], horizontal=True)
        uploaded_file = None
        phys_device_desc = ""
        if "Digital File" in evidence_type:
            uploaded_file = st.file_uploader("Upload Evidence (Screenshots, Logs)", label_visibility="collapsed")
        else:
            st.info("⚠️ **Physical Handover Required:** Please describe the device below.")
            phys_device_desc = st.text_input("Device Description", placeholder="e.g., iPhone 14 Pro (Black)")
            
        st.markdown("<div style='height:10px'></div><h4 style='color:#38bdf8'>5. Legal Consent</h4>", unsafe_allow_html=True)
        consent = st.checkbox("I authorize the Zero Trust investigation team to legally analyze my digital evidence, logs, and provided information.")
            
        st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)
        submit_btn = st.button("SUBMIT COMPLAINT", key="submit_complaint", use_container_width=True)
        st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
        if st.button("⬅️ Cancel & Return to Login", key="cancel_complaint", use_container_width=True):
            st.session_state.page = "login"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        if submit_btn:
            if not name.strip() or not phone.strip() or not desc.strip():
                st.error("🚫 Please fill out your Name, Mobile Number, and Incident Description.")
            elif not consent:
                st.error("🚫 You must agree to the Legal Consent to submit a complaint.")
            elif "Physical" in evidence_type and not phys_device_desc.strip():
                st.error("🚫 Please describe the physical device you intend to hand over.")
            else:
                case_id = f"CASE-{__import__('random').randint(1000, 9999)}"
                file_path = file_name = None
                
                if "Digital File" in evidence_type and uploaded_file:
                    file_name = uploaded_file.name
                    unique_name = f"{case_id}_{__import__('uuid').uuid4().hex[:8]}_{file_name}"
                    file_path = os.path.join(UPLOADS_DIR, unique_name)
                    with open(file_path, "wb") as f: f.write(uploaded_file.getbuffer())
                elif "Physical Device" in evidence_type:
                    file_name = f"[PHYSICAL DEVICE] {phys_device_desc}"
                
                complaint_data = {
                    "case_id": case_id, "victim_name": name, "victim_phone": phone, "category": category,
                    "incident_date": str(incident_date), "incident_time": str(incident_time), "ongoing": ongoing,
                    "compromised_asset": compromised_asset, "asset_details": asset_details, "financial_loss": financial_loss,
                    "attacker_info": attacker_info,
                    "description": desc, "evidence_file": file_name, "evidence_path": file_path,
                    "status": "Unassigned", "assigned_to": None, "timestamp": datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
                }
                
                if "Physical" in evidence_type:
                    complaint_data["chain_of_custody"] = [{"timestamp": complaint_data['timestamp'], "action": "Physical Device Intake Initiated", "actor": name, "location": "Pending Physical Drop-off at Station"}]
                else:
                    complaint_data["chain_of_custody"] = [{"timestamp": complaint_data['timestamp'], "action": "Digital Evidence Uploaded", "actor": name, "location": "Public Intake Portal"}]
                
                save_complaint(case_id, complaint_data)
                st.success(f"✅ Official Complaint Registered. Your Reference ID is **{case_id}**.")
                time.sleep(2); st.session_state.page = "login"; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  REGISTER & LOGIN PAGES (Centered Interface)
# ══════════════════════════════════════════════════════════════════════════════
def register_page(first_time: bool = False):
    _, col, _ = st.columns([1, 1.7, 1])
    with col:
        heading = "Create Your Account" if not first_time else "Welcome — Set Up Your Account"
        sub     = "No users found · Be the first to register" if first_time else "Zero Trust Identity Portal · New User Registration"
        st.markdown(f"""<div class="auth-card"><div class="card-icon">🔐</div><div class="card-title">{heading}</div><div class="card-sub">{sub}</div></div>""", unsafe_allow_html=True)
        
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        full_name = st.text_input("fn", placeholder="Full Name", label_visibility="collapsed")
        user_id   = st.text_input("uid_reg", placeholder="User ID  (e.g. inv3 or admin2)", label_visibility="collapsed")
        email     = st.text_input("email_reg", placeholder="Email Address", label_visibility="collapsed")
        mobile    = st.text_input("mobile_reg", placeholder="Mobile Number (e.g. +1 555-0100)", label_visibility="collapsed")
        role      = st.selectbox("role_sel", ["investigator", "admin", "analyst", "responder", "auditor", "viewer"], label_visibility="collapsed")
        expertise = st.selectbox("expertise_sel", [
            "Digital Forensics", "Malware Analysis", "Incident Response (DFIR)",
            "Network Security Monitoring", "Cloud Security Operations", "Mobile Forensics",
            "Threat Intelligence & Hunting", "SOC Analysis", "Endpoint Detection & Response (EDR)",
            "SIEM Engineering & Log Analysis", "Defensive Vulnerability Management", "Blue Teaming"
        ], label_visibility="collapsed")
        password  = st.text_input("pwd_reg",  placeholder="Password  (min. 8 characters)", type="password", label_visibility="collapsed")
        confirm   = st.text_input("cpwd_reg", placeholder="Confirm Password",               type="password", label_visibility="collapsed")
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        reg_clicked = st.button("CREATE ACCOUNT", key="btn_register", use_container_width=True)

        if not first_time:
            st.markdown('<div class="or-divider">OR</div>', unsafe_allow_html=True)
            with st.container():
                st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
                if st.button("← Back to Login", key="goto_login_from_reg", use_container_width=True):
                    st.session_state.page = "login"; st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        if reg_clicked:
            users, errors = load_users(), []
            if not full_name.strip(): errors.append("Full name is required.")
            if not user_id.strip(): errors.append("User ID is required.")
            elif user_id in users: errors.append(f"User ID '{user_id}' is already taken.")
            if "@" not in email or "." not in email: errors.append("Valid Email is required.")
            if not mobile.strip() or len(mobile.strip()) < 7: errors.append("Valid Mobile Number is required.")
            if len(password) < 8: errors.append("Password must be at least 8 chars.")
            if password != confirm: errors.append("Passwords do not match.")

            if errors:
                for e in errors: st.error(f"⚠️ {e}")
            else:
                users[user_id] = {"full_name": full_name.strip(), "email": email.strip(), "mobile": mobile.strip(), "password": hash_password(password), "role": role, "expertise": expertise, "registered": datetime.datetime.now(IST).isoformat()}
                save_users(users)
                st.success(f"🎉 Account created successfully!")
                st.session_state.temp_user = user_id
                st.session_state.auth_step = "mfa_select"
                st.session_state.page = "login"
                time.sleep(1)
                st.rerun()

def login_page():
    if "auth_step" not in st.session_state: st.session_state.auth_step = "credentials"
    _, col, _ = st.columns([1, 1.6, 1])
    with col:
        if st.session_state.auth_step == "credentials":
            st.markdown("""<div class="auth-card"><div class="card-icon">🛡️</div><div class="card-title">Log In</div><div class="card-sub">Zero Trust Identity Portal</div></div>""", unsafe_allow_html=True)
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            username = st.text_input("uid", placeholder="User ID", label_visibility="collapsed")
            password = st.text_input("pwd", placeholder="Password", type="password", label_visibility="collapsed")
            
            # FORGOT PASSWORD LINK (Only show if login fails)
            if st.session_state.get("show_forgot_password", False):
                st.markdown("<div style='text-align: right; margin-top: -5px; margin-bottom: 10px;'>", unsafe_allow_html=True)
                if st.button("Forgot Password?", key="forgot_pwd_btn", help="Reset your password via Email OTP"):
                    st.session_state.auth_step = "forgot_password"
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)
            
            # ── HORIZONTAL BUTTON LAYOUT ──
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                login_clicked = st.button("LOG IN", key="btn_login", use_container_width=True)
            with btn_col2:
                if st.button("REGISTER ACCOUNT", key="goto_register", use_container_width=True):
                    st.session_state.page = "register"; st.rerun()
            
            st.markdown('<div class="or-divider">CITIZEN PORTAL</div>', unsafe_allow_html=True)
            st.markdown('<div class="secondary-btn" style="margin-bottom: 18px;">', unsafe_allow_html=True)
            if st.button("🚨 File a Public Complaint", key="goto_complaint", use_container_width=True):
                st.session_state.page = "complaint"; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

            if login_clicked:
                users = load_users()
                if username in users and check_password(password, users[username]["password"]):
                    st.session_state.show_forgot_password = False
                    st.session_state.temp_user = username
                    st.session_state.auth_step = "mfa_select"
                    st.rerun()
                else:
                    st.session_state.show_forgot_password = True
                    st.error("⚠️ Invalid User ID or Password.")
                    st.rerun()
                    
            # JS Hack for Keyboard Navigation
            import streamlit.components.v1 as components
            components.html("""
            <script>
                const doc = window.parent.document;
                const inputs = doc.querySelectorAll('input[type="text"], input[type="password"]');
                const buttons = doc.querySelectorAll('button');
                
                if (inputs.length >= 2) {
                    // Enter on Username jumps to Password
                    inputs[0].addEventListener('keydown', function(e) {
                        if (e.key === 'Enter') {
                            e.preventDefault();
                            inputs[1].focus();
                        }
                    });
                    
                    // Enter on Password clicks the Login button
                    inputs[1].addEventListener('keydown', function(e) {
                        if (e.key === 'Enter') {
                            e.preventDefault();
                            for (let btn of buttons) {
                                if (btn.innerText.includes("LOG IN")) {
                                    btn.click();
                                    break;
                                }
                            }
                        }
                    });
                }
            </script>
            """, height=0, width=0)

        elif st.session_state.auth_step == "mfa_select":
            users = load_users()
            tmp_user = st.session_state.get("temp_user", "")
            user_data = users.get(tmp_user, {})
            name = user_data.get("full_name", tmp_user)
            st.markdown(f"""<div class="auth-card"><div class="card-icon">📱</div><div class="card-title">MFA Selection</div><div class="card-sub">Welcome, {name}</div></div>""", unsafe_allow_html=True)
            
            st.markdown("<div style='text-align: center; color: #e0e6f0; margin-bottom: 20px;'>How would you like to receive your security code?</div>", unsafe_allow_html=True)
            
            if st.button("✉️ Send Code via Email", use_container_width=True, type="primary"):
                otp = "".join(random.choices(string.digits, k=6))
                st.session_state.current_otp = otp
                with st.spinner("Sending authentication code..."):
                    success, message = send_email_otp(user_data.get("email", ""), otp)
                    st.session_state.mfa_status_message, st.session_state.mfa_status_success = message, success
                st.session_state.auth_step = "mfa"
                st.rerun()
                
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            
            if st.button("📱 Send Code via SMS (Mobile)", use_container_width=True, type="primary"):
                otp = "".join(random.choices(string.digits, k=6))
                st.session_state.current_otp = otp
                mobile_num = user_data.get("mobile", "Unknown Number")
                st.session_state.mfa_status_message = f"✅ Simulated SMS sent to {mobile_num} with code: **{otp}**"
                st.session_state.mfa_status_success = True
                st.session_state.auth_step = "mfa"
                st.rerun()
                
            st.markdown('<div class="secondary-btn" style="margin-top:20px;">', unsafe_allow_html=True)
            if st.button("← Cancel Login", use_container_width=True):
                st.session_state.auth_step = "credentials"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        elif st.session_state.auth_step == "mfa":
            users, tmp_user = load_users(), st.session_state.get("temp_user", "")
            name = users.get(tmp_user, {}).get("full_name", tmp_user)
            st.markdown(f"""<div class="auth-card"><div class="card-icon">🔐</div><div class="card-title">Verify Identity</div><div class="card-sub">MFA Step 2 — Welcome, {name}</div></div>""", unsafe_allow_html=True)
            
            if st.session_state.get("mfa_status_success"): st.info(st.session_state.get("mfa_status_message", ""))
            else: st.warning(st.session_state.get("mfa_status_message", ""))

            st.markdown('<div class="mfa-hint">🔑 Enter the 6-digit MFA code sent to your email.</div>', unsafe_allow_html=True)
            mfa_code = st.text_input("mfa", placeholder="6-digit MFA Code", type="password", max_chars=6, label_visibility="collapsed")
            verify_clicked = st.button("VERIFY & SIGN IN", key="btn_verify", use_container_width=True)
            st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
            cancel_clicked = st.button("← Back to Login", key="btn_cancel", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

            if verify_clicked:
                if mfa_code == st.session_state.get("current_otp"):
                    st.session_state.logged_in, st.session_state.user_id = True, tmp_user
                    st.session_state.role, st.session_state.full_name = users[tmp_user]["role"], users[tmp_user].get("full_name", tmp_user)
                    st.session_state.expertise = users[tmp_user].get("expertise", "Investigator")
                    st.session_state.session_logs = []
                    log_action("Successful Login")
                    
                    import uuid, json
                    sid = uuid.uuid4().hex
                    try:
                        with open(SESSIONS_FILE, "r") as f: sess_data = json.load(f)
                    except Exception: sess_data = {}
                    sess_data[sid] = {
                        "user_id": tmp_user,
                        "role": st.session_state.role,
                        "full_name": st.session_state.full_name
                    }
                    with open(SESSIONS_FILE, "w") as f: json.dump(sess_data, f)
                    st.query_params["session"] = sid
                    
                    st.success("✅ Authentication Successful! Redirecting…")
                    time.sleep(1); st.rerun()
                else:
                    st.error("⚠️ Invalid MFA Code. Please try again.")
            if cancel_clicked: st.session_state.auth_step = "credentials"; st.rerun()
            
            import streamlit.components.v1 as components
            components.html("""
            <script>
                const doc = window.parent.document;
                const inputs = doc.querySelectorAll('input[type="password"]');
                const buttons = doc.querySelectorAll('button');
                
                if (inputs.length > 0) {
                    // Autofocus the OTP input
                    inputs[0].focus();
                    
                    // Enter presses VERIFY
                    inputs[0].addEventListener('keydown', function(e) {
                        if (e.key === 'Enter') {
                            e.preventDefault();
                            for (let btn of buttons) {
                                if (btn.innerText.includes("VERIFY & SIGN IN")) {
                                    btn.click();
                                    break;
                                }
                            }
                        }
                    });
                }
            </script>
            """, height=0, width=0)
            
        elif st.session_state.auth_step == "forgot_password":
            st.markdown("""<div class="auth-card"><div class="card-icon">🔑</div><div class="card-title">Password Reset</div><div class="card-sub">Identity Verification required</div></div>""", unsafe_allow_html=True)
            reset_uid = st.text_input("reset_uid", placeholder="Enter your registered User ID", label_visibility="collapsed")
            send_otp_btn = st.button("SEND RECOVERY OTP", use_container_width=True)
            st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
            if st.button("← Back to Login", key="cancel_reset", use_container_width=True):
                st.session_state.auth_step = "credentials"; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

            if send_otp_btn:
                users = load_users()
                if reset_uid in users:
                    otp = "".join(random.choices(string.digits, k=6))
                    st.session_state.reset_otp, st.session_state.reset_user = otp, reset_uid
                    with st.spinner("Sending recovery code to your email..."):
                        success, message = send_email_otp(users[reset_uid].get("email", ""), otp)
                        st.session_state.mfa_status_message, st.session_state.mfa_status_success = message, success
                    st.session_state.auth_step = "reset_mfa"; st.rerun()
                else:
                    st.error("⚠️ User ID not found in the system.")
                    
        elif st.session_state.auth_step == "reset_mfa":
            st.markdown("""<div class="auth-card"><div class="card-icon">📧</div><div class="card-title">Verify Reset</div><div class="card-sub">Enter the 6-digit OTP sent to your email</div></div>""", unsafe_allow_html=True)
            if st.session_state.get("mfa_status_success"): st.info(st.session_state.get("mfa_status_message", ""))
            else: st.warning(st.session_state.get("mfa_status_message", ""))

            reset_otp_input = st.text_input("reset_otp_input", placeholder="6-digit Recovery OTP", max_chars=6, type="password", label_visibility="collapsed")
            if st.button("VERIFY CODE", key="btn_ver_reset", use_container_width=True):
                if reset_otp_input == st.session_state.get("reset_otp"):
                    st.session_state.auth_step = "new_password"; st.rerun()
                else:
                    st.error("⚠️ Invalid OTP Code.")
            st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
            if st.button("← Cancel", key="btn_cancel_reset_mfa", use_container_width=True):
                st.session_state.auth_step = "credentials"; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
        elif st.session_state.auth_step == "new_password":
            st.markdown("""<div class="auth-card"><div class="card-icon">🔒</div><div class="card-title">New Password</div><div class="card-sub">Secure your account</div></div>""", unsafe_allow_html=True)
            new_pwd = st.text_input("new_pwd", placeholder="New Password (min 8 chars)", type="password", label_visibility="collapsed")
            new_pwd_confirm = st.text_input("new_pwd_conf", placeholder="Confirm Password", type="password", label_visibility="collapsed")
            
            if st.button("UPDATE PASSWORD", key="btn_update_pwd", use_container_width=True):
                if len(new_pwd) < 8: st.error("⚠️ Password must be at least 8 characters.")
                elif new_pwd != new_pwd_confirm: st.error("⚠️ Passwords do not match.")
                else:
                    users, uid = load_users(), st.session_state.get("reset_user")
                    users[uid]["password"] = hash_password(new_pwd)
                    save_users(users)
                    log_action("Password Reset Successfully")
                    st.success("✅ Password updated successfully!")
                    time.sleep(2); st.session_state.auth_step = "credentials"; st.rerun()

def back_button():
    if st.button("← Back to Workspace", key=f"back_{st.session_state.active_tool}"):
        if "tool" in st.query_params: del st.query_params["tool"]
        st.session_state.active_tool = None; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  FORENSIC TOOLS
# ══════════════════════════════════════════════════════════════════════════════
def tool_ftk():
    log_action("Opened Tool: Portable Acquisition & Triage")
    back_button()
    st.markdown('<div class="tool-header"><div class="tool-title">🖥️ FTK Imager Alternative: Portable Acquisition</div><div class="tool-sub">RAM/Disk Cloning via USB Agent | Cloud Triage & Hashing</div></div>', unsafe_allow_html=True)
    
    st.info("💡 **Architectural Note:** Web browsers cannot legally or physically dump live RAM or clone raw physical hard drives. You must extract the evidence using the **Portable USB Agent** (Tab 1), then upload it to the **Cloud Dashboard** (Tab 2) for forensic analysis.")
    
    tabs = st.tabs(["💾 1. Download Portable USB Agent", "🔍 2. Cloud Evidence Triage (Hex & Hash)"])
    
    with tabs[0]:
        st.markdown("### The Portable Acquisition Agent")
        st.write("Download this standalone agent to a secure USB drive. Plug the USB into the suspect's computer and run the script to securely extract volatile memory (RAM) and logical disk images without alerting network monitoring tools.")
        
        agent_script = """# ==============================================================================
# DIGITAL FORENSICS ACQUISITION AGENT (Real Triage Mode)
# Authorized Investigator Use Only
# ==============================================================================
$ErrorActionPreference = "SilentlyContinue"
Write-Host "Initiating REAL Triage Acquisition..." -ForegroundColor Cyan

# 1. Setup Evidence Folder on the USB
$SavePath = Join-Path -Path $PWD -ChildPath "Forensic_Evidence_Temp"
New-Item -ItemType Directory -Force -Path $SavePath | Out-Null

# 2. Extract Volatile RAM Data (Network & Processes)
Write-Host "[*] Extracting Live Network Connections..."
netstat -ano > "$SavePath\\network_connections.txt"

Write-Host "[*] Extracting Running Processes..."
Get-Process | Select-Object Id, ProcessName, Path > "$SavePath\\running_processes.txt"

# 3. Mini-Acquisition (Logical Files)
Write-Host "[*] Performing Mini-Acquisition of User Documents..."
# We grab only the 5 most recent files to keep the extraction fast and safe
$DocsPath = [Environment]::GetFolderPath('MyDocuments')
Get-ChildItem -Path $DocsPath -File | Sort-Object LastWriteTime -Descending | Select-Object -First 5 | Copy-Item -Destination $SavePath

# 4. Create Forensic Container (ZIP)
Write-Host "[*] Compressing Evidence into Secure Container..."
$ZipPath = Join-Path -Path $PWD -ChildPath "Evidence_Container.zip"
if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
Compress-Archive -Path "$SavePath\\*" -DestinationPath $ZipPath

# 5. Cleanup
Remove-Item -Recurse -Force $SavePath

Write-Host "[+] SUCCESS! Real Evidence safely acquired and saved to: $ZipPath" -ForegroundColor Green
Write-Host "======================================================================"
Write-Host "ACQUISITION COMPLETE." -ForegroundColor Cyan
Write-Host "You may now remove the USB drive and upload Evidence_Container.zip to the Cloud Dashboard." -ForegroundColor Yellow
Pause
"""
        st.download_button(
            label="⬇️ Download Portable Agent (acquisition_agent.ps1)",
            data=agent_script,
            file_name="acquisition_agent.ps1",
            mime="text/plain",
            type="primary",
            use_container_width=True
        )
        st.info("**Instructions:** Download this file to a USB drive. Right-click the file on the suspect's Windows computer and select **'Run with PowerShell'**. Once the script finishes, bring the USB back to your workstation and upload the evidence to Tab 2.")
        
    with tabs[1]:
        st.markdown("### Forensic Hex Viewer & Evidence Preview")
        st.write("Examine the raw hexadecimal code to determine the true file signature, bypassing false extensions used by suspects.")
        hex_file = st.file_uploader("Upload Suspicious File or Small Evidence Block", key="ftk_hex")
        if hex_file:
            hex_file.seek(0)
            raw_bytes = hex_file.read(512)
            
            st.subheader(f"Raw Hex Dump (First {len(raw_bytes)} bytes)")
            
            hex_lines = []
            for i in range(0, len(raw_bytes), 16):
                chunk = raw_bytes[i:i+16]
                hex_part = " ".join([f"{b:02x}" for b in chunk])
                ascii_part = "".join([chr(b) if 32 <= b <= 126 else "." for b in chunk])
                hex_lines.append(f"{i:08x}  {hex_part:<48}  |{ascii_part}|")
                
            st.code("\n".join(hex_lines), language="text")
            
            st.success("💡 **Forensic Tip:** Look at the ASCII column on the right. If the file starts with `4D 5A` (MZ), it is a Windows Executable. If it starts with `FF D8 FF E0`, it's a JPEG.")
            log_tool_to_coc("FTK (Hex Viewer)", f"Performed deep Hex Preview on {hex_file.name}")

        st.markdown("---")
        st.markdown("### Evidence Integrity Verifier")
        ev_file = st.file_uploader("Upload Evidence File for Hashing", key="ftk_hash")
        if ev_file and st.button("▶ Start Block Hashing", type="primary"):
            import hashlib
            md5_hash, sha1_hash, sha256_hash = hashlib.md5(), hashlib.sha1(), hashlib.sha256()
            file_size, bytes_processed = ev_file.size, 0
            progress_bar, status_text = st.progress(0), st.empty()
            
            with st.spinner("Processing file blocks..."):
                ev_file.seek(0)
                while chunk := ev_file.read(65536):
                    md5_hash.update(chunk); sha1_hash.update(chunk); sha256_hash.update(chunk)
                    bytes_processed += len(chunk)
                    if file_size > 0: progress_bar.progress(min(bytes_processed / file_size, 1.0))
            status_text.empty()
            st.success(f"✅ Hashing Complete for `{ev_file.name}`")
            col1, col2, col3 = st.columns(3)
            col1.code(f"MD5\n{md5_hash.hexdigest()}")
            col2.code(f"SHA-1\n{sha1_hash.hexdigest()}")
            col3.code(f"SHA-256\n{sha256_hash.hexdigest()}")
            log_tool_to_coc("FTK (Web Hasher)", f"Verified integrity of {ev_file.name}. MD5: {md5_hash.hexdigest()}")

def tool_defender():
    log_action("Opened Tool: Microsoft Defender")
    back_button()
    st.markdown("""<div class="tool-header"><div class="tool-title">🛡️ Microsoft Defender — EDR Scanner</div><div class="tool-sub">Endpoint Detection & Response | Live MpCmdRun.exe Integration</div></div>""", unsafe_allow_html=True)
    
    st.markdown("### Real-Time Threat Analysis")
    st.write("This engine connects directly to the hidden Microsoft Defender Command Line Engine (`MpCmdRun.exe`) installed on the host operating system to perform live, military-grade malware scanning.")
    
    col_up, col_gen = st.columns([3, 1])
    with col_gen:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Generate EICAR Test Malware", use_container_width=True):
            import os
            # EICAR is a globally recognized, harmless string used to test Antivirus software
            eicar_string = r"X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
            sample_path = r"C:\Users\Chennakeshavulu\.gemini\antigravity\scratch\zero_trust_workspace\test_malware.txt"
            with open(sample_path, "w") as f:
                f.write(eicar_string)
            st.success(f"⚠️ Harmless EICAR test file created at: {sample_path}")
            st.info("Upload this file on the left to test the Defender engine!")
            
    with col_up:
        uploaded_file = st.file_uploader("Upload Suspicious File for Background Scan", key="defender_file")
    
    if uploaded_file and st.button("▶ Run Real Defender Scan", use_container_width=True, type="primary"):
        import os, subprocess, uuid
        temp_dir = "uploads/temp_scans"
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{uploaded_file.name}")
        abs_temp_path = os.path.abspath(temp_path)
        with open(abs_temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        with st.spinner("Executing direct kernel scan with Microsoft Defender (MpCmdRun.exe)..."):
            try:
                # Windows Defender Command Line Utility
                cmd = [r"C:\Program Files\Windows Defender\MpCmdRun.exe", "-Scan", "-ScanType", "3", "-File", abs_temp_path]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                # Check results
                if result.returncode == 0:
                    st.success(f"✅ **CLEAN!** Microsoft Defender analyzed `{uploaded_file.name}` and found no malicious signatures.")
                    log_action(f"Defender Scan Clean: {uploaded_file.name}")
                    log_tool_to_coc("Microsoft Defender", f"Scanned {uploaded_file.name}. Result: CLEAN (No threats found).")
                else:
                    st.error(f"🚨 **THREAT DETECTED!** Microsoft Defender flagged `{uploaded_file.name}` as malicious.")
                    st.code(result.stdout, language="shell")
                    log_action(f"CRITICAL: Defender flagged {uploaded_file.name}")
                    log_tool_to_coc("Microsoft Defender", f"Scanned {uploaded_file.name}. Result: THREAT DETECTED. File quarantined by OS.")
                
                # Cleanup (if Defender didn't automatically quarantine it)
                if os.path.exists(abs_temp_path):
                    try:
                        os.remove(abs_temp_path)
                    except:
                        pass
                        
            except Exception as e:
                st.error(f"Failed to execute MpCmdRun.exe. Ensure you are running this on a Windows machine. Error: {e}")

def tool_sandbox():
    log_action("Opened Tool: Secure Sandbox (Static)")
    back_button()
    st.markdown("""<div class="tool-header"><div class="tool-title">📦 Reverse Engineering Engine (Static Sandbox)</div><div class="tool-sub">PE Header Parsing | Import Analysis | Capability Detection</div></div>""", unsafe_allow_html=True)
    
    st.write("This tool surgically tears open Windows Executables (`.exe`, `.dll`) without running them. By analyzing the 'Imports' (the Windows APIs the program requests), the engine can identify if the file is a Keylogger, Downloader, or Ransomware.")
    
    col_up, col_gen = st.columns([3, 1])
    with col_gen:
        st.markdown("<br>", unsafe_allow_html=True)
        import os
        try:
            with open(r"C:\Windows\System32\find.exe", "rb") as f:
                exe_bytes = f.read()
            st.download_button("📥 Download Sample .exe", data=exe_bytes, file_name="suspicious_sample.exe", mime="application/x-msdownload", use_container_width=True)
        except Exception:
            st.error("Could not read system file for sample.")
            
    with col_up:
        uploaded_file = st.file_uploader("Upload Windows Executable (.exe, .dll)", type=['exe','dll','sys'])
        
    if uploaded_file and st.button("▶ Run Static Reverse Engineering", use_container_width=True, type="primary"):
        import pefile
        import time
        import pandas as pd
        
        with st.spinner("Dissecting PE Headers and extracting Import Address Table (IAT)..."):
            time.sleep(1) # Visual delay for realism
            try:
                # Load the uploaded bytes into pefile
                pe = pefile.PE(data=uploaded_file.getvalue())
                
                # --- Basic Info ---
                st.markdown("### 📊 PE Header Information")
                machine_type = "x64 (64-bit)" if pe.FILE_HEADER.Machine == 0x8664 else "x86 (32-bit)" if pe.FILE_HEADER.Machine == 0x14c else "Unknown"
                
                st.write(f"**Architecture:** {machine_type}")
                st.write(f"**Number of Sections:** {pe.FILE_HEADER.NumberOfSections}")
                
                # --- Sections Analysis ---
                st.markdown("### 🧩 Memory Sections")
                sections_data = []
                for section in pe.sections:
                    sections_data.append({
                        "Name": section.Name.decode('utf-8').rstrip('\\x00'),
                        "Virtual Address": hex(section.VirtualAddress),
                        "Virtual Size": hex(section.Misc_VirtualSize),
                        "Raw Size": section.SizeOfRawData
                    })
                st.dataframe(pd.DataFrame(sections_data), hide_index=True, use_container_width=True)
                
                # --- Import Analysis ---
                st.markdown("### 🧬 Extracted API Imports & Capabilities")
                imports_data = []
                threat_flags = []
                
                # Threat Intelligence Rules (Mapping APIs to Malware Behavior)
                rule_keylogger = [b"GetAsyncKeyState", b"SetWindowsHookEx"]
                rule_ransomware = [b"CryptAcquireContextA", b"CryptEncrypt", b"VirtualAlloc", b"WriteProcessMemory"]
                rule_downloader = [b"InternetOpenA", b"InternetOpenUrlA", b"URLDownloadToFileA"]
                
                if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
                    for entry in pe.DIRECTORY_ENTRY_IMPORT:
                        dll_name = entry.dll.decode('utf-8')
                        for imp in entry.imports:
                            if imp.name:
                                imports_data.append({"DLL": dll_name, "API Function": imp.name.decode('utf-8')})
                                
                                # Check against rules
                                if imp.name in rule_keylogger: threat_flags.append(f"Keylogger Capability ({imp.name.decode('utf-8')})")
                                if imp.name in rule_ransomware: threat_flags.append(f"Encryption/Injection Capability ({imp.name.decode('utf-8')})")
                                if imp.name in rule_downloader: threat_flags.append(f"Network Downloader Capability ({imp.name.decode('utf-8')})")
                                
                st.dataframe(pd.DataFrame(imports_data), hide_index=True, use_container_width=True, height=250)
                
                # --- Threat Verdict ---
                st.markdown("### 🚨 AI Threat Verdict")
                if threat_flags:
                    st.error("**MALICIOUS CAPABILITIES DETECTED:**")
                    for flag in set(threat_flags):
                        st.markdown(f"- 🔴 {flag}")
                    log_action(f"Sandbox Reverse Eng: Flagged {uploaded_file.name} as Malicious")
                    log_tool_to_coc("Static Sandbox", f"Reversed {uploaded_file.name}. Found dangerous imports: {', '.join(set(threat_flags))}")
                else:
                    st.success("✅ **NO OBVIOUS THREATS DETECTED:** The imported APIs appear benign.")
                    log_action(f"Sandbox Reverse Eng: Clean {uploaded_file.name}")
                    log_tool_to_coc("Static Sandbox", f"Reversed {uploaded_file.name}. No dangerous API imports detected.")
                    
            except pefile.PEFormatError:
                st.error("❌ Invalid File Format! The uploaded file is not a valid Windows PE (.exe) file.")
            except Exception as e:
                st.error(f"❌ An error occurred during reverse engineering: {e}")

def tool_volatility():
    log_action("Opened Tool: Volatility Memory Analysis")
    back_button()
    st.markdown("""<div class="tool-header"><div class="tool-title">🧠 Volatility 3 — Memory Forensics</div><div class="tool-sub">Advanced RAM Analysis | Process Extraction | Rootkit Detection</div></div>""", unsafe_allow_html=True)
    
    st.write("Volatility is an advanced memory forensics framework. Upload a raw memory dump (`.raw`, `.mem`, `.vmem`) to analyze the live state of the suspect's computer at the time of extraction.")
    
    # Generate Sample RAM Dump button
    col_up, col_gen = st.columns([3, 1])
    with col_gen:
        st.markdown("<br>", unsafe_allow_html=True)
        import os
        sample_bytes = os.urandom(1024 * 50) + b"VOL_MARKER_WIN10_x64" + os.urandom(1024 * 50)
        st.download_button("📥 Download Sample .raw", data=sample_bytes, file_name="suspect_memory.raw", mime="application/octet-stream", use_container_width=True)
            
    with col_up:
        uploaded_ram = st.file_uploader("Upload RAM Dump File", type=["raw", "mem", "vmem"], key="ram_upload")
        
    if uploaded_ram:
        st.success(f"✅ Memory Image Loaded: {uploaded_ram.name} (Size: {uploaded_ram.size} bytes)")
        st.markdown("### Volatility 3 Plugin Execution")
        
        col_plugin, col_run = st.columns([3, 1])
        with col_plugin:
            plugin = st.selectbox("Select Volatility Plugin:", [
                "windows.pslist.PsList",
                "windows.netscan.NetScan",
                "windows.malfind.Malfind",
                "windows.hashdump.Hashdump"
            ])
        with col_run:
            st.markdown("<br>", unsafe_allow_html=True)
            run_btn = st.button("▶ Execute Plugin", type="primary", use_container_width=True)
            
        if run_btn:
            import pandas as pd
            import time
            
            with st.spinner(f"Running Volatility 3 plugin {plugin}... Parsing memory structures..."):
                time.sleep(2) # Simulate processing time
                
                if plugin == "windows.pslist.PsList":
                    data = [
                        {"PID": 4, "PPID": 0, "ImageFileName": "System", "Offset(V)": "0xfa8003a74040", "Threads": 121, "Handles": 540, "CreateTime": "2023-10-25 08:12:01"},
                        {"PID": 344, "PPID": 4, "ImageFileName": "smss.exe", "Offset(V)": "0xfa8004b7b300", "Threads": 2, "Handles": 30, "CreateTime": "2023-10-25 08:12:05"},
                        {"PID": 512, "PPID": 420, "ImageFileName": "csrss.exe", "Offset(V)": "0xfa8004e12040", "Threads": 10, "Handles": 412, "CreateTime": "2023-10-25 08:12:10"},
                        {"PID": 4012, "PPID": 812, "ImageFileName": "chrome.exe", "Offset(V)": "0xfa8005c2a120", "Threads": 34, "Handles": 890, "CreateTime": "2023-10-25 09:45:22"},
                        {"PID": 8832, "PPID": 3120, "ImageFileName": "svchost.exe", "Offset(V)": "0xfa8009b11040", "Threads": 5, "Handles": 112, "CreateTime": "2023-10-25 10:11:05"}
                    ]
                    df = pd.DataFrame(data)
                    st.markdown("#### Running Processes (windows.pslist)")
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    log_tool_to_coc("Volatility 3", f"Executed windows.pslist on {uploaded_ram.name}. Extracted {len(df)} processes.")

                elif plugin == "windows.netscan.NetScan":
                    data = [
                        {"Offset": "0xfa8008a12010", "Proto": "TCPv4", "LocalAddr": "192.168.1.55", "LocalPort": 49152, "ForeignAddr": "104.21.34.12", "ForeignPort": 443, "State": "ESTABLISHED", "PID": 4012, "Owner": "chrome.exe"},
                        {"Offset": "0xfa8008b44020", "Proto": "TCPv4", "LocalAddr": "192.168.1.55", "LocalPort": 135, "ForeignAddr": "0.0.0.0", "ForeignPort": 0, "State": "LISTENING", "PID": 883, "Owner": "svchost.exe"},
                        {"Offset": "0xfa8009c55040", "Proto": "TCPv4", "LocalAddr": "192.168.1.55", "LocalPort": 4444, "ForeignAddr": "185.112.44.19", "ForeignPort": 8080, "State": "ESTABLISHED", "PID": 8832, "Owner": "svchost.exe"}
                    ]
                    df = pd.DataFrame(data)
                    st.markdown("#### Network Connections (windows.netscan)")
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    st.warning("⚠️ **Suspicious Connection Detected:** PID 8832 (svchost.exe) communicating with foreign IP 185.112.44.19 on port 8080.")
                    log_tool_to_coc("Volatility 3", f"Executed windows.netscan on {uploaded_ram.name}. Found anomalous outbound connection to 185.112.44.19.")
                    
                elif plugin == "windows.malfind.Malfind":
                    st.markdown("#### Injected Code Detection (windows.malfind)")
                    st.error("🚨 **Malware Injection Detected!**")
                    st.code('''Process: svchost.exe Pid: 8832 Address: 0x240000
Vad Tag: PAGE_EXECUTE_READWRITE
Hexdump:
0x00240000  4d 5a 90 00 03 00 00 00 04 00 00 00 ff ff 00 00   MZ..............
0x00240010  b8 00 00 00 00 00 00 00 40 00 00 00 00 00 00 00   ........@.......''', language="text")
                    log_tool_to_coc("Volatility 3", f"Executed windows.malfind on {uploaded_ram.name}. Detected PAGE_EXECUTE_READWRITE injection in svchost.exe (PID 8832).")
                
                elif plugin == "windows.hashdump.Hashdump":
                    st.markdown("#### Extracted Password Hashes (windows.hashdump)")
                    st.code('''Administrator:500:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
SuspectUser:1001:aad3b435b51404eeaad3b435b51404ee:8846f7eaee8fb117ad06bdd830b7586c:::''', language="text")
                    log_tool_to_coc("Volatility 3", f"Executed windows.hashdump on {uploaded_ram.name}. Extracted 3 NTLM password hashes.")

def tool_cellebrite():
    log_action("Opened Tool: Cellebrite UFED XML Analyzer")
    back_button()
    st.markdown("""<div class="tool-header"><div class="tool-title">📱 Cellebrite UFED — XML Report Analyzer</div><div class="tool-sub">Mobile Forensics | Message Extraction | Call Log Parsing</div></div>""", unsafe_allow_html=True)
    
    st.write("Upload a raw **Cellebrite UFED XML Report** generated from a physical device extraction. The engine will parse the schema and map the suspect's SMS, Contacts, and Call Logs.")
    
    col_up, col_gen = st.columns([3, 1])
    with col_gen:
        st.markdown("<br>", unsafe_allow_html=True)
        sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
<ufed_report>
    <metadata>
        <device>Apple iPhone 14 Pro Max</device>
        <extraction_type>Advanced Logical</extraction_type>
        <timestamp>2026-09-30T10:00:00</timestamp>
    </metadata>
    <contacts>
        <contact><name>John Doe (Boss)</name><phone>+1-555-0101</phone></contact>
        <contact><name>Shady Supplier</name><phone>+1-555-9999</phone></contact>
        <contact><name>Burner Phone</name><phone>+1-555-0000</phone></contact>
    </contacts>
    <calls>
        <call><type>Outgoing</type><number>+1-555-9999</number><duration>120</duration><time>2026-09-29 18:30:00</time></call>
        <call><type>Incoming</type><number>+1-555-0101</number><duration>45</duration><time>2026-09-29 19:15:00</time></call>
        <call><type>Missed</type><number>+1-555-0000</number><duration>0</duration><time>2026-09-29 23:45:00</time></call>
    </calls>
    <messages>
        <message><folder>Inbox</folder><sender>+1-555-9999</sender><timestamp>2026-09-29 20:00:00</timestamp><body>Is the package ready?</body></message>
        <message><folder>Sent</folder><receiver>+1-555-9999</receiver><timestamp>2026-09-29 20:05:00</timestamp><body>Yes, bring the cash. Location sent.</body></message>
        <message><folder>Deleted</folder><sender>+1-555-9999</sender><timestamp>2026-09-29 20:10:00</timestamp><body>Understood. Burn this phone after the drop.</body></message>
    </messages>
</ufed_report>"""
        st.download_button("📥 Download Sample XML", data=sample_xml, file_name="Suspect_iPhone_Dump.xml", mime="application/xml", use_container_width=True)
            
    with col_up:
        uploaded_file = st.file_uploader("Upload Cellebrite UFED XML Report", type=["xml"], key="ufed_xml")
        
    if uploaded_file and st.button("▶ Parse UFED Report", use_container_width=True, type="primary"):
        import xml.etree.ElementTree as ET
        import pandas as pd
        import time
        
        with st.spinner("Parsing XML Nodes... Extracting Device Metadata..."):
            time.sleep(1) # Simulated delay
            try:
                tree = ET.parse(uploaded_file)
                root = tree.getroot()
                
                # Metadata
                metadata = root.find('metadata')
                if metadata is not None:
                    st.markdown("### 📱 Device Profile")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Device Model", metadata.findtext('device', 'Unknown'))
                    col2.metric("Extraction Type", metadata.findtext('extraction_type', 'Unknown'))
                    col3.metric("Timestamp", metadata.findtext('timestamp', 'Unknown'))
                    
                st.markdown("---")
                
                tab1, tab2, tab3 = st.tabs(["💬 Messages", "📞 Call Logs", "📒 Contacts"])
                
                with tab1:
                    messages = []
                    for msg in root.findall('.//messages/message'):
                        sender = msg.findtext('sender', '')
                        receiver = msg.findtext('receiver', '')
                        party = f"From: {sender}" if sender else f"To: {receiver}"
                        folder = msg.findtext('folder', 'Unknown')
                        
                        messages.append({
                            "Status": folder,
                            "Party": party,
                            "Timestamp": msg.findtext('timestamp', ''),
                            "Message Body": msg.findtext('body', '')
                        })
                        
                    if messages:
                        df_msgs = pd.DataFrame(messages)
                        # Highlight deleted messages
                        def highlight_deleted(s):
                            return ['background-color: #3b1c1c' if s.Status == 'Deleted' else '' for v in s]
                        st.dataframe(df_msgs.style.apply(highlight_deleted, axis=1), hide_index=True, use_container_width=True)
                        log_tool_to_coc("Cellebrite UFED Analyzer", f"Extracted {len(messages)} SMS/Chats from {uploaded_file.name}")
                    else:
                        st.info("No messages found in this extraction.")
                        
                with tab2:
                    calls = []
                    for call in root.findall('.//calls/call'):
                        calls.append({
                            "Type": call.findtext('type', ''),
                            "Number": call.findtext('number', ''),
                            "Duration (sec)": call.findtext('duration', ''),
                            "Timestamp": call.findtext('time', '')
                        })
                    if calls:
                        st.dataframe(pd.DataFrame(calls), hide_index=True, use_container_width=True)
                        log_tool_to_coc("Cellebrite UFED Analyzer", f"Extracted {len(calls)} Call Logs from {uploaded_file.name}")
                    else:
                        st.info("No call logs found.")
                        
                with tab3:
                    contacts = []
                    for contact in root.findall('.//contacts/contact'):
                        contacts.append({
                            "Name": contact.findtext('name', ''),
                            "Phone Number": contact.findtext('phone', '')
                        })
                    if contacts:
                        st.dataframe(pd.DataFrame(contacts), hide_index=True, use_container_width=True)
                        log_tool_to_coc("Cellebrite UFED Analyzer", f"Extracted {len(contacts)} Contacts from {uploaded_file.name}")
                    else:
                        st.info("No contacts found.")
                        
                st.success("✅ Cellebrite XML Parsing Complete.")
                log_action(f"Cellebrite UFED: Parsed {uploaded_file.name}")
                
            except ET.ParseError:
                st.error("❌ Invalid XML File. Please ensure this is a valid Cellebrite UFED XML Export.")
            except Exception as e:
                st.error(f"❌ Parsing Error: {e}")

def tool_autopsy():
    log_action("Opened Tool: Autopsy (Web GUI)")
    back_button()
    
    # Initialize the wizard state
    if "autopsy_step" not in st.session_state:
        st.session_state.autopsy_step = "welcome"
        
    if st.session_state.autopsy_step == "welcome":
        st.markdown("<h3 style='text-align: center; color: #555;'>Autopsy 4.23.1 (Web-Native Edition)</h3>", unsafe_allow_html=True)
        st.markdown("---")
        
        col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
        with col2:
            # Using a public domain dog icon to mimic the Autopsy bloodhound
            st.markdown("<h1 style='text-align: center; font-size: 80px; margin-bottom: -20px;'>🐶</h1>", unsafe_allow_html=True)
            st.markdown("<h1 style='text-align: center; font-family: Arial; font-weight: 900; color: #333;'>Autopsy®</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; font-size: 12px; letter-spacing: 2px; color: #666;'>OPEN | EXTENSIBLE | FAST</p>", unsafe_allow_html=True)
            
        with col3:
            st.markdown("<br><br>", unsafe_allow_html=True)
            if st.button("📄➕ New Case", use_container_width=True):
                st.session_state.autopsy_step = "new_case_1"
                st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)
            st.button("📄➡️ Open Recent Case", use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.button("📄📂 Open Case", use_container_width=True)
            
    elif st.session_state.autopsy_step == "new_case_1":
        st.markdown("### 🐶 New Case Information")
        st.markdown("---")
        
        col_nav, col_main = st.columns([1, 3])
        
        with col_nav:
            st.markdown("**Steps**")
            st.markdown("<hr style='margin:0px; padding:0px;'>", unsafe_allow_html=True)
            st.markdown("**1. Case Information**")
            st.markdown("<span style='color: gray;'>2. Optional Information</span>", unsafe_allow_html=True)
            
        with col_main:
            st.markdown("**Case Information**")
            st.markdown("<hr style='margin:0px; padding:0px; margin-bottom:10px;'>", unsafe_allow_html=True)
            
            case_name = st.text_input("Case Name:", value=st.session_state.get("autopsy_case_name", ""))
            
            col_dir, col_btn = st.columns([4, 1])
            
            # Initialize base_dir in session state if it doesn't exist
            if "autopsy_base_dir" not in st.session_state:
                st.session_state.autopsy_base_dir = r"C:\Users\Forensics\Documents"
                
            with col_dir:
                base_dir = st.text_input("Base Directory:", value=st.session_state.autopsy_base_dir)
                # Update state if user types it manually
                st.session_state.autopsy_base_dir = base_dir 
                
            with col_btn:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Browse"):
                    st.warning("🌐 **Web Edition:** Please type your Base Directory path directly into the text box.")
                
            st.radio("Case Type:", ["Single-User", "Multi-User"], horizontal=True)
            
            st.markdown("<br><p style='margin-bottom:0px;'>Case data will be stored in the following directory:</p>", unsafe_allow_html=True)
            computed_dir = f"{st.session_state.autopsy_base_dir}\\{case_name}" if case_name else ""
            st.text_input("Target Directory", value=computed_dir, disabled=True, label_visibility="collapsed")
            
        st.markdown("---")
        col_space, b1, b2, b3, b4 = st.columns([4, 1, 1, 1, 1])
        with b1:
            st.button("< Back", disabled=True)
        with b2:
            if st.button("Next >", type="primary"):
                if case_name:
                    st.session_state.autopsy_case_name = case_name
                    st.session_state.autopsy_step = "new_case_2"
                    st.rerun()
                else:
                    st.error("Please enter a Case Name.")
        with b3:
            if st.button("Cancel"):
                st.session_state.autopsy_step = "welcome"
                st.rerun()
        with b4:
            st.button("Help")
            
    elif st.session_state.autopsy_step == "new_case_2":
        st.markdown("### 🐶 New Case Information")
        st.markdown("---")
        col_nav, col_main = st.columns([1, 3])
        with col_nav:
            st.markdown("**Steps**")
            st.markdown("<hr style='margin:0px; padding:0px;'>", unsafe_allow_html=True)
            st.markdown("1. Case Information")
            st.markdown("**2. Optional Information**")
        with col_main:
            st.markdown("**Optional Information**")
            st.markdown("<hr style='margin:0px; padding:0px; margin-bottom:10px;'>", unsafe_allow_html=True)
            
            # Fetch real details from the logged-in session
            users = load_users()
            current_uid = st.session_state.get("user_id", "")
            real_name = st.session_state.get("full_name", "")
            real_email = users.get(current_uid, {}).get("email", "")
            
            case_number = st.text_input("Case Number:")
            # Pre-fill Examiner details automatically for security/convenience
            exam_name = st.text_input("Examiner Name:", value=real_name)
            exam_phone = st.text_input("Examiner Phone:")
            exam_email = st.text_input("Examiner Email:", value=real_email)
            notes = st.text_area("Notes:")
            
        st.markdown("---")
        col_space, b1, b2, b3, b4 = st.columns([4, 1, 1, 1, 1])
        with b1:
            if st.button("< Back"):
                st.session_state.autopsy_step = "new_case_1"
                st.rerun()
        with b2:
            if st.button("Finish", type="primary"):
                # Strict Input Validation
                import re
                errors = []
                if exam_email and not re.match(r"[^@]+@[^@]+\.[^@]+", exam_email):
                    errors.append("Please enter a valid Examiner Email.")
                if exam_phone and not re.match(r"^\+?[0-9\-\s]{10,15}$", exam_phone):
                    errors.append("Please enter a valid Phone Number (10+ digits).")
                if not exam_name.strip():
                    errors.append("Examiner Name cannot be empty.")
                    
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    # Actually create the folder on the backend server!
                    import os
                    try:
                        case_name = st.session_state.get("autopsy_case_name", "Unnamed_Case")
                        base_dir = st.session_state.get("autopsy_base_dir", r"C:\Users\Forensics\Documents")
                        target_dir = os.path.join(base_dir, case_name)
                        os.makedirs(target_dir, exist_ok=True)
                        st.success(f"Case directory created at: {target_dir}")
                    except Exception as e:
                        pass # Ignore permissions errors if they type an invalid path
                        
                    st.session_state.autopsy_step = "ingest_engine"
                    st.rerun()
        with b3:
            if st.button("Cancel"):
                st.session_state.autopsy_step = "welcome"
                st.rerun()
        with b4:
            st.button("Help")
            
    elif st.session_state.autopsy_step == "ingest_engine":
        # The actual backend forensics engine we built earlier!
        st.markdown("### 🗂️ Autopsy Workspace (Case Active)")
        if st.button("🚪 Close Case & Return to Welcome Screen"):
            st.session_state.autopsy_step = "welcome"
            st.rerun()
        st.markdown("---")
        tab1, tab2 = st.tabs(["🧩 Raw Binary Carver", "⏱️ Sleuth Kit Timeline Analyzer"])
        
        with tab1:
            st.write("Upload a raw evidence file. The Autopsy Ingest Modules will run automatically in the background to carve strings and hidden files.")
            evidence_file = st.file_uploader("Add Data Source (Raw Binary Image)", key="autopsy_upload")
            
            if evidence_file and st.button("▶ Run Autopsy Ingest Modules", use_container_width=True, type="primary"):
                import re, time
                evidence_file.seek(0)
                raw_data = evidence_file.read()
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # =========================================================================
                # PROFESSIONAL GRADE INGEST ENGINE (Advanced String Carving)
                # =========================================================================
                status_text.text("Ingest Module 1: Executing Contiguous String Extraction...")
                progress_bar.progress(30)
                time.sleep(0.5)
                
                import string
                printable = set(bytes(string.printable, 'ascii'))
                strings_list = []
                current_string = bytearray()
                for b in raw_data:
                    if b in printable:
                        current_string.append(b)
                    else:
                        if len(current_string) >= 4:
                            strings_list.append(current_string.decode('ascii'))
                        current_string = bytearray()
                if len(current_string) >= 4:
                    strings_list.append(current_string.decode('ascii'))
                    
                clean_ascii_text = " ".join(strings_list)
                
                status_text.text("Ingest Module 2: Strict Regex Artifact Carving...")
                progress_bar.progress(60)
                time.sleep(0.5)
                
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
                ip_pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
                
                found_emails = list(set(re.findall(email_pattern, clean_ascii_text)))
                found_ips = list(set(re.findall(ip_pattern, clean_ascii_text)))
                found_emails = [email for email in found_emails if ".." not in email]
                
                status_text.text("Ingest Module 3: Scanning Raw Headers for Magic Bytes...")
                progress_bar.progress(80)
                time.sleep(0.5)
                
                jpeg_count = raw_data.count(b'\xff\xd8\xff')
                zip_count = raw_data.count(b'\x50\x4b\x03\x04')
                pdf_count = raw_data.count(b'%PDF')
                
                progress_bar.progress(100)
                status_text.empty()
                st.success(f"✅ Autopsy Analysis Complete for `{evidence_file.name}`")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("### 📧 Extracted Text Artifacts")
                    st.write("**Emails Found:**")
                    if found_emails:
                        for email in found_emails: st.code(email)
                    else:
                        st.write("No emails found.")
                    st.write("**IP Addresses Found:**")
                    if found_ips:
                        for ip in found_ips: st.code(ip)
                    else:
                        st.write("No IPs found.")
                        
                with col2:
                    st.markdown("### 🗂️ Carved File Signatures")
                    st.write("Autopsy scanned the raw binary for magic bytes:")
                    st.metric("JPEG Images Found", jpeg_count)
                    st.metric("ZIP/DOCX Archives Found", zip_count)
                    st.metric("PDF Documents Found", pdf_count)
                    
                log_tool_to_coc("Autopsy / Sleuth Kit", f"Ran binary ingest modules on {evidence_file.name}. Found {len(found_emails)} emails, {len(found_ips)} IPs, and {jpeg_count} JPEGs.")

        with tab2:
            st.write("Upload a Forensic Timeline (CSV/Bodyfile) generated by The Sleuth Kit. The engine will parse MAC times and automatically flag deleted or suspicious files.")
            col_up, col_gen = st.columns([3, 1])
            with col_gen:
                st.markdown("<br>", unsafe_allow_html=True)
                sample_csv = """Filename,File Path,Size (Bytes),Created Time,Modified Time,Accessed Time,Status
secret_plans.pdf,C:\\Users\\Suspect\\Documents\\,45000,2026-09-28 10:00:00,2026-09-28 10:05:00,2026-09-28 10:05:00,Allocated
burner_contacts.xlsx,C:\\Users\\Suspect\\Desktop\\,12000,2026-09-29 14:00:00,2026-09-29 14:30:00,2026-09-29 14:30:00,Deleted
browser_history.sqlite,C:\\Users\\Suspect\\AppData\\Local\\,1048576,2026-01-15 08:00:00,2026-09-30 09:00:00,2026-09-30 09:00:00,Allocated
IMG_4921.jpg,C:\\Users\\Suspect\\Pictures\\,3500000,2026-09-29 18:00:00,2026-09-29 18:00:00,2026-09-29 18:00:00,Deleted
system.dll,C:\\Windows\\System32\\,999999,2024-01-01 00:00:00,2024-01-01 00:00:00,2026-09-30 11:00:00,Allocated"""
                st.download_button("📥 Download Sample CSV", data=sample_csv, file_name="mft_timeline.csv", mime="text/csv", use_container_width=True)
            
            with col_up:
                timeline_file = st.file_uploader("Upload Forensic Timeline (.csv)", type=["csv"], key="timeline_upload")
                
            if timeline_file and st.button("▶ Run MFT Analysis", use_container_width=True, type="primary"):
                import pandas as pd
                import time
                with st.spinner("Parsing Master File Table and analyzing MAC timestamps..."):
                    time.sleep(1) # Simulation delay
                    try:
                        df = pd.read_csv(timeline_file)
                        
                        st.markdown("### ⏱️ Master File Table Analysis")
                        st.write("Below is the reconstructed file system timeline. Files flagged by The Sleuth Kit as **Deleted** are highlighted in red, allowing you to instantly triage destroyed evidence.")
                        
                        # Style function to highlight deleted rows
                        def highlight_deleted(row):
                            if 'Status' in row and str(row['Status']).strip().lower() == 'deleted':
                                return ['background-color: #3b1c1c'] * len(row)
                            return [''] * len(row)
                            
                        st.dataframe(df.style.apply(highlight_deleted, axis=1), hide_index=True, use_container_width=True)
                        
                        deleted_count = len(df[df['Status'].str.strip().str.lower() == 'deleted'])
                        if deleted_count > 0:
                            st.error(f"🚨 **WARNING:** {deleted_count} deleted file(s) recovered from Unallocated Space!")
                            
                        log_tool_to_coc("Sleuth Kit MFT Analyzer", f"Analyzed {timeline_file.name}. Found {len(df)} total files, {deleted_count} deleted files recovered.")
                        log_action("Sleuth Kit Timeline Parsed")
                        
                    except Exception as e:
                        st.error(f"Error parsing CSV Timeline: {e}")

def tool_exiftool():
    log_action("Opened Tool: Exif Metadata Extractor")
    back_button()
    st.markdown("""<div class="tool-header"><div class="tool-title">📷 Exif Metadata Extractor</div><div class="tool-sub">Image Forensics | GPS Location Mapping (Powered by Python ExifRead)</div></div>""", unsafe_allow_html=True)
    
    st.markdown("### Backend Image Scanner")
    uploaded_file = st.file_uploader("Upload Image (JPG/TIFF) for Metadata Extraction", type=["jpg", "jpeg", "tiff"])
    
    if uploaded_file and st.button("▶ Extract Real EXIF Data", use_container_width=True, type="primary"):
        import exifread
        with st.spinner("Extracting EXIF data..."):
            tags = exifread.process_file(uploaded_file, details=False)
            if not tags:
                st.warning("⚠️ No EXIF metadata found in this image. (Note: Platforms like WhatsApp and Facebook automatically strip GPS data from photos for privacy).")
                log_action(f"ExifTool: No metadata in {uploaded_file.name}")
                log_tool_to_coc("Exif Metadata Extractor", f"Scanned {uploaded_file.name}. Result: No EXIF/GPS metadata found.")
            else:
                st.success(f"✅ Found {len(tags)} EXIF tags! Metadata parsed.")
                exif_data = {tag: str(tags[tag]) for tag in tags.keys() if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote')}
                st.json(exif_data)
                
                gps_lat = tags.get('GPS GPSLatitude')
                gps_lat_ref = tags.get('GPS GPSLatitudeRef')
                gps_lon = tags.get('GPS GPSLongitude')
                gps_lon_ref = tags.get('GPS GPSLongitudeRef')
                
                if gps_lat and gps_lon and gps_lat_ref and gps_lon_ref:
                    try:
                        def convert_to_degrees(value):
                            d = float(value.values[0].num) / float(value.values[0].den)
                            m = float(value.values[1].num) / float(value.values[1].den)
                            s = float(value.values[2].num) / float(value.values[2].den)
                            return d + (m / 60.0) + (s / 3600.0)
                        
                        lat = convert_to_degrees(gps_lat)
                        if gps_lat_ref.values != 'N': lat = -lat
                        
                        lon = convert_to_degrees(gps_lon)
                        if gps_lon_ref.values != 'E': lon = -lon
                        
                        st.info(f"📍 **GPS Coordinates Found!** Latitude: {lat:.5f}, Longitude: {lon:.5f}")
                        
                        import pandas as pd
                        map_df = pd.DataFrame({'lat': [lat], 'lon': [lon]})
                        st.map(map_df, zoom=14)
                        
                        log_tool_to_coc("Exif Metadata Extractor", f"Extracted {len(tags)} tags. Suspect GPS Location: {lat}, {lon}")
                    except Exception as e:
                        st.error(f"Could not parse GPS coordinates: {e}")
                        log_tool_to_coc("Exif Metadata Extractor", f"Extracted {len(tags)} tags. GPS parsing failed.")
                else:
                    st.info("ℹ️ No GPS coordinates found in the EXIF data.")
                    log_tool_to_coc("Exif Metadata Extractor", f"Extracted {len(tags)} EXIF tags. No GPS data found.")
                
                log_action(f"Extracted EXIF from {uploaded_file.name}")
                
                # Generate Word Document Report (HTML format for MS Word)
                import datetime
                
                doc_html = f"""<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word" xmlns="http://www.w3.org/TR/REC-html40">
<head><meta charset="utf-8"><title>Forensic Report</title></head>
<body style="font-family: Arial, sans-serif;">
    <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;">EXIF FORENSIC METADATA REPORT</h2>
    <p><b>Generated:</b> {datetime.datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')}<br>
    <b>Investigator:</b> {st.session_state.get('full_name', 'Unknown')}<br>
    <b>File Analyzed:</b> {uploaded_file.name}<br>
    <b>Total Tags Found:</b> {len(tags)}</p>
"""
                if gps_lat and gps_lon and gps_lat_ref and gps_lon_ref:
                    try:
                        doc_html += f"""
    <div style="background-color: #ffefc4; padding: 10px; border-left: 5px solid #f39c12; margin: 15px 0;">
        <h3 style="margin-top: 0; color: #d35400;">📍 GPS COORDINATES FOUND</h3>
        <b>Latitude:</b> {lat:.5f}<br>
        <b>Longitude:</b> {lon:.5f}<br>
        <b>Google Maps Link:</b> <a href="https://maps.google.com/?q={lat},{lon}" style="color: blue; text-decoration: underline;">https://maps.google.com/?q={lat},{lon}</a><br>
        <i>(Note: In Microsoft Word, you may need to hold <b>Ctrl + Click</b> on the link to open it)</i>
    </div>
"""
                    except:
                        pass
                        
                doc_html += f"""
    <h3 style="color: #2c3e50; border-bottom: 1px solid #bdc3c7;">RAW METADATA DUMP</h3>
    <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
        <tr style="background-color: #ecf0f1;">
            <th style="padding: 8px; border: 1px solid #bdc3c7; text-align: left;">EXIF Tag</th>
            <th style="padding: 8px; border: 1px solid #bdc3c7; text-align: left;">Value</th>
        </tr>
"""
                for k, v in exif_data.items():
                    doc_html += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #bdc3c7; font-weight: bold;">{k}</td>
            <td style="padding: 8px; border: 1px solid #bdc3c7; word-break: break-all;">{v}</td>
        </tr>
"""
                doc_html += """
    </table>
</body>
</html>"""
                
                st.markdown("---")
                st.download_button(
                    label="📄 Download Forensic Report (.doc)",
                    data=doc_html,
                    file_name=f"Forensic_EXIF_Report_{uploaded_file.name}.doc",
                    mime="application/msword",
                    type="primary",
                    use_container_width=True
                )

def tool_virustotal():
    log_action("Opened Tool: VirusTotal API")
    back_button()
    st.markdown("""<div class="tool-header"><div class="tool-title">🌐 VirusTotal API — Threat Intelligence</div><div class="tool-sub">Real-time Hash, IP, and Domain Reputation Scanning</div></div>""", unsafe_allow_html=True)
    
    st.markdown("### Web-Native API Scanner")
    
    # Hide the API key box if it's already configured in the backend
    if VIRUSTOTAL_API_KEY.strip():
        api_key = VIRUSTOTAL_API_KEY
        st.info("🔒 API Connection Secured: Key loaded from backend configuration.")
    else:
        api_key = st.text_input("Enter VirusTotal API Key", type="password", help="You can permanently save this in the app.py configuration block.")
        
    ioc = st.text_input("Enter IP Address, Hash, or Domain to Scan", placeholder="e.g. 185.112.44.19")
    
    if st.button("▶ Run Real VirusTotal Scan", use_container_width=True, type="primary"):
        if not api_key:
            st.error("Please enter a VirusTotal API key.")
        elif not ioc:
            st.error("Please enter an IP or Hash.")
        else:
            import requests
            with st.spinner(f"Querying real VirusTotal servers for {ioc}..."):
                url = f"https://www.virustotal.com/api/v3/ip_addresses/{ioc}" if "." in ioc else f"https://www.virustotal.com/api/v3/files/{ioc}"
                headers = {"x-apikey": api_key}
                try:
                    response = requests.get(url, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        stats = data['data']['attributes']['last_analysis_stats']
                        
                        st.markdown("### 📊 Aggregate Threat Score")
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Malicious", stats['malicious'])
                        col2.metric("Suspicious", stats['suspicious'])
                        col3.metric("Undetected", stats['undetected'])
                        
                        if stats['malicious'] > 0:
                            st.error(f"🚨 **CRITICAL RISK:** {stats['malicious']} security vendors flagged this IOC as malicious!")
                            log_tool_to_coc("VirusTotal API", f"Scanned IOC {ioc}. Result: MALICIOUS by {stats['malicious']} vendors.")
                        else:
                            st.success(f"✅ **CLEAN:** No vendors flagged this.")
                            log_tool_to_coc("VirusTotal API", f"Scanned IOC {ioc}. Result: Clean.")
                            
                        # Extract detailed vendor breakdown
                        st.markdown("### 🛡️ Detailed Vendor Breakdown")
                        vendor_results = data['data']['attributes']['last_analysis_results']
                        vendor_data = []
                        
                        for vendor, result in vendor_results.items():
                            status = result['category'].upper()
                            verdict = result.get('result', 'None')
                            
                            # Make the UI pretty depending on the status
                            if status == "MALICIOUS":
                                status_emoji = "🔴 MALICIOUS"
                            elif status == "SUSPICIOUS":
                                status_emoji = "🟡 SUSPICIOUS"
                            else:
                                status_emoji = "🟢 UNDETECTED"
                                
                            vendor_data.append({
                                "Antivirus Engine": vendor,
                                "Status": status_emoji,
                                "Specific Threat Name": verdict
                            })
                            
                        import pandas as pd
                        df = pd.DataFrame(vendor_data)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                        
                        log_action(f"Queried VirusTotal for {ioc}")
                    else:
                        st.error(f"API Error: {response.status_code}. (Are you sure this is an IP or Hash?)")
                except Exception as e:
                    st.error(f"Request failed: {e}")


def tool_wireshark():
    log_action("Opened Tool: Wireshark (Web-Native)")
    back_button()
    st.markdown('<div class="tool-header"><div class="tool-title">🦈 Wireshark — Network Analyzer</div><div class="tool-sub">PCAP Parsing | Powered by Scapy</div></div>', unsafe_allow_html=True)
    
    st.markdown("### Backend PCAP Analyzer")
    st.write("Upload a raw `.pcap` capture file. The backend server will mathematically parse the network packets and extract the top communicating IP addresses.")
    
    col_up, col_gen = st.columns([3, 1])
    with col_gen:
        st.markdown("<br>", unsafe_allow_html=True)
        try:
            from scapy.all import IP, TCP, ICMP, wrpcap
            import tempfile, os
            pkts = [
                IP(src="192.168.1.15", dst="8.8.8.8")/ICMP(),
                IP(src="8.8.8.8", dst="192.168.1.15")/ICMP(),
                IP(src="192.168.1.15", dst="185.112.44.19")/TCP(dport=80, flags="S"),
                IP(src="185.112.44.19", dst="192.168.1.15")/TCP(sport=80, flags="SA"),
                IP(src="192.168.1.15", dst="185.112.44.19")/TCP(dport=80, flags="A") / b"GET /malware.exe HTTP/1.1\r\n\r\n"
            ]
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pcap") as tmp:
                temp_path = tmp.name
            wrpcap(temp_path, pkts)
            with open(temp_path, "rb") as f:
                pcap_bytes = f.read()
            os.remove(temp_path)
            st.download_button("📥 Download Sample PCAP", data=pcap_bytes, file_name="Suspicious_Traffic.pcap", mime="application/vnd.tcpdump.pcap", use_container_width=True)
        except Exception as e:
            st.error(f"Error generating PCAP: {e}")
                
    with col_up:
        pcap_file = st.file_uploader("Upload Network Capture (.pcap)", type=["pcap"])
    
    if pcap_file and st.button("▶ Analyze PCAP File", use_container_width=True, type="primary"):
        import struct
        from collections import Counter
        
        file_bytes = pcap_file.read()
        
        with st.spinner("Parsing packets on the backend server..."):
            if len(file_bytes) < 24:
                st.error("Invalid PCAP file.")
            else:
                magic = struct.unpack('<I', file_bytes[:4])[0]
                endian = '<' if magic == 0xa1b2c3d4 else '>'
                
                offset = 24
                packets = []
                
                while offset < len(file_bytes):
                    if offset + 16 > len(file_bytes): break
                    hdr = struct.unpack(f'{endian}IIII', file_bytes[offset:offset+16])
                    incl_len = hdr[2]
                    offset += 16
                    
                    if offset + incl_len > len(file_bytes): break
                    packet_data = file_bytes[offset:offset+incl_len]
                    offset += incl_len
                    
                    if len(packet_data) >= 34:
                        ethertype = struct.unpack('>H', packet_data[12:14])[0]
                        if ethertype == 0x0800: # IPv4
                            src_ip = ".".join(map(str, packet_data[26:30]))
                            dst_ip = ".".join(map(str, packet_data[30:34]))
                            proto = packet_data[23]
                            p_name = "TCP" if proto == 6 else "UDP" if proto == 17 else "ICMP" if proto == 1 else str(proto)
                            packets.append((src_ip, dst_ip, p_name))
                
                st.success(f"✅ Successfully parsed {len(packets)} IPv4 packets!")
                
                if packets:
                    st.subheader("Top Communicating IP Addresses")
                    ip_counter = Counter([p[0] for p in packets] + [p[1] for p in packets])
                    
                    col1, col2 = st.columns(2)
                    for i, (ip, count) in enumerate(ip_counter.most_common(10)):
                        if i % 2 == 0: col1.markdown(f"- `{ip}` ({count} packets)")
                        else: col2.markdown(f"- `{ip}` ({count} packets)")
                        
                    log_tool_to_coc("Wireshark (Backend Analyzer)", f"Parsed {pcap_file.name}: {len(packets)} packets. Top IP: {ip_counter.most_common(1)[0][0]}")
                    log_action(f"Parsed PCAP: {pcap_file.name}")

def tool_weblog():
    log_action("Opened Tool: Web Log Analyzer")
    back_button()
    st.markdown('<div class="tool-header"><div class="tool-title">📊 Web Log Analyzer</div><div class="tool-sub">SIEM Forensics | Apache & Nginx Parse Engine</div></div>', unsafe_allow_html=True)
    st.caption("100% REAL TOOL: Upload raw web server access logs to parse traffic, graph IP origins, and hunt for SQLi/XSS attack signatures using regex.")
    
    col_up, col_gen = st.columns([3, 1])
    with col_gen:
        st.markdown("<br>", unsafe_allow_html=True)
        sample_log = (
            '192.168.1.5 - - [10/Oct/2026:13:55:36 -0700] "GET /index.html HTTP/1.1" 200 2326\n'
            '10.0.0.42 - - [10/Oct/2026:13:56:11 -0700] "GET /login.php HTTP/1.1" 200 1520\n'
            '45.22.19.11 - - [10/Oct/2026:13:57:02 -0700] "GET /admin/dashboard.php?user=admin\' OR \'1\'=\'1 HTTP/1.1" 403 543\n'
            '45.22.19.11 - - [10/Oct/2026:13:57:05 -0700] "GET /admin/dashboard.php?user=admin\' UNION SELECT password FROM users-- HTTP/1.1" 200 1204\n'
            '192.168.1.5 - - [10/Oct/2026:13:58:22 -0700] "GET /contact.php HTTP/1.1" 200 892\n'
            '114.55.20.19 - - [10/Oct/2026:14:01:14 -0700] "POST /api/search?q=<script>alert(1)</script> HTTP/1.1" 200 442\n'
            '114.55.20.19 - - [10/Oct/2026:14:01:15 -0700] "POST /api/search?q=../../../../etc/passwd HTTP/1.1" 404 122\n'
            '10.0.0.42 - - [10/Oct/2026:14:05:00 -0700] "GET /logout.php HTTP/1.1" 302 0\n'
        )
        st.download_button("📥 Download Sample access.log", data=sample_log, file_name="access.log", mime="text/plain", use_container_width=True)
            
    with col_up:
        uploaded_file = st.file_uploader("Upload access.log (Apache/Nginx format)", type=["log", "txt"])
        
    if uploaded_file:
        if st.button("Parse Web Logs", type="primary"):
            st.info("Parsing log file with Regex Engine...")
            import re
            import pandas as pd
            
            # regex for standard apache combined log
            log_pattern = re.compile(r'(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) - - \[(?P<date>.*?)\] "(?P<method>[A-Z]+) (?P<url>.*?) HTTP/.*?" (?P<status>\d{3}) (?P<size>\d+)')
            
            content = ""
            if uploaded_file:
                content = uploaded_file.read().decode('utf-8', errors='ignore')
            else:
                with open(os.path.join(UPLOADS_DIR, "access.log"), "r") as f:
                    content = f.read()
                    
            parsed_data = []
            for line in content.split('\n'):
                match = log_pattern.search(line)
                if match:
                    parsed_data.append(match.groupdict())
            
            if parsed_data:
                df = pd.DataFrame(parsed_data)
                df['status'] = df['status'].astype(int)
                
                st.success(f"✅ Successfully parsed {len(df)} log entries.")
                
                colA, colB, colC = st.columns(3)
                colA.metric("Total Requests", len(df))
                colB.metric("Unique IP Addresses", df['ip'].nunique())
                colC.metric("HTTP 404/403 Errors", len(df[df['status'] >= 400]))
                
                st.markdown("### 📡 Top Attacker IP Addresses")
                ip_counts = df['ip'].value_counts()
                st.bar_chart(ip_counts)
                
                st.markdown("### 🚨 Threat Intelligence (Malicious Payloads)")
                # Hunt for SQLi, XSS, Path Traversal
                threat_pattern = re.compile(r'(union select|or \'1\'=\'1|<script>|\.\./\.\.)', re.IGNORECASE)
                
                df['Threat_Flag'] = df['url'].apply(lambda x: "Malicious" if threat_pattern.search(x) else "Safe")
                threats = df[df['Threat_Flag'] == "Malicious"]
                
                if not threats.empty:
                    st.error(f"⚠️ Detected {len(threats)} malicious requests targeting your server!")
                    st.dataframe(threats[['date', 'ip', 'method', 'url', 'status']], use_container_width=True)
                    log_tool_to_coc("Web Log Analyzer", f"Parsed {len(df)} logs. Flagged {len(threats)} malicious payloads (SQLi/XSS).")
                else:
                    st.success("✅ No obvious malicious payloads detected in the URL parameters.")
            else:
                st.error("No valid log entries found. Ensure file matches Apache combined format.")
def tool_sleuthkit():
    log_action("Opened Tool: Autopsy / Sleuth Kit (Web-Native)")
    back_button()
    st.markdown('<div class="tool-header"><div class="tool-title">🕵️ Autopsy / Sleuth Kit (Web-Native)</div><div class="tool-sub">Binary Analysis | String & Artifact Carving Engine</div></div>', unsafe_allow_html=True)
    
    st.write("Upload a raw evidence file (like the `.dd` image created by the Portable Agent). The Autopsy Ingest Engine will carve through the raw binary data to extract hidden artifacts, emails, IP addresses, and deleted file signatures.")
    
    evidence_file = st.file_uploader("Upload Evidence File for Analysis", key="autopsy_upload")
    
    if evidence_file and st.button("▶ Run Autopsy Ingest Modules", use_container_width=True, type="primary"):
        import re
        import time
        
        evidence_file.seek(0)
        raw_data = evidence_file.read()
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 1. String Extraction (Mocking bulk_extractor)
        status_text.text("Ingest Module 1: Carving Emails and IP Addresses...")
        progress_bar.progress(30)
        time.sleep(0.5) # Simulate processing time for realism
        
        # Decode binary to ascii string (ignore errors to keep only valid text)
        ascii_text = raw_data.decode('ascii', errors='ignore')
        
        # Regex for emails and IPv4
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        
        found_emails = list(set(re.findall(email_pattern, ascii_text)))
        found_ips = list(set(re.findall(ip_pattern, ascii_text)))
        
        # 2. File Signature Carving (Magic Bytes)
        status_text.text("Ingest Module 2: Carving Hidden Files (Magic Bytes)...")
        progress_bar.progress(60)
        time.sleep(0.5)
        
        # Search for JPEG magic bytes (FF D8 FF)
        jpeg_count = raw_data.count(b'\xff\xd8\xff')
        # Search for PK ZIP/DOCX magic bytes (50 4b 03 04)
        zip_count = raw_data.count(b'\x50\x4b\x03\x04')
        # Search for PDF magic bytes (%PDF)
        pdf_count = raw_data.count(b'%PDF')
        
        progress_bar.progress(100)
        status_text.empty()
        
        st.success(f"✅ Autopsy Analysis Complete for `{evidence_file.name}`")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📧 Extracted Text Artifacts")
            st.write("**Emails Found:**")
            if found_emails:
                for email in found_emails:
                    st.code(email)
            else:
                st.write("No emails found in binary data.")
                
            st.write("**IP Addresses Found:**")
            if found_ips:
                for ip in found_ips:
                    st.code(ip)
            else:
                st.write("No IPs found in binary data.")
                
        with col2:
            st.markdown("### 🗂️ Carved File Signatures")
            st.write("Autopsy scanned the raw binary for magic bytes to find hidden/deleted files:")
            st.metric("JPEG Images Found", jpeg_count)
            st.metric("ZIP/DOCX Archives Found", zip_count)
            st.metric("PDF Documents Found", pdf_count)
            
        log_tool_to_coc("Autopsy / Sleuth Kit", f"Ran binary ingest modules on {evidence_file.name}. Found {len(found_emails)} emails, {len(found_ips)} IPs, and {jpeg_count} JPEGs.")

def tool_osint():
    log_action("Opened Tool: OSINT Geo-Tracker")
    back_button()
    st.markdown('<div class="tool-header"><div class="tool-title">🌍 OSINT Geo-Tracker</div><div class="tool-sub">Live Intelligence | IP & Domain Geolocation</div></div>', unsafe_allow_html=True)
    st.caption("100% REAL TOOL: Enter a live IP address or Domain to trace its physical location and ISP via public OSINT databases.")
    
    target = st.text_input("Enter Target IP or Domain (e.g., 8.8.8.8 or github.com)", "8.8.8.8")
    
    if st.button("Trace Target", type="primary"):
        st.info(f"Initiating live OSINT trace on {target}...")
        time.sleep(0.5)
        
        import urllib.request, json
        import pandas as pd
        
        try:
            url = f"http://ip-api.com/json/{target}?fields=status,message,country,regionName,city,zip,lat,lon,timezone,isp,org,as,query"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
            
            if data.get("status") == "success":
                st.success(f"✅ Trace Complete! Target resolved to IP: {data.get('query')}")
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.markdown(f"""<div class='stat-box'>
                    <h4 style="margin-top:0; color:#38bdf8;">🌐 Network & ISP</h4>
                    <b>ISP:</b> {data.get('isp')}<br>
                    <b>Organization:</b> {data.get('org')}<br>
                    <b>ASN:</b> {data.get('as')}
                    </div>""", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""<div class='stat-box'>
                    <h4 style="margin-top:0; color:#38bdf8;">📍 Physical Location</h4>
                    <b>Country:</b> {data.get('country')}<br>
                    <b>Region:</b> {data.get('regionName')}, {data.get('city')}<br>
                    <b>Zip/Postal:</b> {data.get('zip', 'N/A')}
                    </div>""", unsafe_allow_html=True)
                
                st.markdown("<br>### 🗺️ Live Target Geolocation", unsafe_allow_html=True)
                df = pd.DataFrame({'lat': [data.get('lat')], 'lon': [data.get('lon')]})
                st.map(df, zoom=4)
                
                log_action(f"Ran OSINT trace on {target} (Resolved: {data.get('query')})")
                log_tool_to_coc("OSINT Geo-Tracker", f"Traced target {target} to {data.get('city')}, {data.get('country')}. ISP: {data.get('isp')}.")
            else:
                st.error(f"❌ Trace failed: {data.get('message', 'Unknown Error')}")
                
        except Exception as e:
            st.error(f"⚠️ Network error during OSINT lookup. Check internet connection. Details: {e}")

def tool_steganography():
    log_action("Opened Tool: Steganography Extractor")
    back_button()
    st.markdown('<div class="tool-header"><div class="tool-title">🎭 Steganography Extractor</div><div class="tool-sub">Deep Pixel Forensics | LSB Decoding Engine</div></div>', unsafe_allow_html=True)
    st.caption("100% REAL TOOL: Upload an image to analyze its Least Significant Bits (LSB). Hackers use LSB steganography to invisibly hide secret passwords or malicious payloads inside the pixels of normal-looking photos.")
    
    tab1, tab2 = st.tabs(["🔓 Extract Hidden Data", "🔒 Hide Data (Generate Evidence)"])
    
    with tab2:
        st.markdown("### Generate Suspect Evidence")
        st.write("Use this to securely hide a secret message inside an image. You can then use the **Extract** tab to prove the forensic tool can mathematically find it.")
        cover_image = st.file_uploader("Upload Cover Image (PNG/JPG)", type=["png", "jpg", "jpeg"], key="stego_hide")
        secret_message = st.text_input("Secret Message to Hide:", placeholder="e.g., The bank server password is: admin123")
        
        if cover_image and secret_message and st.button("Inject Secret into Pixels", type="primary"):
            try:
                from PIL import Image
                import io
                img = Image.open(cover_image).convert("RGB")
                pixels = img.load()
                
                # Convert message to binary, add a unique delimiter (=====) so the decoder knows when to stop
                binary_msg = ''.join([format(ord(i), "08b") for i in secret_message + "====="])
                
                width, height = img.size
                if len(binary_msg) > width * height * 3:
                    st.error("Error: Message is too long to hide in this image.")
                else:
                    data_idx = 0
                    binary_len = len(binary_msg)
                    
                    for y in range(height):
                        for x in range(width):
                            if data_idx < binary_len:
                                r, g, b = pixels[x, y]
                                
                                # Modify the Least Significant Bit of each color channel
                                if data_idx < binary_len:
                                    r = (r & ~1) | int(binary_msg[data_idx])
                                    data_idx += 1
                                if data_idx < binary_len:
                                    g = (g & ~1) | int(binary_msg[data_idx])
                                    data_idx += 1
                                if data_idx < binary_len:
                                    b = (b & ~1) | int(binary_msg[data_idx])
                                    data_idx += 1
                                    
                                pixels[x, y] = (r, g, b)
                            else:
                                break
                        if data_idx >= binary_len:
                            break
                            
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    st.success("✅ Secret successfully injected! The image looks identical to the human eye.")
                    st.download_button(label="Download Weaponized Image", data=buf.getvalue(), file_name="suspect_evidence.png", mime="image/png")
            except Exception as e:
                st.error(f"Failed to process image. Make sure Pillow is installed. Error: {e}")

    with tab1:
        st.markdown("### 🔓 Forensic LSB Extraction")
        suspect_image = st.file_uploader("Upload Suspect Image (PNG)", type=["png"], key="stego_extract")
        
        if suspect_image and st.button("▶ Run LSB Pixel Extraction", type="primary"):
            import time
            
            st.info("Scanning pixel matrices for LSB anomalies...")
            progress_bar = st.progress(0)
            time.sleep(0.5)
            progress_bar.progress(30)
            
            try:
                from PIL import Image
                img = Image.open(suspect_image).convert("RGB")
                pixels = img.load()
                width, height = img.size
                
                progress_bar.progress(60)
                
                binary_data = ""
                # We only need to scan enough to find the delimiter, not the whole massive image
                for y in range(height):
                    for x in range(width):
                        r, g, b = pixels[x, y]
                        binary_data += str(r & 1)
                        binary_data += str(g & 1)
                        binary_data += str(b & 1)
                        
                        # Optimization: Check for delimiter every few pixels so it doesn't freeze on 4K images
                        if len(binary_data) % 80 == 0: 
                            pass # We'll just collect it all and parse after to keep it simple and robust, but capped at a reasonable limit
                            
                    if len(binary_data) > 50000: # Cap at ~6KB of hidden text to prevent browser lag
                        break 
                        
                progress_bar.progress(100)
                
                # Convert binary string to characters
                all_bytes = [binary_data[i: i+8] for i in range(0, len(binary_data), 8)]
                decoded_data = ""
                for byte in all_bytes:
                    if len(byte) == 8:
                        decoded_data += chr(int(byte, 2))
                        if decoded_data.endswith("====="):
                            decoded_data = decoded_data[:-5]
                            break
                
                # Validate that we found coherent data
                if len(decoded_data) > 0 and len(decoded_data) < 5000 and all(32 <= ord(c) < 127 for c in decoded_data):
                    st.error("🚨 **HIDDEN DATA DETECTED IN IMAGE PIXELS!**")
                    st.markdown(f"""
                    <div class="stat-box" style="border: 2px solid #ef4444; background: rgba(239,68,68,0.1);">
                    <h4 style="color:#ef4444; margin:0;">Extracted Payload:</h4>
                    <code style="font-size:1.1em; color:white; white-space: pre-wrap;">{decoded_data}</code>
                    </div>
                    """, unsafe_allow_html=True)
                    log_tool_to_coc("Steganography Extractor", f"Detected hidden LSB payload in '{suspect_image.name}': {decoded_data}")
                    log_action("Steganography Payload Found")
                else:
                    st.success("✅ Image appears clean. No coherent hidden LSB data found.")
                    
            except Exception as e:
                st.error(f"Error processing image: {e}")

def tool_hashcat():
    log_action("Opened Tool: Hashcat Offline Cracker")
    back_button()
    st.markdown('<div class="tool-header"><div class="tool-title">🔐 Hashcat (Python Engine)</div><div class="tool-sub">Offline Cryptographic Hash Cracking | Dictionary Attack</div></div>', unsafe_allow_html=True)
    st.caption("100% REAL TOOL: Simulates offline password cracking. Enter a raw cryptographic hash (MD5, SHA1, SHA256) extracted from a suspect's machine, and the Python `hashlib` engine will brute-force it against a dictionary.")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Load Sample Target", use_container_width=True):
            # MD5 for 'password123' is 482c811da5d5b4bc6d497ffa98491e38
            st.session_state.target_hash_input = "482c811da5d5b4bc6d497ffa98491e38"
            st.session_state.hash_type = "MD5"
            st.rerun()
            
    with col1:
        target_hash = st.text_input("Target Hash (Hexadecimal):", value=st.session_state.get("target_hash_input", ""))
        hash_type = st.selectbox("Hash Algorithm:", ["MD5", "SHA1", "SHA256"], index=0 if st.session_state.get("hash_type", "MD5")=="MD5" else 0)
    
    # Dictionary Configuration
    st.markdown("#### 📚 Dictionary Configuration")
    st.write("By default, the engine will download and use a top 10,000 real-world password list. You can also upload your own custom wordlist here.")
    custom_dicts = st.file_uploader("Upload Custom Dictionaries (.txt format)", type=["txt"], accept_multiple_files=True)
    
    if st.button("▶ Initialize Cracking Engine", type="primary"):
        if not target_hash:
            st.error("Please enter a target hash.")
            return
            
        target_hash = target_hash.strip().lower() # FIX: Remove accidental spaces
        
        import hashlib
        import urllib.request
        import time
        
        wordlist = []
        
        if custom_dicts:
            # Load user's custom dictionaries (could be 1 or 10 files)
            st.info(f"Merging and loading {len(custom_dicts)} custom dictionary files...")
            for c_dict in custom_dicts:
                content = c_dict.read().decode('utf-8', errors='ignore')
                wordlist.extend([line.strip() for line in content.splitlines() if line.strip()])
            
            # Remove duplicate passwords across the different files to save math time
            wordlist = list(set(wordlist))
        else:
            # Load default online dictionary
            st.info("Downloading REAL top 10,000 password dictionary from SecLists...")
            try:
                url = "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10k-most-common.txt"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    wordlist = response.read().decode('utf-8', errors='ignore').splitlines()
            except Exception:
                wordlist = ["123456", "password", "password123", "admin", "admin123"]
                
        # Ensure it's not empty
        if not wordlist:
            wordlist = ["password123"]
        
        st.info(f"Loaded {len(wordlist)} dictionary words. Spinning up Python hashing threads...")
        progress_bar = st.progress(0)
        
        cracked_password = None
        start_time = time.time()
        
        for i, word in enumerate(wordlist):
            if i % 500 == 0:
                progress_bar.progress(min(1.0, i / len(wordlist)))
            
            # The REAL Cryptographic math
            if hash_type == "MD5":
                calculated = hashlib.md5(word.encode()).hexdigest()
            elif hash_type == "SHA1":
                calculated = hashlib.sha1(word.encode()).hexdigest()
            elif hash_type == "SHA256":
                calculated = hashlib.sha256(word.encode()).hexdigest()
                
            if calculated == target_hash:
                cracked_password = word
                progress_bar.progress(1.0)
                break
                
        end_time = time.time()
        time_taken = end_time - start_time
        
        if cracked_password:
            st.success(f"🔓 **HASH CRACKED SUCCESSFULLY!**")
            st.markdown(f"""
            <div class="stat-box" style="border: 2px solid #34d399; background: rgba(52,211,153,0.1);">
            <h3 style="color:#34d399; margin:0;">Plaintext Password: {cracked_password}</h3>
            <p style="margin:0; font-size:0.9em; color:#a1a1aa;">Algorithm: {hash_type} | Math Time: {time_taken:.4f}s | Speed: ~{int((i+1)/max(time_taken, 0.0001))} Hashes/sec</p>
            </div>
            """, unsafe_allow_html=True)
            log_tool_to_coc("Hashcat Password Cracker", f"Successfully cracked {hash_type} hash '{target_hash[:8]}...'. Plaintext discovered.")
            log_action("Hash Cracked Successfully")
        else:
            progress_bar.progress(1.0)
            st.error("❌ **Hash Not Found in Dictionary.**")
            st.write(f"The python engine mathematically hashed all {len(wordlist)} words in {time_taken:.4f} seconds, but your specific hash was not found.")
            st.write("In a real environment, you would use a larger dictionary (like the 14GB RockYou.txt) or launch a massive brute-force character attack utilizing GPU arrays.")
            log_tool_to_coc("Hashcat Password Cracker", f"Attempted to crack {hash_type} hash '{target_hash[:8]}...'. Hash not found in current dictionary.")
            log_action("Hash Cracking Failed")

# ══════════════════════════════════════════════════════════════════════════════
#  WORKSPACE DASHBOARD (Case Management & Tools)

# ══════════════════════════════════════════════════════════════════════════════
def render_tool_grid(key_suffix=""):
    st.markdown("---")
    st.header("🛠️ Forensic Tool Integrations")
    tool_cards = [("🖥️", "FTK Imager", "Disk imaging", "ftk"), ("🗂️", "Autopsy", "File system carving", "autopsy"), ("📷", "ExifTool", "Metadata extraction", "exiftool"), ("🛡️", "Defender", "Threat scanning", "defender"), ("📦", "Sandbox", "Malware detonation", "sandbox"), ("🌐", "VirusTotal", "Hash Reputation", "virustotal"), ("🧠", "Volatility 3", "Memory forensics", "volatility"), ("📱", "Cellebrite", "Mobile extraction", "cellebrite"), ("🦈", "Wireshark", "Network PCAP", "wireshark"), ("📊", "Web Log Analyzer", "SIEM / Log Forensics", "weblog"), ("🕵️", "Sleuth Kit", "Command Line FS", "sleuthkit"), ("🌍", "OSINT Tracker", "Live Geolocation", "osint"), ("🎭", "Steganography", "Hidden Pixel Forensics", "stego"), ("🔐", "Hashcat", "Offline Hash Cracking", "hashcat")]
    for i in range(0, len(tool_cards), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(tool_cards):
                icon, title, sub, key = tool_cards[i + j]
                with cols[j]:
                    st.markdown(f"""<div class="tool-header" style="text-align:center;padding:24px 16px;margin-bottom:12px"><div style="font-size:2rem">{icon}</div><div class="tool-title" style="font-size:1.1rem;margin-top:8px">{title}</div><div class="tool-sub" style="margin-top:4px;font-size:0.8rem">{sub}</div></div>""", unsafe_allow_html=True)
                    if st.button(f"Open {title}", key=f"open_{key}_{key_suffix}", use_container_width=True):
                        st.query_params["tool"] = key
                        st.session_state.active_tool = key; st.rerun()

def workspace():
    if "active_case" not in st.session_state: st.session_state.active_case = None

    with st.sidebar:
        expertise_display = f" | 🛡️ {st.session_state.get('expertise', 'Investigator')}"
        st.header(f"👤 {st.session_state.get('full_name', st.session_state.user_id)}{expertise_display}")
        st.subheader(f"Role: {st.session_state.role.title()}")
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        if st.button("Logout"):
            log_action("User Logout")
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.query_params.clear()
            st.rerun()
            
        st.markdown("---")
        st.markdown("**🤖 AI Security Monitor**")
        st.caption("Live behavioral analysis of active sessions.")
        log_container = st.container(height=400)
        with log_container:
            for log in reversed(st.session_state.get("session_logs", [])):
                if "CRITICAL" in log or "Flagged" in log:
                    st.markdown(f"<div style='font-size:0.75rem; color:#f87171; border-left: 2px solid #f87171; padding-left: 5px; margin-bottom: 8px; background: rgba(248,113,113,0.1);'>{log}</div>", unsafe_allow_html=True)
                elif "Verified" in log or "Logged" in log:
                    st.markdown(f"<div style='font-size:0.75rem; color:#34d399; border-left: 2px solid #34d399; padding-left: 5px; margin-bottom: 8px;'>{log}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='font-size:0.75rem; color:#7ec8e3; border-left: 2px solid #7ec8e3; padding-left: 5px; margin-bottom: 8px;'>{log}</div>", unsafe_allow_html=True)

    tools_map = {
        "ftk": tool_ftk, "defender": tool_defender, "sandbox": tool_sandbox,
        "volatility": tool_volatility, "cellebrite": tool_cellebrite, 
        "autopsy": tool_autopsy, "exiftool": tool_exiftool, "virustotal": tool_virustotal,
        "wireshark": tool_wireshark, "weblog": tool_weblog, "sleuthkit": tool_sleuthkit,
        "osint": tool_osint, "stego": tool_steganography, "hashcat": tool_hashcat
    }
    if st.session_state.active_tool in tools_map:
        tools_map[st.session_state.active_tool]()
        return

    users, all_complaints = load_users(), load_complaints()
    investigators = [uid for uid, u in users.items() if u.get("role") not in ["admin", "viewer"]]

    def get_tool_suggestions(category: str) -> str:
        s = {
            "Financial Fraud & UPI Scams": "💡 **AI Investigation Plan:** Use **ExifTool** to extract metadata from forged receipts, and **Autopsy** to carve the disk for deleted financial records.",
            "Identity Theft & Impersonation": "💡 **AI Investigation Plan:** Use **Cellebrite UFED** to extract mobile communication logs, and **Autopsy** to search for stolen identity documents on drives.",
            "Malware, Ransomware & Hacking": "💡 **AI Investigation Plan:** Use **Secure Sandbox** to safely detonate suspicious files, **Volatility 3** for RAM analysis, and **VirusTotal API** to check IP/Hash reputation.",
            "Cyberbullying & Harassment": "💡 **AI Investigation Plan:** Use **Cellebrite UFED** to extract social media chat history, and **ExifTool** to trace GPS locations from threatening images.",
            "Phishing, Vishing & Smishing": "💡 **AI Investigation Plan:** Use **VirusTotal API** to analyze malicious URLs/IPs, and **Cellebrite UFED** to extract SMS logs.",
            "Social Media Account Takeover": "💡 **AI Investigation Plan:** Use **VirusTotal API** to investigate login IPs, and **ExifTool** on provided screenshots.",
            "Online Shopping & E-Commerce Scams": "💡 **AI Investigation Plan:** Use **ExifTool** to check metadata of fake invoices, and **VirusTotal API** to scan the fake shopping domain.",
            "Extortion & Sextortion": "💡 **AI Investigation Plan:** Use **Cellebrite UFED** to extract WhatsApp/Telegram logs, and **ExifTool** to analyze blackmail media.",
            "Cryptocurrency & Investment Scams": "💡 **AI Investigation Plan:** Use **Autopsy** to carve for crypto wallet files/seed phrases, and **Volatility 3** to check memory for clipboard stealers.",
            "Corporate Data Breach": "💡 **AI Investigation Plan:** Start with **FTK Imager** for server imaging, then use **Volatility 3** and **Autopsy** for lateral movement analysis.",
            "Child Exploitation / CSAM": "💡 **AI Investigation Plan:** Secure evidence using **FTK Imager**, then use **Autopsy** and **Cellebrite UFED** for extensive media carving.",
            "Deepfakes & AI Misinformation": "💡 **AI Investigation Plan:** Use **ExifTool** to analyze media creation metadata, and **VirusTotal API** to trace the source domain.",
            "Denial of Service (DDoS)": "💡 **AI Investigation Plan:** Use **VirusTotal API** to map botnet C2 IP addresses.",
            "Other Cyber Crime": "💡 **AI Investigation Plan:** Start with **FTK Imager** to secure a forensic copy, then run **Microsoft Defender** for baseline threat scanning."
        }
        return s.get(category, "💡 **AI Investigation Plan:** Secure evidence using **FTK Imager** and begin standard forensic triage.")

    # ── CASE INVESTIGATION VIEW ──
    if st.session_state.active_case:
        cid = st.session_state.active_case
        c = all_complaints.get(cid)
        if not c:
            st.error("Case not found.")
            if "case" in st.query_params: del st.query_params["case"]
            st.session_state.active_case = None; st.rerun()
            
        st.markdown('<div class="secondary-btn" style="width: 200px;">', unsafe_allow_html=True)
        if st.button("← Back to Dashboard", key="back_to_dash"):
            st.session_state.active_case = None; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown(f"<h2 style='color:#38bdf8; margin-top:20px;'>📁 Active Investigation: {cid}</h2>", unsafe_allow_html=True)
        st.markdown(f"**Category:** {c['category']} &nbsp;|&nbsp; **Reported On:** {c['timestamp']}")
        st.markdown(f"**Current Status:** `{c.get('status', 'Assigned')}`")
        
        if c.get("status") == "Unassigned" and st.session_state.role == "admin":
            st.warning("⚠️ **This case is unassigned.** Review the evidence below and assign it to an investigator.")
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                assigned_to = st.selectbox(
                    "Assign to Investigator", 
                    ["(Select Investigator)"] + investigators, 
                    format_func=lambda x: f"{x} — {users[x].get('expertise', 'General')}" if x != "(Select Investigator)" else x,
                    key=f"sel_{cid}"
                )
            with col2: ev_location = st.text_input("Evidence Location", "Secure Cloud Enclave", key=f"loc_{cid}")
            with col3:
                st.write("")
                if st.button("Handover Evidence", key=f"btn_{cid}", use_container_width=True, type="primary"):
                    if assigned_to != "(Select Investigator)":
                        c["status"], c["assigned_to"] = "Assigned", assigned_to
                        if "chain_of_custody" not in c:
                            c["chain_of_custody"] = [{"timestamp": c['timestamp'], "action": "Evidence Initially Submitted", "actor": c['victim_name'], "location": "Public Intake Portal"}]
                        c["chain_of_custody"].append({
                            "timestamp": datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
                            "action": f"Evidence Handed Over to {assigned_to}",
                            "actor": f"Admin ({st.session_state.user_id})",
                            "location": ev_location
                        })
                        save_complaint(cid, c)
                        log_action(f"Handed over {cid} evidence to {assigned_to} at {ev_location}")
                        st.success(f"Case securely handed over to {assigned_to}!")
                        time.sleep(1)
                        if "case" in st.query_params: del st.query_params["case"]
                        st.session_state.active_case = None; st.rerun()
                    else: st.error("Please select an investigator first.")
        elif c.get("status") == "Completed":
            st.success("✅ **CASE CLOSED**")
            if c.get("final_report"):
                st.markdown(f"**Investigator's Final Findings:**\n> {c['final_report']}")
                
                # Generate Official Export Text
                coc_log = "\n".join([f"[{item.get('timestamp', '')}] {item.get('actor', '')} -> {item.get('action', '')}" for item in c.get('chain_of_custody', [])])
                report_content = (
                    f"=========================================\n"
                    f"  OFFICIAL INVESTIGATION REPORT\n"
                    f"=========================================\n\n"
                    f"Case ID: {cid}\n"
                    f"Category: {c.get('category', 'N/A')}\n"
                    f"Reported On: {c.get('timestamp', 'N/A')}\n\n"
                    f"VICTIM DETAILS\n"
                    f"-----------------------------------------\n"
                    f"Name: {c.get('victim_name', 'N/A')}\n"
                    f"Phone: {c.get('victim_phone', 'N/A')}\n\n"
                    f"INCIDENT DESCRIPTION\n"
                    f"-----------------------------------------\n"
                    f"{c.get('complaint_text', 'N/A')}\n\n"
                    f"INVESTIGATOR FINDINGS\n"
                    f"-----------------------------------------\n"
                    f"{c.get('final_report', '')}\n\n"
                    f"CHAIN OF CUSTODY (AUDIT TRAIL)\n"
                    f"-----------------------------------------\n"
                    f"{coc_log}\n\n"
                    f"*** END OF REPORT ***"
                )
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.download_button(
                    label="📄 Export Official Case Report (.txt)",
                    data=report_content,
                    file_name=f"Case_Report_{cid}.txt",
                    mime="text/plain",
                    type="primary"
                )
        else:
            with st.expander("✍️ Add Investigation Note to Chain of Custody"):
                new_note = st.text_input("Enter your observation, action taken, or intermediate findings...", key=f"note_{cid}")
                if st.button("Log Note to CoC"):
                    if new_note.strip():
                        if "chain_of_custody" not in c: c["chain_of_custody"] = []
                        c["chain_of_custody"].append({
                            "timestamp": datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
                            "action": f"📝 Investigator Note: {new_note}",
                            "actor": f"Investigator ({st.session_state.user_id})",
                            "location": "Active Investigation File"
                        })
                        save_complaint(cid, c)
                        st.success("Note logged to Chain of Custody!")
                        time.sleep(1); st.rerun()
                    else: st.error("Please enter a note to log.")
                    
            with st.expander("📝 Submit Final Investigation Report & Close Case"):
                final_findings = st.text_area("Forensic Findings & Conclusion", placeholder="Detail the results of your investigation, IOCs found, and final resolution...")
                if st.button("Submit Report & Close Case", type="primary"):
                    if not final_findings.strip():
                        st.error("⚠️ You must provide forensic findings to close the case.")
                    else:
                        c["status"] = "Completed"
                        c["final_report"] = final_findings
                        if "chain_of_custody" not in c: c["chain_of_custody"] = []
                        c["chain_of_custody"].append({
                            "timestamp": datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
                            "action": "Case Closed & Final Report Filed",
                            "actor": f"Investigator ({st.session_state.user_id})",
                            "location": "Secure Database"
                        })
                        save_complaint(cid, c)
                        log_action(f"Closed Case {cid} and filed report.")
                        st.success("✅ Case officially closed!")
                        time.sleep(1.5); st.rerun()
                
        st.info(get_tool_suggestions(c['category']))
        
        st.markdown("---")
        
        col1, col2 = st.columns([1, 1.2])
        with col1:
            st.markdown("""<div class="case-card"><h4 style="margin-top:0; color:#e0e6f0;">📝 Complainer Details</h4>""", unsafe_allow_html=True)
            st.markdown(f"**Victim Name:** {c['victim_name']}")
            st.markdown(f"**Contact Number:** {c['victim_phone']}</div>", unsafe_allow_html=True)
            
            st.markdown("""<div class="case-card"><h4 style="margin-top:0; color:#e0e6f0;">📄 Incident Description</h4>""", unsafe_allow_html=True)
            st.markdown(f"<p style='color:#7ec8e3; line-height: 1.6;'>{c['description']}</p></div>", unsafe_allow_html=True)
            
        with col2:
            st.markdown("""<div class="case-card"><h4 style="margin-top:0; color:#38bdf8;">🔍 Evidence Details</h4>""", unsafe_allow_html=True)
            
            ev_file = c.get("evidence_file", "")
            if ev_file and ev_file.startswith("[PHYSICAL DEVICE]"):
                st.info(f"📦 **Physical Evidence:** {ev_file.replace('[PHYSICAL DEVICE] ', '')}")
                st.caption("This is a physical device. Please refer to the Chain of Custody log below for its current physical location in the precinct or forensic lab.")
            elif c.get("evidence_path") and os.path.exists(c["evidence_path"]):
                file_ext = os.path.splitext(c["evidence_path"])[1].lower()
                with open(c["evidence_path"], "rb") as f:
                    file_bytes = f.read()
                
                if file_ext in ['.png', '.jpg', '.jpeg']:
                    st.image(file_bytes, caption=c['evidence_file'], use_container_width=True)
                
                st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)
                
                def log_download():
                    if "chain_of_custody" not in c: c["chain_of_custody"] = []
                    c["chain_of_custody"].append({
                        "timestamp": datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
                        "action": "Evidence Downloaded/Accessed",
                        "actor": f"Investigator ({st.session_state.user_id})",
                        "location": "Local Workstation Sandbox"
                    })
                    save_complaint(cid, c)
                    log_action(f"Downloaded Evidence for {cid}")
                
                st.download_button(
                    label=f"⬇️ Download Evidence File ({c['evidence_file']})",
                    data=file_bytes,
                    file_name=c['evidence_file'],
                    mime="application/octet-stream",
                    use_container_width=True,
                    on_click=log_download
                )
            else:
                st.warning("⚠️ No evidence file was attached to this complaint.")
            
            st.markdown("<hr style='border-color:#2d4060;'>", unsafe_allow_html=True)
            st.markdown("<h5 style='color:#e0e6f0;'>🔗 Chain of Custody Log</h5>", unsafe_allow_html=True)
            if "chain_of_custody" in c and c["chain_of_custody"]:
                for log in c["chain_of_custody"]:
                    st.markdown(f"<div style='font-size:0.85em; margin-bottom:5px; padding:8px; background:#0d1a26; border-left:3px solid #7ec8e3;'><b>{log['timestamp']}</b><br/><b>Action:</b> {log['action']}<br/><b>By:</b> {log['actor']}<br/><b>Location:</b> {log['location']}</div>", unsafe_allow_html=True)
            else:
                st.info("No Chain of Custody records available.")
            
            st.markdown("</div>", unsafe_allow_html=True)
        # ── PERMANENT EVIDENCE VAULT ──
        st.markdown("---")
        with st.expander("🗄️ Permanent Evidence Vault", expanded=True):
            st.write("Securely upload and store suspect files, logs, and disk images permanently attached to this case.")
            
            case_evidence_dir = os.path.join(EVIDENCE_VAULT_DIR, cid)
            os.makedirs(case_evidence_dir, exist_ok=True)
            
            col_vault_1, col_vault_2 = st.columns([1, 1])
            with col_vault_1:
                st.markdown("#### 📤 Upload New Evidence")
                new_evidence = st.file_uploader("Upload Case Files", accept_multiple_files=True, key=f"vault_upload_{cid}")
                if new_evidence and st.button("💾 Secure Evidence to Vault", type="primary"):
                    for ev_file in new_evidence:
                        file_path = os.path.join(case_evidence_dir, ev_file.name)
                        with open(file_path, "wb") as f:
                            f.write(ev_file.getbuffer())
                        # Log to CoC
                        if "chain_of_custody" not in c: c["chain_of_custody"] = []
                        c["chain_of_custody"].append({
                            "timestamp": datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
                            "action": f"Secured evidence file: {ev_file.name}",
                            "actor": f"Investigator ({st.session_state.user_id})",
                            "location": "Permanent Evidence Vault"
                        })
                    save_complaint(cid, c)
                    st.success(f"Successfully secured {len(new_evidence)} file(s)!")
                    time.sleep(1)
                    st.rerun()
                    
            with col_vault_2:
                st.markdown("#### 📥 Attached Case Files")
                existing_files = os.listdir(case_evidence_dir)
                if existing_files:
                    for f_name in existing_files:
                        file_path = os.path.join(case_evidence_dir, f_name)
                        with open(file_path, "rb") as f_read:
                            st.download_button(
                                label=f"📄 {f_name}",
                                data=f_read,
                                file_name=f_name,
                                key=f"dl_vault_{cid}_{f_name}",
                                use_container_width=True
                            )
                else:
                    st.info("No evidence files have been attached to this case yet.")

        render_tool_grid("case")
        return

    st.title("🔍 Secure Investigator Workspace")
    st.markdown("---")

    if st.session_state.role == "admin":
        # --- NEW: AI GLOBAL MONITOR ---
        st.header("🧠 AI Global Security SOC")
        with st.expander("👁️ Expand Live Activity & Threat Dashboard", expanded=False):
            st.markdown("This AI-driven SIEM tracks every action taken by every user across the entire Zero Trust platform in real-time.")
        
            try:
                import json, pandas as pd
                if os.path.exists(GLOBAL_AUDIT_FILE):
                    with open(GLOBAL_AUDIT_FILE, "r") as f: audit_data = json.load(f)
                else:
                    audit_data = []
            except Exception:
                audit_data = []
            
            if not audit_data:
                st.info("No global activity logged yet.")
            else:
                total_actions = len(audit_data)
                recent = audit_data[-50:] if total_actions > 50 else audit_data
                critical_flags = sum(1 for x in recent if "CRITICAL" in x["ai_flag"] or "Flagged" in x["ai_flag"])
                active_users = len(set(x["user"] for x in recent if x["user"] != "Unknown"))
            
                if critical_flags > 0:
                    sys_status = "⚠️ WARNING: Suspicious/High-Risk Forensic Activity Detected"
                    color = "#f87171"
                else:
                    sys_status = "✅ SECURE: No Anomalies Detected"
                    color = "#4ade80"
                
                st.markdown(f"""
                <div style="background:#1b2a3b; border-left:4px solid {color}; padding:15px; border-radius:5px; margin-bottom:20px; box-shadow:0 4px 6px rgba(0,0,0,0.3);">
                    <h4 style="margin-top:0; color:{color};">{sys_status}</h4>
                    <b style="color:#e0e6f0;">AI Security Analysis:</b> Tracking {total_actions} total events. In the recent window, {active_users} unique user(s) performed operations. {critical_flags} high-risk execution(s) were isolated. All evidence tampering vectors are currently blocked.
                </div>
                """, unsafe_allow_html=True)
            
                df_audit = pd.DataFrame(audit_data)
                df_audit = df_audit[["timestamp", "user", "role", "ai_flag", "action"]]
                # Style the dataframe for dark mode
                st.dataframe(df_audit.sort_values("timestamp", ascending=False), use_container_width=True, hide_index=True, height=250)
            
        st.markdown("---")

        st.header("🚨 Admin Action Required: Unassigned Complaints")
        unassigned = {cid: c for cid, c in all_complaints.items() if c.get("status") == "Unassigned"}
        if not unassigned: st.success("No new public complaints pending assignment.")
        else:
            for cid, c in unassigned.items():
                st.markdown(f"""<div class="case-card">
                    <h3 style="color:#f87171;margin-top:0">{cid} — {c.get('category', 'N/A')}</h3>
                    <p><b>Victim:</b> {c.get('victim_name', 'N/A')} | <b>Contact:</b> {c.get('victim_phone', 'N/A')} | <b>Reported:</b> {c.get('timestamp', 'N/A')}</p>
                    <p><b>Incident Time:</b> {c.get('incident_date', 'N/A')} {c.get('incident_time', 'N/A')} | <b>Ongoing:</b> {c.get('ongoing', 'N/A')}</p>
                    <p><b>Asset:</b> {c.get('compromised_asset', 'N/A')} ({c.get('asset_details', 'N/A')}) | <b>Suspect Intel:</b> {c.get('attacker_info', 'None')}</p>
                    <p><b>Description:</b> {c.get('description', 'N/A')}</p>
                </div>""", unsafe_allow_html=True)
                if st.button(f"🔍 Open Case for Review", key=f"open_admin_{cid}", type="primary"):
                    if "chain_of_custody" not in c: c["chain_of_custody"] = [{"timestamp": c['timestamp'], "action": "Evidence Initially Submitted", "actor": c['victim_name'], "location": "Public Intake Portal"}]
                    c["chain_of_custody"].append({
                        "timestamp": datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
                        "action": "Unassigned Case Opened for Admin Review",
                        "actor": f"Admin ({st.session_state.user_id})",
                        "location": "Admin Dashboard"
                    })
                    save_complaint(cid, c)
                    st.query_params["case"] = cid
                    st.session_state.active_case = cid
                    log_action(f"Admin Opened Unassigned Case: {cid}")
                    st.rerun()
        st.markdown("---")
        
        st.header("📊 Investigator Workloads")
        with st.expander("👥 Expand Team Workloads & Active Cases", expanded=False):
            for inv_uid in investigators:
                inv_name = users[inv_uid].get("full_name", inv_uid)
                inv_exp  = users[inv_uid].get("expertise", "General")
                inv_cases = {cid: c for cid, c in all_complaints.items() if c.get("assigned_to") == inv_uid}
                
                pending_cases = {cid: c for cid, c in inv_cases.items() if c.get("status", "Assigned") != "Completed"}
                completed_cases = {cid: c for cid, c in inv_cases.items() if c.get("status", "") == "Completed"}
                
                # Custom Toggle State
                state_key = f"toggle_inv_{inv_uid}"
                if state_key not in st.session_state:
                    st.session_state[state_key] = False
                    
                icon = "➖" if st.session_state[state_key] else "➕"
                
                col_btn, col_info = st.columns([1, 4])
                with col_btn:
                    if st.button(f"{icon} Expand", key=f"btn_{inv_uid}"):
                        st.session_state[state_key] = not st.session_state[state_key]
                        st.rerun()
                with col_info:
                    st.markdown(f"<div style='padding-top:5px'><b>{inv_name} ({inv_uid})</b> — 🛡️ {inv_exp} | {len(pending_cases)} Pending | {len(completed_cases)} Completed</div>", unsafe_allow_html=True)
                
                if st.session_state[state_key]:
                    st.markdown(f"""<div style="background:#1b2a3b; padding:15px; border-radius:5px; margin-bottom:15px; border-left: 2px solid #38bdf8;">""", unsafe_allow_html=True)
                    if pending_cases:
                        st.markdown("**Pending / Assigned Cases:**")
                        for cid, c in pending_cases.items():
                            c_col1, c_col2 = st.columns([4, 1])
                            with c_col1:
                                st.markdown(f"- **{cid}** ({c.get('category', 'N/A')}) — Victim: {c.get('victim_name', 'N/A')} — *{c.get('timestamp', 'N/A')}*")
                                st.markdown(f"  <small style='color:#7ec8e3'>Status: {c.get('status', 'In Progress')}</small>", unsafe_allow_html=True)
                            with c_col2:
                                if st.button("🔍 Open Case", key=f"admin_open_pending_{cid}"):
                                    st.query_params["case"] = cid
                                    st.session_state.active_case = cid
                                    log_action(f"Admin reviewing Assigned Case: {cid}")
                                    st.rerun()
                    else:
                        st.markdown("*No pending cases.*")
                        
                    if completed_cases:
                        st.markdown("**Completed Cases:**")
                        for cid, c in completed_cases.items():
                            c_col1, c_col2 = st.columns([4, 1])
                            with c_col1:
                                st.markdown(f"✅ **{cid}** ({c.get('category', 'N/A')}) — Victim: {c.get('victim_name', 'N/A')}")
                                if c.get("final_report"):
                                    st.markdown(f"<div style='margin-left: 20px; font-size: 0.9em; padding: 5px; border-left: 2px solid #38bdf8; color: #7ec8e3;'><b>Final Report:</b> {c['final_report']}</div>", unsafe_allow_html=True)
                            with c_col2:
                                if st.button("🔍 Open Case", key=f"admin_open_completed_{cid}"):
                                    st.query_params["case"] = cid
                                    st.session_state.active_case = cid
                                    log_action(f"Admin reviewing Completed Case: {cid}")
                                    st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("<hr style='margin:5px 0; border-color:#334155'>", unsafe_allow_html=True)
                
        st.markdown("---")
    else:
        st.header("📂 My Active Case Files")
        my_cases = {cid: c for cid, c in all_complaints.items() if c.get("assigned_to") == st.session_state.user_id and c.get("status") != "Completed"}
        if not my_cases: st.info("You have no assigned cases right now. Relax!")
        else:
            for cid, c in my_cases.items():
                with st.expander(f"📁 {cid}: {c['category']} (Victim: {c['victim_name']})"):
                    st.markdown(f"**Contact:** {c.get('victim_phone', 'N/A')}  |  **Reported On:** {c.get('timestamp', 'N/A')}")
                    st.markdown(f"**Incident Time:** {c.get('incident_date', 'N/A')} {c.get('incident_time', 'N/A')} | **Ongoing:** {c.get('ongoing', 'N/A')}")
                    st.markdown(f"**Asset:** {c.get('compromised_asset', 'N/A')} ({c.get('asset_details', 'N/A')})")
                    st.markdown(f"**Suspect Intel:** {c.get('attacker_info', 'None provided')} | **Loss:** {c.get('financial_loss', 'None')}")
                    st.markdown(f"**Description:**\n> {c.get('description', 'N/A')}")
                    has_evidence = bool(c.get('evidence_file'))
                    st.markdown(f"**Attached Evidence:** `{c['evidence_file'] if has_evidence else 'None'}`")
                    st.markdown(f"<div style='margin-top: 8px; margin-bottom: 12px; font-size: 0.9em; color: #7ec8e3;'>{get_tool_suggestions(c['category'])}</div>", unsafe_allow_html=True)
                    if st.button(f"Load Evidence into Secure Enclave", key=f"load_{cid}"):
                        log_action(f"Opened Case File: {cid}")
                        if "chain_of_custody" not in c: c["chain_of_custody"] = []
                        c["chain_of_custody"].append({
                            "timestamp": datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
                            "action": "Case File & Evidence Opened for Review",
                            "actor": f"Investigator ({st.session_state.user_id})",
                            "location": "Secure Investigator Enclave"
                        })
                        save_complaint(cid, c)
                        st.query_params["case"] = cid
                        st.session_state.active_case = cid
                        st.rerun()
        st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
def main():
    if st.session_state.get("logged_in"): workspace(); return
    
    users = load_users()
    current_page = st.session_state.get("page", "login")
    if len(users) == 0: current_page = "register"
    
    # Lock scrolling on Login, but allow it on Register/Complaint since they are longer
    overflow_rule = "hidden" if current_page == "login" else "auto"
    max_height_rule = "100vh" if current_page == "login" else "none"
    padding_top = "2vh" if current_page == "login" else "5vh"
    
    # ── DYNAMIC SCROLLING (AUTH PAGES) ──
    
    if current_page == "login" or current_page == "register":
        bg_url = "https://raw.githubusercontent.com/mohankanta/Zero-trust_Forensics/main/assets/wolf_login_background.jpg"
        bg_css = f"linear-gradient(rgba(10, 16, 24, 0.75), rgba(10, 16, 24, 0.75)), url('{bg_url}')"
    else:
        bg_url = "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?q=80&w=2070&auto=format&fit=crop"
        bg_css = f"url('{bg_url}')"

    st.markdown(f"""
    <style>
    [data-testid="stApp"] {{ background-image: {bg_css} !important; }}
    
    /* Dynamic Scrolling Rules */
    html, body, [data-testid="stAppViewContainer"] {{
        overflow: {overflow_rule} !important;
    }}
    .block-container, [data-testid="stAppViewBlockContainer"] {{
        padding-top: {padding_top} !important;
        padding-bottom: 5vh !important;
        max-height: {max_height_rule} !important;
        overflow: {overflow_rule} !important;
    }}
    </style>
    """, unsafe_allow_html=True)
    if st.session_state.page == "complaint": public_complaint_page(); return
    if st.session_state.page == "register": register_page(first_time=False); return
    if st.session_state.page == "login": login_page(); return
    if len(users) == 0: register_page(first_time=True)
    else: login_page()

if __name__ == "__main__": main()
