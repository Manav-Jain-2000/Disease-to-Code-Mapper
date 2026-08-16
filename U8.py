import streamlit as st
import pandas as pd
import time
import random
from scripts.icd_10_cm_search_bar import icd_10_cm_search_bar
from scripts.icd_10_pcs_search_bar import search_icd10_pcs_search_bar
from scripts.cpt_search_bar import cpt_search_bar
from scripts.icd_10_cm_search_bar import ICDcodeNode
from scripts.batch_search import batch_search_function
# -----------------------------------------------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="MediCode | Cognitio Analytics",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)
df_master = pd.read_excel("ICD_10_CM_Complete_Data.xlsx")
# -----------------------------------------------------------------------------
# CUSTOM STYLING (BLUE / CLINICAL THEME)
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
    /* Global Font & Colors */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&family=Inter:wght@400;500&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3 {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 700;
        color: #0f172a;
    }
    
    /* Theme Colors (Retaining Primary for Main Content) */
    :root {
        --primary: #c8306d;      /* Brand Color (Magenta) */
        --primary-dark: #9d1568; 
        --bg-soft: #fdf2f8;      /* Pink 50 */
        --text-main: #0f172a;    /* Slate 900 */
        --text-muted: #64748b;   /* Slate 500 */
    }

    /* Sidebar Styling - UPDATED COLOR: #2596be */
    section[data-testid="stSidebar"] {
        background-color: #063970; /* Updated Sidebar Color to Blue */
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] div {
        color: #ffffff !important; 
    }
    section[data-testid="stSidebar"] .stRadio label {
        color: #ffffff !important;
    }

    /* Sidebar Navigation Buttons */
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] {
        gap: 8px; /* Vertical spacing between buttons */
    }

    section[data-testid="stSidebar"] .stRadio label {
        background-color: rgba(255, 255, 255, 0.1); /* Subtle white background */
        border-radius: 8px;
        padding: 10px 15px;
        transition: background-color 0.2s;
        border: 1px solid rgba(255, 255, 255, 0.2);
        font-weight: 500 !important;
    }

    /* Selected state */
    section[data-testid="stSidebar"] .stRadio label[data-testid="stCheckableElement-checked"] {
        background-color: #ffffff; /* White background when selected */
        border-color: #ffffff;
        font-weight: 700 !important;
    }

    section[data-testid="stSidebar"] .stRadio label[data-testid="stCheckableElement-checked"] p {
        color: #2596be !important; /* Blue text color when selected (matches sidebar BG) */
    }

    /* Hide the default radio dot */
    section[data-testid="stSidebar"] .stRadio [data-testid="stCheckableElement-empty"],
    section[data-testid="stSidebar"] .stRadio [data-testid="stCheckableElement-checked"] {
        display: none;
    }

    /* Buttons (Main Content) */
    .stButton > button {
        background-color: var(--primary);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background-color: var(--primary-dark);
        box-shadow: 0 4px 12px rgba(219, 39, 119, 0.25);
        color: white;
    }

    /* Cards / Containers */
    .metric-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-main);
    }
    .metric-label {
        color: var(--text-muted);
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Hero Section Card */
    .hero-card {
        background-color: var(--primary); /* Keep brand color for hero */
        color: white;
        border-radius: 16px;
        padding: 3rem;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    .hero-card h1 {
        color: white !important;
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    .hero-card p {
        font-size: 1.1rem;
        opacity: 0.9;
        margin-bottom: 2rem;
        max-width: 800px;
    }

    /* Custom Result Card */
    .result-card {
        border-left: 4px solid var(--primary);
        background: white;
        padding: 1rem;
        margin-bottom: 1rem;
        border-radius: 0 8px 8px 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# MOCK DATA
# -----------------------------------------------------------------------------
MOCK_CODES = [
    {"code": "E11.9", "description": "Type 2 diabetes mellitus without complications", "system": "ICD-10-CM", "confidence": 0.98},
    {"code": "I10", "description": "Essential (primary) hypertension", "system": "ICD-10-CM", "confidence": 0.95},
    {"code": "J45.909", "description": "Unspecified asthma, uncomplicated", "system": "ICD-10-CM", "confidence": 0.92},
    {"code": "99213", "description": "Office/outpatient visit, est patient", "system": "CPT", "confidence": 0.89},
    {"code": "M54.5", "description": "Low back pain", "system": "ICD-10-CM", "confidence": 0.85},
    {"code": "R05", "description": "Cough", "system": "ICD-10-CM", "confidence": 0.99},
    {"code": "02HV33Z", "description": "Insertion of Infusion Device into Superior Vena Cava, Percutaneous Approach", "system": "ICD-10-PCS", "confidence": 0.93},
]

# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
with st.sidebar:
    # LOGO HANDLING - WIDTH INCREASED
    st.image(r"cognitio_logo.png", width=280)
    
    st.markdown("### Disease to Code Mapper") 
    st.caption("Enterprise Clinical Coding Platform")
    
    st.markdown("---")
    
    # Navigation uses the new CSS styling for box buttons
    page = st.radio(
        "Navigation",
        ["Dashboard", "Interactive Mapping", "Batch Processing", "Clinical NLP"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    with st.expander("System Status", expanded=True):
        st.markdown("🟢 **System Online**")
        st.caption("v2.4.0 • Enterprise Edition")

# -----------------------------------------------------------------------------
# PAGES
# -----------------------------------------------------------------------------

def show_dashboard():
    # Hero Section with Custom HTML/CSS
    st.markdown("""
        <div class="hero-card">
            <h1>Welcome to Disease to Code Mapper</h1>
            <p>Your intelligent partner for standardized clinical coding. Process single terms, batch files, or unstructured clinical notes with high-confidence AI predictions.</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Start Mapping", type="primary", use_container_width=True):
            if hasattr(st, "switch_page"):
                st.switch_page("Interactive Mapping")
    with col2:
        st.markdown("")

    st.markdown("### Overview")
    
    # Custom Metric Cards
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-label">Codes Processed</div>
                <div class="metric-value">1,284</div>
                <div style="color: #10b981; font-size: 0.875rem;">▲ 12% vs last month</div>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-label">Accuracy Rate</div>
                <div class="metric-value">98.5%</div>
                <div style="color: #10b981; font-size: 0.875rem;">▲ 0.4% confidence</div>
            </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-label">Pending Review</div>
                <div class="metric-value">24</div>
                <div style="color: #f59e0b; font-size: 0.875rem;">Needs Attention</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("### 📅 Recent Activity")
    
    df = pd.DataFrame([
        {"Time": "10:42 AM", "Action": "Map Term", "Input": "Type 2 Diabetes", "Result": "E11.9", "Status": "Completed"},
        {"Time": "10:15 AM", "Action": "Batch Upload", "Input": "Q4_Patients.csv", "Result": "154 Records", "Status": "Processing"},
        {"Time": "09:30 AM", "Action": "NLP Analysis", "Input": "Note #8821", "Result": "5 Codes", "Status": "Completed"},
    ])
    
    st.dataframe(
        df, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Status": st.column_config.TextColumn(
                "Status",
                help="Current status of the task",
                validate="^Completed|Processing$"
            )
        }
    )

def show_interactive():
    st.title("Interactive Mapping")
    st.markdown("Real-time AI lookup for clinical terminology.")
    
    with st.container():
        c1, c2 = st.columns([3, 1])
        with c1:
            query = st.text_input("Search Term", placeholder="e.g. Chest pain, Hypertension...")
        with c2:
            top_k = st.selectbox("Limit Results", [1, 3, 5, 10, "All"], index=2)
            
        systems = st.selectbox(
            "Filter by System", 
            ["ICD-10-CM", "ICD-10-PCS", "CPT"], 
            index =2
        )
        
        if st.button("Map Term"):
            if query:
                with st.spinner("Running AI Model..."):
                    df = pd.DataFrame()
                    time.sleep(0.5)
                    if not systems :
                        st.warning("Please select a Code Type (ICD-10 CM / ICD-10 PCS / CPT).")
                    else:
                        try:
                            if systems == 'ICD-10-CM':
                                df = icd_10_cm_search_bar(query)
                                df.rename(columns={'Score (0-100)': 'confidence', 'ICD_Code': 'code','Description':'description'}, inplace=True)
                            elif systems == 'ICD-10-PCS':
                                df = search_icd10_pcs_search_bar(query)
                            else:  # CPT
                                df = cpt_search_bar(query)

                            # if df is not None:
                            #     st.markdown("### Mapping Results")
                            #     st.dataframe(df.head(top_k), use_container_width=True)
                            # else:
                            #     st.info("No results returned by the selected search function.")
                        except Exception as e:
                            st.error(f"Error while fetching results: {e}")
                    
                    # Filter & Sort
                    if systems == 'ICD-10-CM':
                        # filt_code = df['code'].tolist()
                        # df.to_excel('test.xlsx')
                        # df_filt = df_master[df_master['Code'].isin(filt_code)]
                        # chapters = df_filt['Section'].unique()
                        # section = df_filt['Chapter'].unique()
                        # st.subheader("Filter by Chapter & Section")

                        # selected_chapter = st.selectbox("Select Chapter", chapters)
                        # selected_section = st.selectbox("Select Section", section)
                        # df_view =  pd.merge(df, df_filt, left_on="code",right_on="Code" ,how="inner")

                        # if selected_chapter != "All":
                        #     df_view = df_view[df_view["Chapter"] == selected_chapter]

                        # if selected_section != "All":
                        #     df_view = df_view[df_view["Section"] == selected_section]

                        results = df.to_dict(orient='records')
                        results.sort(key=lambda x: x['confidence'], reverse=True)
                        limit = len(results) if top_k == "All" else int(top_k)
                        st.markdown(f"### Found {len(results[:limit])} Matches")
                        for item in results[:limit]:
                            confidence_pct = int(item['confidence'])
                            color = "#10b981" if confidence_pct > 50 else "#f59e0b"
                            st.markdown(f"""
                            <div class="result-card">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <div>
                                    <span style="background:#fdf2f8; color:#db2777; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:bold;">{systems}</span>
                                    <h3 style="margin:4px 0 0 0; color:#0f172a;">{item['code']}</h3>
                                </div>
                                <div style="text-align:right;">
                                    <div style="font-size:1.25rem; font-weight:bold; color:{color};">{confidence_pct}%</div>
                                    <div style="font-size:0.75rem; color:#64748b;">Confidence</div>
                                </div>
                            </div>
                            <p style="margin-top:8px; color:#334155;">{item['description']}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    else :
                        results = df.to_dict(orient='records')
                        results.sort(key=lambda x: x['confidence'], reverse=True)
                        limit = len(results) if top_k == "All" else int(top_k)
                    
                        st.markdown(f"### Found {len(results[:limit])} Matches")
                    
                        for item in results[:limit]:
                            confidence_pct = int(item['confidence'])
                            color = "#10b981" if confidence_pct > 50 else "#f59e0b"
                            
                            st.markdown(f"""
                            <div class="result-card">
                                <div style="display:flex; justify-content:space-between; align-items:center;">
                                    <div>
                                        <span style="background:#fdf2f8; color:#db2777; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:bold;">{systems}</span>
                                        <h3 style="margin:4px 0 0 0; color:#0f172a;">{item['code']}</h3>
                                    </div>
                                    <div style="text-align:right;">
                                        <div style="font-size:1.25rem; font-weight:bold; color:{color};">{confidence_pct}%</div>
                                        <div style="font-size:0.75rem; color:#64748b;">Confidence</div>
                                    </div>
                                </div>
                                <p style="margin-top:8px; color:#334155;">{item['description']}</p>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.info("Enter a term to begin mapping.")

def show_batch():
    st.title("Batch Processing")
    st.markdown("Bulk process CSV or Excel files.")
    with st.container():
        c1,c2 = st.columns([3,1])
        with c1:
            uploaded = st.file_uploader("Drag and drop file here", type=['csv', 'xlsx'])
        with c2:
            top_k = st.selectbox("Limit Results", [1, 3, 5, 10,15], index=2)
        
        systems = st.selectbox(
            "Filter by System", 
            ["ICD-10-CM", "ICD-10-PCS", "CPT"], 
            index =2
        )
        
        if uploaded:
            if uploaded.name.endswith('.csv'):
                df = pd.read_csv(uploaded)
            else :
                df = pd.read_excel(uploaded)
            
            st.dataframe(df.head(2), use_container_width=True)

            st.success(f"Ready to process: {uploaded.name}")
            if st.button("Start Batch Job"):
                # my_bar = st.progress(0)
                # # for i in range(100):
                # #     time.sleep(0.01)
                # #     my_bar.progress(i + 1)
                # # st.balloons()
                df_result = batch_search_function(systems,df,top_k)
                
                st.markdown("### ✅ Processing Complete")
                st.dataframe(df_result, use_container_width=True)

def show_nlp():
    st.title("Clinical NLP Analysis")
    st.markdown("Extract codes from unstructured clinical notes.")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        text = st.text_area("Clinical Note", height=250, placeholder="Patient presenting with...")
        if st.button("Analyze Text"):
            with st.spinner("Extracting entities..."):
                time.sleep(1.5)
                st.success("Entities Extracted")
                
                # Mock NLP Result
                st.markdown("""
                <div class="result-card">
                    <h4>Extracted Entities</h4>
                    <ul>
                        <li><b>Acute chest pain</b> → <code style="color:#db2777">R07.9</code> (95%)</li>
                        <li><b>Hypertension</b> → <code style="color:#db2777">I10</code> (98%)</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                
    with col2:
        st.info("💡 **Tip:** Paste anonymized clinical text. The AI will identify diagnoses, procedures, and medications automatically.")

# -----------------------------------------------------------------------------
# ROUTER
# -----------------------------------------------------------------------------
if page == "Dashboard":
    show_dashboard()
elif page == "Interactive Mapping":
    show_interactive()
elif page == "Batch Processing":
    show_batch()
elif page == "Clinical NLP":
    show_nlp()