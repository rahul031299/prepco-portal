import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client
import json
from datetime import datetime, timezone



# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="PrepCo · IIM Nagpur",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────
# CUSTOM CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500;600&display=swap');

  html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
  }
  h1, h2, h3 {
    font-family: 'DM Serif Display', serif !important;
  }
  .hero {
    text-align: center;
    padding: 2.5rem 0 1.5rem;
  }
  .hero h1 {
    font-size: 2.6rem;
    margin-bottom: 0.3rem;
    color: #1a1a2e;
  }
  .hero p {
    color: #555;
    font-size: 1rem;
  }
  .quota-bar-wrap {
    background: #e8e8ef;
    border-radius: 8px;
    height: 8px;
    margin: 6px 0 2px;
    overflow: hidden;
  }
  .quota-bar-fill {
    height: 8px;
    border-radius: 8px;
    background: linear-gradient(90deg, #4f46e5, #7c3aed);
    transition: width 0.4s ease;
  }
  .tool-card {
    border: 1.5px solid #e2e2ef;
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    cursor: pointer;
    transition: border-color 0.15s, box-shadow 0.15s;
    background: white;
  }
  .tool-card:hover {
    border-color: #4f46e5;
    box-shadow: 0 4px 16px rgba(79,70,229,0.10);
  }
  .tool-card.selected {
    border-color: #4f46e5;
    background: #fafaff;
  }
  .chip {
    display: inline-block;
    background: #eef2ff;
    color: #4f46e5;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    margin-bottom: 6px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }
  .user-pill {
    display: flex;
    align-items: center;
    gap: 10px;
    background: #f4f4fb;
    border-radius: 40px;
    padding: 6px 14px 6px 8px;
    width: fit-content;
    margin: 0 auto 1.5rem;
    font-size: 13px;
    color: #444;
  }
  .user-pill img {
    width: 28px;
    height: 28px;
    border-radius: 50%;
  }
  .stButton > button {
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
  }
  .stButton > button[kind="primary"] {
    background: #4f46e5 !important;
    border: none !important;
  }
  .stButton > button[kind="primary"]:hover {
    background: #4338ca !important;
  }
  div[data-testid="stExpander"] {
    border-radius: 10px;
    border: 1px solid #e2e2ef;
  }
  .section-divider {
    border: none;
    border-top: 1px solid #eee;
    margin: 1.5rem 0;
  }
  .footer {
    text-align: center;
    font-size: 11px;
    color: #aaa;
    margin-top: 3rem;
    padding-bottom: 2rem;
  }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# CONFIG & SECRETS
# ──────────────────────────────────────────────
ALLOWED_DOMAIN      = st.secrets.get("ALLOWED_DOMAIN", "@iimn.ac.in")
LIFETIME_RUN_LIMIT  = int(st.secrets.get("LIFETIME_RUN_LIMIT", 25))
GEMINI_API_KEY      = st.secrets.get("GEMINI_API_KEY", "")
SUPABASE_URL        = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY        = st.secrets.get("SUPABASE_KEY", "")
GOOGLE_CLIENT_ID    = st.secrets.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = st.secrets.get("GOOGLE_CLIENT_SECRET", "")
ADMIN_EMAILS        = st.secrets.get("ADMIN_EMAILS", "").split(",")

# ──────────────────────────────────────────────
# SUPABASE CLIENT
# ──────────────────────────────────────────────
@st.cache_resource
def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def check_whitelist_and_get_user(email: str) -> dict:
    """Check if user exists in Supabase. If yes, let them in. If no, block them."""
    sb = get_supabase()
    res = sb.table("usage").select("*").eq("email", email).execute()
    
    if res.data:
        return res.data[0] # User found in backend!
    else:
        return None # User not found, block them.

def login_wall():
    """Show a simple email login UI and return (email, name, picture)."""
    # Initialize session state for login
    if "connected" not in st.session_state:
        st.session_state.connected = False

    # If already logged in, bypass the wall
    if st.session_state.connected:
        return st.session_state.email, st.session_state.name, ""

    # The Login Screen
    st.markdown("""
    <div class='hero'>
      <h1>🎯 PrepCo</h1>
      <p>IIM Nagpur · Placement Preparation Portal</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("Enter your approved IIMN email address to access the portal.")
        email_input = st.text_input("Email Address", placeholder="name@iimn.ac.in")
        
        if st.button("Access Portal", type="primary", use_container_width=True):
            if not email_input:
                st.warning("Please enter your email.")
                st.stop()
                
            email_clean = email_input.strip().lower()
            
            # Check the Supabase database
            with st.spinner("Verifying access..."):
                user_row = check_whitelist_and_get_user(email_clean)
                
            if user_row:
                # Login Success
                st.session_state.connected = True
                st.session_state.email = user_row["email"]
                st.session_state.name = user_row["name"]
                st.rerun()
            else:
                # Login Failed
                st.error(f"⛔ Access Denied: '{email_clean}' is not on the approved list. Contact the Preparatory Committee.")
                st.stop()

    st.markdown('<div class="footer">PrepCo · IIM Nagpur Preparatory Committee · 2024–25</div>', unsafe_allow_html=True)
    st.stop()
# ──────────────────────────────────────────────
# GEMINI HELPER
# ──────────────────────────────────────────────
def get_gemini_model():
    """Lean model initialization that skips cache and avoids unnecessary API pings."""
    import google.generativeai as genai
    import streamlit as st
    
    # 1. Force the app to read the secret directly every time, ignoring old caches
    current_api_key = st.secrets.get("GEMINI_API_KEY", "").strip()
    
    if not current_api_key:
        st.error("API Key is missing from Streamlit Secrets.")
        st.stop()
        
    genai.configure(api_key=current_api_key)
    
    # 2. Hardcode the exact model to prevent burning quota on list_models()
    model_name = "models/gemini-1.5 Flash"
    
    # Initialize and return
    model = genai.GenerativeModel(model_name)
    return model, model_name


def scrape_website(url: str) -> str | None:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(r.content, "html.parser")
        return soup.get_text(separator=" ", strip=True)[:10000]
    except Exception:
        return None

# ──────────────────────────────────────────────
# TOOL 1 — RESUME AGENT
# ──────────────────────────────────────────────
def tool_resume(user_row: dict):
    st.markdown("### 📝 Resume Agent")
    st.caption("Transform rough notes into IIMN-compliant CV bullet points.")

    user_text = st.text_area("Paste your rough experience here:", height=160,
                             placeholder="e.g. Worked on a market sizing project for a FMCG client, found that the market was $2B, presented to senior leadership...")

    if st.button("✨ Generate Bullet Points", type="primary", use_container_width=True):
        if not user_text.strip():
            st.warning("Please enter some experience text first.")
            return
        if user_row["runs"] >= LIFETIME_RUN_LIMIT:
            st.error(f"You've reached your lifetime limit of {LIFETIME_RUN_LIMIT} runs.")
            return

        with st.spinner("Optimising for IIMN guidelines..."):
            model, model_name = get_gemini_model()
            prompt = f"""
ROLE: IIM Nagpur Resume Optimization Engine.
TASK: Convert the input text into 3 high-impact resume bullet points.

--- IIM NAGPUR GUIDELINES (NON-NEGOTIABLE) ---
1. LENGTH: Max 14 words OR 120 characters per point. [Strict Constraint]
2. SYNTAX: Start with a strong POWER VERB. Use Active Voice. Use Past Tense.
3. STAR FRAMEWORK: Context (Situation) -> Action -> Result (Impact).
4. QUANTIFICATION: You MUST include numbers/metrics (%, $, time saved). If missing, use placeholders like [X]%.
5. FORBIDDEN WORDS: Never use 'worked on', 'helped', 'responsible for', 'managed team' (unless specific).

--- TRAINING EXAMPLES (FROM OFFICIAL GUIDE) ---
* BAD: "Worked on a sales project."
* GOOD (Sales): "Converted 30+ B2B leads via cold calls, achieving 20% monthly revenue growth."
* GOOD (Marketing): "Boosted Meta Ads ROAS by 2.1x using A/B tested creatives and landing pages."
* GOOD (Consulting): "Analysed 5 client portfolios, recommended 3 strategy shifts, boosting efficiency by 12%."
* GOOD (Ops): "Automated purchase order flow, reducing manual effort by 8 hours/week using workflow tools."
* GOOD (Finance): "Reconciled financial data of 3 quarters, identifying errors worth 5L in reporting."

--- USER INPUT ---
{user_text}

--- OUTPUT INSTRUCTIONS ---
Provide 3 variations. Ensure every point is under 120 characters.

1. **Consulting/Strategy Style** (Focus: Efficiency, Analysis, Recommendations)
2. **Finance/Analytical Style** (Focus: Accuracy, Audit, Numbers, Budget)
3. **General Mgmt/Ops Style** (Focus: Leadership, Execution, Timelines, Stakeholders)
"""
            try:
                response = model.generate_content(prompt)
                runs = increment_runs(user_row["email"])
                user_row["runs"] = runs

                st.success(f"✅ Points generated following IIMN Prep Comm Guidelines. — Model: `{model_name}`")
                st.markdown(response.text)
                with st.expander("Copy raw text"):
                    st.text_area("", response.text, height=200)
            except Exception as e:
                if "429" in str(e):
                    st.error("⚠️ Rate limit hit — please wait 60 seconds and try again.")
                else:
                    st.error(f"Error: {e}")

# ──────────────────────────────────────────────
# TOOL 2 — INTERVIEW INTEL AGENT
# ──────────────────────────────────────────────
def tool_interview(user_row: dict):
    st.markdown("### 🎯 Interview Intel Agent")
    st.caption("Generate a 5-minute research dossier for your upcoming interview.")

    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input("Company Name *", placeholder="e.g., McKinsey & Company")
    with col2:
        job_role = st.text_input("Job Title / Role *", placeholder="e.g., Summer Associate")

    website_url = st.text_input("Company Website URL (optional, improves accuracy)",
                                placeholder="e.g., https://www.mckinsey.com")

    if st.button("🔍 Generate Research Briefing", type="primary", use_container_width=True):
        if not company_name or not job_role:
            st.warning("Please enter both the Company Name and the Job Role.")
            return
        if user_row["runs"] >= LIFETIME_RUN_LIMIT:
            st.error(f"You've reached your lifetime limit of {LIFETIME_RUN_LIMIT} runs.")
            return

        with st.spinner(f"Deploying agents to research {company_name}..."):
            live_context = ""
            if website_url:
                st.toast("Scraping live website data...")
                scraped = scrape_website(website_url)
                if scraped:
                    live_context = f"\n\n--- LIVE WEBSITE DATA FROM {website_url} ---\n{scraped}\n---\nUse the live data above to make your insights highly accurate."
                else:
                    st.warning("⚠️ Could not read the website. Proceeding with AI knowledge.")

            model, model_name = get_gemini_model()
            prompt = f"""
Act as an elite corporate intelligence researcher and MBA Career Coach. Generate a comprehensive "5-Minute Interview Dossier" for a candidate interviewing at {company_name} for the {job_role} position.
{live_context}

CRITICAL ACCURACY & ENTITY CHECK:
Before generating the dossier, verify the exact identity of '{company_name}'.
- If multiple companies share this name, use the '{job_role}' context and website data to identify the correct entity.
- Ground ALL facts strictly in reality. Do NOT hallucinate financial metrics.
- If a metric is unknown, state "Data not publicly disclosed".

STRICT FORMATTING RULES:
- Target length: 600-800 words (5-minute read).
- Use bullet points with bolded keywords for easy scanning.
- NO long, blocky paragraphs.
- MBA-level strategic insights, not surface-level facts.

STRUCTURE THE DOSSIER EXACTLY AS FOLLOWS:

### 🏢 1. The Executive Brief (Company DNA)
* **Verified Entity:** [Full legal name, industry, HQ]
* **Mission & Vision:** [2-3 sentences]
* **Culture & Values:** [3 detailed bullets]

### 💰 2. The Economic Engine (Business Model)
* **Revenue Streams:** [3-4 detailed bullets]
* **Financial Posture:** [2 bullets — growth, profitability, cost-cutting?]

### ⚔️ 3. The Competitive Moat (Market Landscape)
* **Key Competitors:** [Top 3-4 + how {company_name} differentiates]
* **Unique Value Proposition:** [Their 'unfair advantage']

### 📰 4. Strategic Imperatives (Recent News & Headwinds)
* **Recent Wins:** [2-3 bullets, last 12-18 months]
* **Current Challenges/Headwinds:** [2-3 bullets]

### 🎯 5. The {job_role} Playbook
* **Core Competencies:** [3 specific skills they will test]
* **How to Add Value:** [2 concrete ways to solve the company's current challenges]

### 🎤 6. "Drop the Mic" Questions (To ask the Interviewer)
3 strategic MBA-level questions with rationale.
* **Question 1:** [Strategic question about company direction]
  * *Why this works:* [Rationale]
* **Question 2:** [Role-specific or operational question]
  * *Why this works:* [Rationale]
* **Question 3:** [Culture, team-dynamics, or success-metric question]
  * *Why this works:* [Rationale]
"""
            try:
                response = model.generate_content(prompt)
                runs = increment_runs(user_row["email"])
                user_row["runs"] = runs

                st.success(f"✅ Briefing generated! — Model: `{model_name}`")
                st.markdown("---")
                st.markdown(response.text)
                with st.expander("Copy raw text"):
                    st.text_area("", response.text, height=300)
            except Exception as e:
                if "429" in str(e):
                    st.error("⚠️ Rate limit hit — please wait 60 seconds and try again.")
                else:
                    st.error(f"Error: {e}")

# ──────────────────────────────────────────────
# ADMIN DASHBOARD
# ──────────────────────────────────────────────
def admin_dashboard():
    st.markdown("### 🛡️ Admin Dashboard")
    st.caption("Committee view — usage analytics across all students.")

    data = get_all_usage()
    if not data:
        st.info("No usage data yet.")
        return

    total_runs  = sum(d["runs"] for d in data)
    active_users = sum(1 for d in data if d["runs"] > 0)
    top_user    = data[0] if data else {}

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total runs", total_runs)
    c2.metric("Students registered", len(data))
    c3.metric("Active users", active_users)
    c4.metric("Top user runs", top_user.get("runs", 0))

    st.markdown("#### Usage per student")
    for row in data:
        pct = min(row["runs"] / LIFETIME_RUN_LIMIT, 1.0)
        col_a, col_b = st.columns([4, 1])
        with col_a:
            st.markdown(f"**{row['name']}** `{row['email']}`")
            st.markdown(
                f'<div class="quota-bar-wrap"><div class="quota-bar-fill" style="width:{pct*100:.0f}%"></div></div>',
                unsafe_allow_html=True
            )
        with col_b:
            st.markdown(f"**{row['runs']}** / {LIFETIME_RUN_LIMIT}")
        st.markdown("")

    if st.button("⬇️ Export as JSON"):
        st.download_button("Download usage.json", json.dumps(data, indent=2, default=str),
                           "prepco_usage.json", "application/json")

# ──────────────────────────────────────────────
# MAIN APP
# ──────────────────────────────────────────────
def main():
    # ── Auth ──────────────────────────────────
    email, name, picture = login_wall()

    # ── Load user row ─────────────────
    if SUPABASE_URL and SUPABASE_KEY:
        user_row = check_whitelist_and_get_user(email)
    else:
        st.error("Supabase database is not connected. Whitelist offline.")
        st.stop()

    runs_left = LIFETIME_RUN_LIMIT - user_row["runs"]

    # ... [Keep your Header, User Pill, and Quota Bar code exactly the same] ...    # ── Header ────────────────────────────────
    st.markdown("""
    <div class='hero'>
      <h1>🎯 PrepCo</h1>
      <p>IIM Nagpur · Placement Preparation Portal</p>
    </div>
    """, unsafe_allow_html=True)

    # User pill
    pill_img = f'<img src="{picture}" />' if picture else ""
    st.markdown(f"""
    <div class='user-pill'>
      {pill_img}
      <span>{name} &nbsp;·&nbsp; {email}</span>
    </div>
    """, unsafe_allow_html=True)

    # Quota bar
    pct = max(0, min(runs_left / LIFETIME_RUN_LIMIT, 1.0))
    color = "#4f46e5" if pct > 0.4 else ("#f59e0b" if pct > 0.15 else "#ef4444")
    st.markdown(f"""
    <div style="max-width:480px;margin:0 auto 1.5rem;text-align:center">
      <div style="font-size:12px;color:#888;margin-bottom:4px">
        Runs remaining: <strong>{runs_left}</strong> of {LIFETIME_RUN_LIMIT}
      </div>
      <div class="quota-bar-wrap">
        <div class="quota-bar-fill" style="width:{pct*100:.0f}%;background:{color}"></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Logout ────────────────────────────────
    with st.sidebar:
        st.markdown(f"**{name}**")
        st.caption(email)
        st.markdown("---")
        
        # New simple logout button
        if st.button("🚪 Logout"):
            st.session_state.connected = False
            st.rerun()
            
        if email.strip() in [a.strip() for a in ADMIN_EMAILS if a.strip()]:
            if st.button("🛡️ Admin Dashboard"):
                st.session_state["page"] = "admin"
        if st.button("🏠 Home"):
            st.session_state["page"] = "home"

    # ... [Keep the rest of your main() function exactly the same] ...

    # ── Admin page ────────────────────────────
    if st.session_state.get("page") == "admin":
        if email.strip() in [a.strip() for a in ADMIN_EMAILS if a.strip()]:
            admin_dashboard()
        else:
            st.error("Access denied.")
        return

    # ── Tool selector ─────────────────────────
    st.markdown("#### Choose a tool")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝  Resume Agent\n\nTransform rough notes into IIMN-compliant CV bullets",
                     use_container_width=True):
            st.session_state["tool"] = "resume"
    with col2:
        if st.button("🎯  Interview Intel\n\nGenerate a 5-min company research dossier",
                     use_container_width=True):
            st.session_state["tool"] = "interview"

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── Render selected tool ──────────────────
    tool = st.session_state.get("tool", "resume")
    if tool == "resume":
        tool_resume(user_row)
    else:
        tool_interview(user_row)

    # ── Footer ────────────────────────────────
    st.markdown('<div class="footer">PrepCo · IIM Nagpur Preparatory Committee · 2025–27 · Built with Streamlit</div>',
                unsafe_allow_html=True)


if __name__ == "__main__":
    main()
