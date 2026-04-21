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
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# CUSTOM CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

  /* Base App Styling & Typography */
  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: #0f172a;
  }
  
  /* Make the main app container have a subtle mesh-like gradient background */
  .stApp {
    background: radial-gradient(circle at top left, #f3e8ff 0%, #f8fafc 30%, #f8fafc 70%, #e0e7ff 100%);
  }

  h1, h2, h3, h4, h5 {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
  }
  
  /* Hero Section */
  .hero {
    text-align: center;
    padding: 0.5rem 0 0.5rem;
    animation: fadeInDown 0.8s ease-out;
  }
  .hero h1 {
    font-size: 2.2rem;
    margin-bottom: 0.2rem;
    background: linear-gradient(135deg, #4f46e5, #d946ef);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: inline-block;
  }
  .hero p {
    color: #64748b;
    font-size: 0.95rem;
    font-weight: 500;
    letter-spacing: 0.02em;
    margin-bottom: 0.5rem;
  }

  /* Quota Bar */
  .quota-bar-wrap {
    background: rgba(226, 232, 240, 0.6);
    border-radius: 999px;
    height: 10px;
    margin: 8px 0 4px;
    overflow: hidden;
    backdrop-filter: blur(4px);
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
  }
  .quota-bar-fill {
    height: 10px;
    border-radius: 999px;
    background: linear-gradient(90deg, #4f46e5, #8b5cf6, #d946ef);
    transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 0 10px rgba(139, 92, 246, 0.5);
  }

  /* Buttons - Premium Styling */
  .stButton > button {
    border-radius: 12px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.01em !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    border: 1px solid rgba(226, 232, 240, 0.8) !important;
    background: rgba(255, 255, 255, 0.7) !important;
    color: #334155 !important;
    backdrop-filter: blur(10px) !important;
    box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04) !important;
  }
  
  .stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 16px rgba(15, 23, 42, 0.08) !important;
    border-color: #cbd5e1 !important;
  }

  .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    border: none !important;
    color: white !important;
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3) !important;
  }
  
  .stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #4338ca, #6d28d9) !important;
    box-shadow: 0 8px 20px rgba(79, 70, 229, 0.4) !important;
  }

  /* Inputs and Text Areas - Glassmorphism */
  .stTextInput > div > div > input, 
  .stTextArea > div > div > textarea {
    border-radius: 12px !important;
    border: 1px solid rgba(203, 213, 225, 0.6) !important;
    background: rgba(255, 255, 255, 0.6) !important;
    backdrop-filter: blur(8px) !important;
    padding: 0.75rem 1rem !important;
    font-size: 1rem !important;
    transition: all 0.2s ease !important;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.02) !important;
  }
  
  .stTextInput > div > div > input:focus, 
  .stTextArea > div > div > textarea:focus {
    border-color: #8b5cf6 !important;
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2), inset 0 2px 4px rgba(0,0,0,0.02) !important;
    background: rgba(255, 255, 255, 0.9) !important;
  }

  /* User Pill */
  .user-pill {
    display: flex;
    align-items: center;
    gap: 12px;
    background: rgba(255, 255, 255, 0.7);
    border: 1px solid rgba(226, 232, 240, 0.8);
    backdrop-filter: blur(10px);
    border-radius: 40px;
    padding: 6px 14px 6px 8px;
    width: fit-content;
    margin: 0 auto 0.75rem;
    font-size: 14px;
    font-weight: 500;
    color: #475569;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }
  .user-pill:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08);
  }
  .user-pill img {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    border: 2px solid white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }

  /* Expanders */
  div[data-testid="stExpander"] {
    border-radius: 12px !important;
    border: 1px solid rgba(226, 232, 240, 0.8) !important;
    background: rgba(255, 255, 255, 0.5) !important;
    backdrop-filter: blur(8px) !important;
    overflow: hidden !important;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.02) !important;
  }
  div[data-testid="stExpander"] summary {
    font-weight: 600 !important;
    color: #1e293b !important;
  }

  /* Information / Alert boxes */
  .stAlert {
    border-radius: 12px !important;
    border: none !important;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04) !important;
  }

  /* Custom Dividers */
  .section-divider {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(203, 213, 225, 0.8), transparent);
    margin: 1rem 0 1.5rem;
  }

  /* Footer */
  .footer {
    text-align: center;
    font-size: 13px;
    color: #94a3b8;
    margin-top: 4rem;
    padding-bottom: 2rem;
    font-weight: 500;
  }

  /* Sidebar tweaks */
  [data-testid="stSidebar"] {
    background-color: rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(10px);
  }

  /* Animations */
  @keyframes fadeInDown {
    from { opacity: 0; transform: translateY(-20px); }
    to { opacity: 1; transform: translateY(0); }
  }
  
  /* Tool Card fixes */
  .tool-card {
    border: 1px solid rgba(226, 232, 240, 0.8);
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    cursor: pointer;
    transition: all 0.2s ease;
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(10px);
  }
  .tool-card:hover {
    border-color: #8b5cf6;
    box-shadow: 0 8px 24px rgba(139, 92, 246, 0.15);
    transform: translateY(-2px);
  }
  .chip {
    display: inline-block;
    background: rgba(238, 242, 255, 0.8);
    color: #4f46e5;
    font-size: 11px;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 20px;
    margin-bottom: 8px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    backdrop-filter: blur(4px);
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
DRIVE_FOLDER_ID     = st.secrets.get("DRIVE_FOLDER_ID", "")
ATS_WEBSITE_URL     = st.secrets.get("ATS_WEBSITE_URL", "https://resumeframe.com/")

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


def get_or_create_user(email: str, name: str) -> dict:
    """Return usage row for this user, creating it if absent."""
    sb = get_supabase()
    res = sb.table("usage").select("*").eq("email", email).execute()
    if res.data:
        return res.data[0]
    new_row = {"email": email, "name": name, "runs": 0, "created_at": datetime.now(timezone.utc).isoformat()}
    sb.table("usage").insert(new_row).execute()
    return {**new_row, "runs": 0}


def increment_runs(email: str) -> int:
    """Increment run count and return new total."""
    sb = get_supabase()
    res = sb.table("usage").select("runs").eq("email", email).execute()
    current = res.data[0]["runs"] if res.data else 0
    new_val = current + 1
    sb.table("usage").update({"runs": new_val, "last_run": datetime.now(timezone.utc).isoformat()}).eq("email", email).execute()
    return new_val


def get_all_usage() -> list:
    """Get all user records for admin dashboard."""
    sb = get_supabase()
    res = sb.table("usage").select("*").order("runs", desc=True).execute()
    return res.data or []

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
    """Auto-detect the best available Gemini model."""
    import google.generativeai as genai
    import streamlit as st
    
    # 1. Get the API key
    current_api_key = st.secrets.get("GEMINI_API_KEY", "").strip()
    
    if not current_api_key:
        st.error("API Key is missing from Streamlit Secrets.")
        st.stop()
        
    genai.configure(api_key=current_api_key)
    
    # 2. Try a priority list of model names
    model_names_to_try = [
        "gemini-2.5-flash-lite"
    ]
    
    # 3. Try each model until one works
    for model_name in model_names_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            # Quick test to see if it actually works
            return model, model_name
        except Exception:
            continue
    
    # 4. If nothing works, try listing models
    try:
        available = [m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
        if available:
            model_name = available[0]
            model = genai.GenerativeModel(model_name)
            return model, model_name
    except Exception as e:
        st.error(f"Could not find any working Gemini model. Error: {e}")
        st.stop()
    
    st.error("No compatible Gemini models found. Please check your API key.")
    st.stop()


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
            prompt = f""" Here is an upgraded, comprehensive version of your prompt. It directly integrates the specific STAR domain examples from the PrepCo guidelines and categorizes the power verbs to ensure the generated variations are highly targeted and impactful for the 700 students utilizing the optimization tool. 

You can copy and paste this directly into your system.

***

### Improved Resume Optimization Prompt

```text
ROLE: IIM Nagpur Resume Optimization Engine.
TASK: Convert the input text into 3 high-impact resume bullet points tailored to specific domains.

--- IIM NAGPUR PREPCO GUIDELINES (NON-NEGOTIABLE) ---
1. [cite_start]LENGTH: Max 14 words OR 120 characters per point[cite: 452]. [Strict Constraint]
2. [cite_start]SYNTAX: Begin each bullet point with a strong action verb[cite: 453]. [cite_start]Use Active voice[cite: 462]. [cite_start]Prefer past tense, unless it's an ongoing responsibility[cite: 463].
3. [cite_start]STAR FRAMEWORK: Situation (Context) -> Task -> Action -> Result (Impact)[cite: 455, 471, 472, 474, 475].
4. [cite_start]QUANTIFICATION: You MUST include quantifiable outcomes: numbers, %, timelines, growth metrics[cite: 454]. If missing, use placeholders like [X]%. 
5. [cite_start]CLARITY: Each point must be crisp and result-oriented[cite: 462]. [cite_start]A recruiter should understand the impact in 5 seconds[cite: 464].
6. [cite_start]FORBIDDEN WORDS: Do not write generic or vague points like ""worked on a project"" or ""helped the team""[cite: 456].

--- HIGH-IMPACT POWER VERBS TO UTILIZE ---
* [cite_start]For Consulting/Strategy: Analyzed [cite: 262][cite_start], Formulated [cite: 279][cite_start], Recommended [cite: 270][cite_start], Streamlined [cite: 256][cite_start], Evaluated [cite: 11][cite_start], Diagnosed[cite: 264].
* [cite_start]For Finance/Analytical: Reconciled [cite: 303][cite_start], Audited [cite: 315][cite_start], Appraised [cite: 313][cite_start], Calculated [cite: 318][cite_start], Forecasted [cite: 12][cite_start], Projected[cite: 287].
* [cite_start]For General Mgmt/Ops: Automated [cite: 558][cite_start], Orchestrated [cite: 223][cite_start], Executed [cite: 80][cite_start], Supervised [cite: 130][cite_start], Spearheaded [cite: 157][cite_start], Accelerated[cite: 153].

--- TRAINING EXAMPLES (FROM OFFICIAL GUIDE) ---
* [cite_start]BAD: ""Worked on a project."" [cite: 456]
* [cite_start]GOOD (Sales): ""Converted 30+ B2B leads via cold calls, achieving 20% monthly revenue growth""[cite: 484].
* [cite_start]GOOD (Marketing): ""Boosted Meta Ads ROAS by 2.1x using A/B tested creatives and landing pages""[cite: 505].
* [cite_start]GOOD (Consulting): ""Analysed 5 client portfolios, recommended 3 strategy shifts, boosting efficiency by 12%""[cite: 521].
* [cite_start]GOOD (Finance): ""Reconciled financial data of 3 quarters, identifying errors worth ₹5L in reporting""[cite: 539].
* [cite_start]GOOD (Operations): ""Automated purchase order flow, reducing manual effort by 8 hours/week using workflow tools""[cite: 558].
* [cite_start]GOOD (HR): ""Built an HR dashboard for attrition tracking, reducing reporting time by 40%""[cite: 585].
* [cite_start]GOOD (Gen Management): ""Led cross-functional team of 8 to execute CSR campaign impacting 500+ rural students""[cite: 594].

--- USER INPUT ---
{user_text}

--- OUTPUT INSTRUCTIONS ---
Provide 3 variations based on the user input. [cite_start]Ensure EVERY point is strictly under 14 words OR 120 characters[cite: 452]. 
 
1. **Consulting/Strategy Style** (Focus: Efficiency, Analysis, Recommendations. Use Problem-Solving Verbs).
2. **Finance/Analytical Style** (Focus: Accuracy, Audit, Numbers, Budget. Use Quantitative Verbs).
3. **General Mgmt/Ops Style** (Focus: Leadership, Execution, Timelines, Stakeholders. Use Leading & Getting Results Verbs).
```
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
 Act as an elite corporate intelligence researcher and MBA Career Coach. Your task is to generate a comprehensive but highly scannable "5-Minute Interview Dossier" for a candidate interviewing at {company_name} for the {job_role} position.
                {live_context}
                
                CRITICAL ACCURACY & ENTITY CHECK:
                Before generating the dossier, you MUST verify the exact identity of '{company_name}'. 
                - If multiple companies share this name, use the '{job_role}' context and the provided website data to identify the correct corporate entity.
                - Ground ALL facts (revenue, competitors, news) strictly in reality. Do NOT hallucinate or guess financial metrics.
                - If a specific metric or news item is unknown, state "Data not publicly disclosed" rather than making it up.
                
                STRICT FORMATTING RULES:
                - Target length: Detailed enough for a 5-minute read (approx. 600-800 words).
                - Use bullet points with bolded keywords for easy scanning.
                - NO long, blocky paragraphs. 
                - Focus on MBA-level strategic insights rather than generic surface-level facts.
                
                STRUCTURE THE DOSSIER EXACTLY AS FOLLOWS:
                
                ### 🏢 1. The Executive Brief (Company DNA)
                * **Verified Entity:** [State the full legal name, industry, and HQ location of the company you are profiling to prove you selected the right one]
                * **Mission & Vision:** [2-3 sentences explaining their core purpose and long-term goal]
                * **Culture & Values:** [3 detailed bullet points on their management style and what behaviors they actually reward]
                
                ### 💰 2. The Economic Engine (Business Model)
                * **Revenue Streams:** [Break down exactly how they make money in 3-4 detailed bullets. Mention core products/services and target demographics.]
                * **Financial Posture:** [Explain their current financial narrative in 2 bullets. Are they prioritizing growth, profitability, cutting costs, or expanding?]
                
                ### ⚔️ 3. The Competitive Moat (Market Landscape)
                * **Key Competitors:** [List top 3-4 competitors and exactly how {company_name} differentiates itself from them]
                * **Unique Value Proposition:** [Detail their 'unfair advantage'—e.g., distribution network, proprietary tech, brand loyalty]
                
                ### 📰 4. Strategic Imperatives (Recent News & Headwinds)
                * **Recent Wins:** [2-3 bullet points on major launches, acquisitions, or positive news from the last 12-18 months]
                * **Current Challenges/Headwinds:** [2-3 bullet points on their biggest threats right now—e.g., regulatory hurdles, supply chain, new entrants, AI disruption]
                
                ### 🎯 5. The {job_role} Playbook
                * **Core Competencies:** [3 specific technical or soft skills they will heavily test for this specific role]
                * **How to Add Value:** [2 concrete ways a person in this role can help solve the company's current challenges mentioned above]
                
                ### 🎤 6. "Drop the Mic" Questions (To ask the Interviewer)
                Provide 3 highly strategic, MBA-level questions for the candidate to ask at the end of the interview. For each, include a brief rationale.
                * **Question 1:** [Strategic question about company direction or market shifts]
                  * *Why this works:* [Brief rationale on why this impresses the panel]
                * **Question 2:** [Role-specific or operational question]
                  * *Why this works:* [Brief rationale]
                * **Question 3:** [Culture, team-dynamics, or success-metric question]
                  * *Why this works:* [Brief rationale]
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
# TOOL 3 — PREP DOCUMENTS (GOOGLE DRIVE)
# ──────────────────────────────────────────────
def tool_drive_documents():
    import streamlit.components.v1 as components
    import re
    st.markdown("### 📁 Prep Documents")
    st.caption("Access shared preparation materials from Google Drive directly.")
    
    if not DRIVE_FOLDER_ID:
        st.warning("⚠️ The Drive Folder ID is not configured in the secrets yet. Please add `DRIVE_FOLDER_ID` to your `.streamlit/secrets.toml`.")
        return
        
    # Extract ID just in case the user pasted a full URL
    folder_id = DRIVE_FOLDER_ID.strip()
    match = re.search(r'folders/([a-zA-Z0-9_-]+)', folder_id)
    if match:
        folder_id = match.group(1)
    else:
        match = re.search(r'id=([a-zA-Z0-9_-]+)', folder_id)
        if match:
            folder_id = match.group(1)
            
    with st.spinner("Loading Drive folder..."):
        drive_url = f"https://drive.google.com/embeddedfolderview?id={folder_id}#grid"
        components.iframe(drive_url, width=None, height=600, scrolling=True)

# ──────────────────────────────────────────────
# TOOL 4 — ATS SCORE CHECKER
# ──────────────────────────────────────────────
def tool_ats_checker():
    st.markdown("### 🤖 ATS Score Checker")
    st.caption("Check your resume against modern ATS screening tools.")
    
    st.info("To ensure your resume passes automated screening, use our recommended ATS checker tool below. This will open securely in a new tab.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.link_button("🚀 Launch ATS Checker", url=ATS_WEBSITE_URL, type="primary", use_container_width=True)
        st.caption(f"<div style='text-align: center;'>Opens {ATS_WEBSITE_URL}</div>", unsafe_allow_html=True)

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
    <div style="max-width:480px;margin:0 auto 0.5rem;text-align:center">
      <div style="font-size:12px;color:#888;margin-bottom:4px">
        Runs remaining: <strong>{runs_left}</strong> of {LIFETIME_RUN_LIMIT}
      </div>
      <div class="quota-bar-wrap">
        <div class="quota-bar-fill" style="width:{pct*100:.0f}%;background:{color}"></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Sidebar Navigation ────────────────────
    with st.sidebar:
        st.markdown("### 🧰 Tools Menu")
        if st.button("📝 Resume Agent", use_container_width=True):
            st.session_state["tool"] = "resume"
            st.session_state["page"] = "home"
        if st.button("🎯 Interview Intel", use_container_width=True):
            st.session_state["tool"] = "interview"
            st.session_state["page"] = "home"
        if st.button("📁 Prep Documents", use_container_width=True):
            st.session_state["tool"] = "drive"
            st.session_state["page"] = "home"
        if st.button("🤖 ATS Score Checker", use_container_width=True):
            st.session_state["tool"] = "ats"
            st.session_state["page"] = "home"
            
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown(f"**{name}**")
        st.caption(email)
        
        if email.strip() in [a.strip() for a in ADMIN_EMAILS if a.strip()]:
            if st.button("🛡️ Admin Dashboard", use_container_width=True):
                st.session_state["page"] = "admin"
                
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.connected = False
            st.rerun()

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── Admin page ────────────────────────────
    if st.session_state.get("page") == "admin":
        if email.strip() in [a.strip() for a in ADMIN_EMAILS if a.strip()]:
            admin_dashboard()
        else:
            st.error("Access denied.")
        return

    # ── Render selected tool ──────────────────
    tool = st.session_state.get("tool", "resume")
    if tool == "resume":
        tool_resume(user_row)
    elif tool == "interview":
        tool_interview(user_row)
    elif tool == "drive":
        tool_drive_documents()
    elif tool == "ats":
        tool_ats_checker()

    # ── Footer ────────────────────────────────
    st.markdown('<div class="footer">PrepCo · IIM Nagpur Preparatory Committee · 2025–27 · Built with Streamlit</div>',
                unsafe_allow_html=True)


if __name__ == "__main__":
    main()
