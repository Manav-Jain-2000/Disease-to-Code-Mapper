import streamlit as st
import pandas as pd
import time

# --- 1. CONFIGURATION AND STYLING (Modern Aesthetic & Branding) ---

# Hex codes derived from Cognitio Analytics branding and modern design
COLOR_PRIMARY_BLUE = "#153A6A"
COLOR_ACCENT_MAGENTA = "#E0407F"
COLOR_CTA_BLUE = "#36A9E1"
COLOR_BACKGROUND = "#F8F9FA"

def set_custom_css():
    """Applies modern aesthetic CSS for better design fidelity."""
    st.markdown(
        f"""
        <style>
        .css-1d391kg, .css-18e3th9, .css-1dp5ss0 {{
            background-color: {COLOR_BACKGROUND}; /* Light background for app content */
        }}
        .sidebar .sidebar-content {{
            background-color: #FFFFFF; /* White background for sidebar */
            border-right: 1px solid #EEEEEE;
        }}
        .stButton>button {{
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: bold;
            transition: all 0.2s ease-in-out;
        }}
        .main-cta {{ /* For 'Get Started' and 'Map Code' */
            background-color: {COLOR_ACCENT_MAGENTA};
            color: white;
        }}
        .main-cta:hover {{
            background-color: {COLOR_CTA_BLUE};
            color: white;
        }}
        /* Custom card styling for results and input box to add depth */
        .st-card-modern {{
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            background-color: white;
            margin-bottom: 20px;
        }}
        .st-h1 {{
            color: {COLOR_PRIMARY_BLUE};
            font-size: 36px;
            font-weight: 700;
        }}
        .sidebar-header {{
            font-size: 20px;
            font-weight: 600;
            color: {COLOR_PRIMARY_BLUE};
            padding: 15px 0 15px 0;
            border-bottom: 1px solid #E0E0E0;
            margin-bottom: 20px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Use session state to track the current page
    if 'page' not in st.session_state:
        st.session_state.page = 'landing'

# --- 2. COMPONENTS AND DATA ---

def display_header(title, subtitle=None):
    """Displays the custom header with Logo and title."""
    # Simulating the Cognitio Analytics logo/branding
    st.markdown(f'<h1 class="st-h1">{title}</h1>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<p style="color: #666; font-size: 16px;">{subtitle}</p>', unsafe_allow_html=True)
    st.markdown("---") # Visual separator

def get_sample_results(mode='interactive'):
    """Generates sample data for results table."""
    if mode == 'interactive':
        return pd.DataFrame({
            'Comorbidity': ['Insomnia', 'Sleep apnea', 'Anxiety'],
            'CODE': ['G47.00', 'G47.33', 'F41.9'],
            'CODE DESCRIPTION': ['Insomnia, unspecified', 'Obstructive sleep apnea (adult)', 'Anxiety disorder, unspecified'],
            'Confidence': ['<span style="color: green;">95%</span>', '<span style="color: orange;">75%</span>', '<span style="color: red;">30%</span>']
        })
    else: # Batch mode
        return pd.DataFrame({
            'Original Input Term': ['Trouble Sleeping', 'Chronic Cough', 'Diabetes'],
            'CODE': ['G47.00', 'R05', 'E11.9'],
            'Confidence': ['<span style="color: green;">99%</span>', '<span style="color: orange;">65%</span>', '<span style="color: green;">90%</span>']
        })

# --- 3. PAGE VIEWS ---

def landing_page():
    """Builds the aesthetic Landing Page."""
    display_header("COGNITIO ANALYTICS", "Driving Data Clarity in Healthcare")

    st.markdown('<div class="st-card-modern">', unsafe_allow_html=True)
    
    # Hero Section - Main Title and CTA
    st.markdown(
        f'<h2 style="color: {COLOR_PRIMARY_BLUE}; font-size: 3em; font-weight: 700; margin-bottom: 0;">AI-Powered Disease to Code Mapping</h2>',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<h3 style="color: {COLOR_ACCENT_MAGENTA}; font-size: 1.8em; font-weight: 600; margin-top: 5px;">Speed up your clinical coding and data analysis.</h3>',
        unsafe_allow_html=True
    )

    st.markdown("""
    <p style="font-size: 1.1em; line-height: 1.6;">
    The Disease Mapper utilizes advanced Interactive Disease Mapping and Batch Processing to instantly convert complex disease names, symptoms, and clinical text into standardized codes (ICD-10, CPT). Eliminate manual lookups and achieve compliance with high confidence scores.
    </p>
    """, unsafe_allow_html=True)

    st.button(
        "Launch Interactive Disease Mapping",
        key='launch_app_btn',
        on_click=lambda: st.session_state.update(page='app'),
        help="Try the single-search mapping mode immediately."
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Key Features Section (Simulated)
    st.markdown(f'<h2 style="color: {COLOR_PRIMARY_BLUE}; margin-top: 30px;">Key Capabilities</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            """
            <div class="st-card-modern" style="min-height: 180px;">
            <p style="font-weight: 700; color: #E0407F;">Interactive Disease Mapping</p>
            <p>Real-time, high-confidence mapping for single disease terms and comorbidities.</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(
            """
            <div class="st-card-modern" style="min-height: 180px;">
            <p style="font-weight: 700; color: #E0407F;">High-Volume Batch Processing</p>
            <p>Upload CSVs to map thousands of entries at once with exportable results.</p>
            </div>
            """, unsafe_allow_html=True)
            
    with col3:
        st.markdown(
            """
            <div class="st-card-modern" style="min-height: 180px;">
            <p style="font-weight: 700; color: #E0407F;">Multi-Code Support</p>
            <p>Map against ICD-10 CM, ICD-10 PCS, and CPT standards simultaneously.</p>
            </div>
            """, unsafe_allow_html=True)

def app_interface():
    """Builds the main Disease Mapper application interface."""
    
    # Sidebar Setup
    with st.sidebar:
        st.markdown(f'<div class="sidebar-header">Disease Mapper</div>', unsafe_allow_html=True)
        
        # Mode Selection
        mode = st.radio(
            "Select Mapping Mode",
            ('Interactive Disease Mapping', 'Batch Processing', 'Clinical Text (Coming Soon)'),
            index=0,
            format_func=lambda x: x.split('(')[0].strip() # Cleaner display for radio options
        )
        
        # Dynamic Sidebar Content based on Mode
        st.markdown("---")
        
        if mode == 'Interactive Disease Mapping':
            st.markdown('**Search Configuration**', help="Filters apply to single search results.")
            
            # Top K Filter
            st.selectbox(
                'Result count: Top k results',
                options=[3, 5, 10, 20],
                index=0,
                key='interactive_top_k'
            )
            
            # Code Type Filter
            st.markdown('**Code type:**')
            col_cm, col_pcs, col_cpt = st.columns(3)
            with col_cm: st.checkbox('ICD-10 CM', value=True)
            with col_pcs: st.checkbox('ICD-10 PCS')
            with col_cpt: st.checkbox('CPT')
            
        elif mode == 'Batch Processing':
            st.markdown('**Batch Configuration**', help="Settings for file upload and processing.")
            
            st.selectbox(
                'Top k for batch',
                options=[5, 10, 25],
                index=0,
                key='batch_top_k'
            )
            
            st.markdown('**File Upload:**')
            uploaded_file = st.file_uploader("Upload CSV", type=['csv'], help="Upload a CSV file with disease names.")
            
            # Custom buttons to simulate aesthetic
            if uploaded_file is None:
                st.button('Upload CSV File', use_container_width=True) # Styled via CSS as main-cta
                st.button('Process Batch', disabled=True, use_container_width=True)
            else:
                st.success(f"File loaded: {uploaded_file.name}")
                st.button('Replace File', use_container_width=True)
                st.button('Process Batch', type='primary', use_container_width=True)

        elif mode == 'Clinical Text (Coming Soon)':
             st.info("This feature for analyzing large clinical documents is currently in development.")

    # Main Content Area
    st.title("Disease To Code Mapper")
    st.markdown('<p style="color: #666; font-size: 14px; margin-top: -15px;">by OnePiece</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    # --- INTERACTIVE DISEASE MAPPING MODE VIEW ---
    if mode == 'Interactive Disease Mapping':
        
        st.markdown(
            f'<h3 style="color: {COLOR_PRIMARY_BLUE};">Interactive Disease Mapping</h3>',
            unsafe_allow_html=True
        )

        # Input Row
        input_col, button_col = st.columns([4, 1])
        with input_col:
            disease_name = st.text_input("Input: Disease name", "TROUBLE SLEEPING", key='disease_input')
        with button_col:
            # Adding a blank space to align the button vertically
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True) 
            if st.button("MAP CODE", key='map_code_btn', use_container_width=True):
                st.session_state.mapping_triggered = True

        st.markdown("### Mapping Results")

        if st.session_state.get('mapping_triggered', False):
            # Displaying the results table
            results_df = get_sample_results(mode='interactive')
            
            # Displaying Confidence as HTML for colored bars
            st.write(results_df.to_html(escape=False, index=False), unsafe_allow_html=True)
            
            # Simulating the confidence bar visualization
            st.markdown("""
            <div style='margin-top: 20px;'>
                <p>Confidence Key:</p>
                <div style='display: flex; gap: 10px; font-size: 0.8em;'>
                    <span><span style='color: green;'>■</span> High (>90%)</span>
                    <span><span style='color: orange;'>■</span> Medium (60%-90%)</span>
                    <span><span style='color: red;'>■</span> Low (<60%)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # --- BATCH PROCESSING MODE VIEW ---
    elif mode == 'Batch Processing':
        st.markdown(
            f'<h3 style="color: {COLOR_PRIMARY_BLUE};">Batch Processing Results</h3>',
            unsafe_allow_html=True
        )
        
        # Simulated Batch Processing Flow
        st.info("Please upload your file and click 'Process Batch' in the sidebar.")
        
        if st.button("Download Results (CSV)", key='download_btn', disabled=True):
            st.success("Simulating CSV Download...")
            time.sleep(1)
            # In a real app, this would trigger a file download handler
            
        st.markdown("---")
        st.markdown("#### Preview of Processed Data")
        
        # Displaying a placeholder for batch results
        results_df = get_sample_results(mode='batch')
        st.dataframe(results_df)

# --- 4. MAIN APP LOGIC ---

if __name__ == '__main__':
    st.set_page_config(layout="wide", page_title="Disease Mapper")
    set_custom_css()
    
    if st.session_state.page == 'landing':
        landing_page()
    else:
        app_interface()