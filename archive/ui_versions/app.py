import streamlit as st
import pandas as pd
import time
import os
from scripts.icd_10_cm_search_bar import icd_10_cm_search_bar
from scripts.icd_10_pcs_search_bar import search_icd10_pcs_search_bar
# --- 1. CONFIGURATION AND STYLING (Modern Aesthetic & Branding) ---

# Refined Hex codes for a premium, Cognitio-like aesthetic
COLOR_DEEP_NAVY = "#112D57"         
COLOR_BRAND_MAGENTA = "#E0407F"     
COLOR_CTA_GRADIENT_END = "#AF44B0"  
COLOR_BACKGROUND_LIGHT = "#F0F2F6"  
COLOR_TEXT_DARK = "#333333"         
class ICDcodeNode:
    def __init__(self, icd_code, description, children, parent):
        self.icd_code = icd_code
        self.description = description
        self.children  =  children
        self.parent = parent

    def get_children(self):
        return self.children
    
    def add_child(self, child):
        if child not in self.children:
            self.children.append(child)

    def get_parent(self):
        return self.parent
    
    def set_parent(self,parent):
        self.parent = parent

    def __repr__(self):
        return f'{self.icd_code} - {self.description} -  Children: {[x.icd_code for x in self.children]}'
# --- IMPORTANT: Logo Path Configuration ---
LOGO_PATH = "cognitio_logo.png" 

def set_custom_css():
    """Applies modern aesthetic CSS using gradients and depth."""
    
    GRADIENT_STYLE = f"""
        background-image: linear-gradient(to right, {COLOR_BRAND_MAGENTA} 0%, {COLOR_CTA_GRADIENT_END} 100%);
        color: white;
        border: none;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease-in-out;
    """
    
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {COLOR_BACKGROUND_LIGHT};
        }}
        .css-1d391kg, .css-18e3th9, .css-1dp5ss0 {{
            background-color: white; 
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1); 
        }}
        .sidebar .sidebar-content {{
            background-color: white;
            padding: 20px;
            border-right: 1px solid #EEEEEE;
        }}
        .stButton button[kind="primary"] {{
            {GRADIENT_STYLE}
        }}
        .stButton button[kind="primary"]:hover {{
            box-shadow: 0 6px 15px rgba(0, 0, 0, 0.3);
            transform: translateY(-2px);
        }}
        
        /* Typography */
        h1, h2, h3, h4 {{
            color: {COLOR_DEEP_NAVY};
        }}
        .st-h1-cognitio {{
            color: {COLOR_DEEP_NAVY};
            font-size: 38px;
            font-weight: 800;
            line-height: 1.1;
        }}
        .st-subtitle-onepiece {{
            color: #6c757d;
            font-size: 14px;
            margin-top: -10px;
            margin-bottom: 20px;
            display: block;
        }}
        .st-card-modern {{
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            background-color: #FFFFFF;
            margin-bottom: 20px;
        }}
        
        /* Fix for Streamlit image padding/margin in columns */
        .css-1jc7a0z, .css-1r0fymm, .css-1r6gwwb, .css-1g6x2c9 {{
            padding: 0;
            margin: 0;
        }}
        
        .nav-links {{
            text-align: right; 
            font-size: 16px; 
            padding-top: 10px; 
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    if 'page' not in st.session_state:
        st.session_state.page = 'landing'
    if 'mapping_triggered' not in st.session_state:
        st.session_state.mapping_triggered = False
    if 'batch_processed' not in st.session_state:
        st.session_state.batch_processed = False
    if 'app_mode' not in st.session_state:
        st.session_state.app_mode = 'Interactive Disease Mapping'

# --- 2. COMPONENTS AND DATA ---

def get_sample_results(mode='interactive'):
    """Generates sample data for results table with HTML for confidence bars."""
    if mode == 'interactive':
        data = {
            'Comorbidity': ['Insomnia', 'Sleep Apnea', 'Anxiety Disorder'],
            'CODE': ['G47.00 (ICD-10 CM)', 'G47.33 (ICD-10 PCS)', 'F41.9 (CPT)'],
            'Confidence': [0.95, 0.75, 0.30]
        }
    else: # Batch mode
        data = {
            'Original Input Term': ['Trouble Sleeping', 'Chronic Cough', 'Type 2 Diabetes'],
            'CODE': ['G47.00 (CM)', 'R05 (CM)', 'E11.9 (CM)'],
            'Confidence': [0.99, 0.65, 0.90]
        }
    
    df = pd.DataFrame(data)
    
    def confidence_bar(conf):
        color = 'green' if conf > 0.9 else ('orange' if conf > 0.6 else 'red')
        width = int(conf * 100)
        return f'<div style="width: 100px; background-color: #eee; border-radius: 3px; height: 8px;">' \
               f'<div style="width: {width}%; background-color: {color}; border-radius: 3px; height: 8px;"></div>' \
               f'</div> <span style="font-size: 0.9em; color: {COLOR_TEXT_DARK};"> {conf*100:.0f}%</span>'

    df['Confidence'] = df['Confidence'].apply(confidence_bar)
    return df.to_html(escape=False, index=False)


# --- 3. PAGE VIEWS ---

def landing_page():
    """Builds the aesthetic Landing Page with the Cognitio Analytics logo and clickable cards."""
    
    col_logo, col_nav = st.columns([4, 5]) 

    with col_logo:
        try:
            st.image(LOGO_PATH, width=450) 
        except FileNotFoundError:
            st.error(f"Logo not found. Ensure '{LOGO_PATH}' is in the same directory as the script.")
        except Exception:
            st.markdown(
                f'<span style="font-size: 16px; font-weight: 700; color: {COLOR_DEEP_NAVY};">Cognitio Analytics</span>',
                unsafe_allow_html=True
            )

    with col_nav:
        # Pushes the navigation links down to align with the bottom of the larger logo.
        st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True) 
        st.markdown(
            f'<div class="nav-links">Solutions | About Us | Contact</div>', 
            unsafe_allow_html=True
        )

    st.markdown("---")

    # Helper function to create clickable card elements
    def clickable_card(mode, title, description, color):
        # We use a hidden Streamlit button to manage state transitions
        if st.button(title, key=f"launch_{mode}", use_container_width=True):
            st.session_state.page = 'app'
            st.session_state.app_mode = mode
        
        # Use HTML/CSS to style the visible card. 
        # Note: True cross-browser click-to-Streamlit-state transition without JS is complex, 
        # so we rely on the hidden button above for core functionality.
        st.markdown(
            f"""
            <div class="st-card-modern" style="min-height: 150px; text-align: center; margin-top: -30px;">
                <p style="font-weight: 700; color: {color}; font-size: 1.1em; margin-bottom: 5px;">{title}</p>
                <p>{description}</p>
            </div>
            """, unsafe_allow_html=True)


    # Hero Section - Main Title
    st.markdown('<div class="st-card-modern" style="padding: 40px; text-align: center;">', unsafe_allow_html=True)
    st.markdown(
        f'<h1 class="st-h1-cognitio" style="color: {COLOR_BRAND_MAGENTA};">AI-Powered Disease to Code Mapper</h1>',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<h2 style="color: {COLOR_DEEP_NAVY}; font-size: 1.8em; font-weight: 500; margin-top: 10px;">'
        'Rapidly transform clinical terminology into accurate, standardized codes (ICD-10, CPT).'
        '</h2>',
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    
    # Key Features Section (Now with dedicated launch buttons)
    st.markdown(f'<h2 style="color: {COLOR_DEEP_NAVY}; margin-top: 40px; text-align: center;">Core Capabilities</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        clickable_card(
            'Interactive Disease Mapping', 
            'Interactive Disease Mapping', 
            'Real-time, high-confidence mapping for single disease terms.', 
            COLOR_BRAND_MAGENTA
        )

    with col2:
        clickable_card(
            'Batch Processing', 
            'Batch Processing', 
            'Upload CSVs for high-volume mapping and easy export.', 
            COLOR_BRAND_MAGENTA
        )
        
    with col3:
        # Note: Clinical Text remains non-functional, but acts as a visual card
        st.markdown(
            """
            <div class="st-card-modern" style="min-height: 180px; text-align: center;">
            <p style="font-weight: 700; color: #E0407F; font-size: 1.1em; margin-bottom: 5px;">Clinical Text</p>
            <p>Maps against ICD-10 CM, ICD-10 PCS, and CPT standards.</p>
            </div>
            """, unsafe_allow_html=True)



def app_interface():
    """Builds the main Disease Mapper application interface."""
    
    # -------------------------------------------------------------------------
    # NEW: Helper functions for mutually-exclusive checkbox behavior
    # -------------------------------------------------------------------------
    def _set_code_type(selected_key: str):
        """Ensure only one Interactive mode checkbox remains True."""
        for k in ('interactive_cm', 'interactive_pcs', 'interactive_cpt'):
            st.session_state[k] = (k == selected_key)

    def _set_batch_code_type(selected_key: str):
        """Ensure only one Batch mode checkbox remains True."""
        for k in ('batch_cm', 'batch_pcs', 'batch_cpt'):
            st.session_state[k] = (k == selected_key)

    # Initialize defaults (so we don’t get KeyErrors on first render)
    st.session_state.setdefault('interactive_cm', True)
    st.session_state.setdefault('interactive_pcs', False)
    st.session_state.setdefault('interactive_cpt', False)

    st.session_state.setdefault('batch_cm', True)
    st.session_state.setdefault('batch_pcs', False)
    st.session_state.setdefault('batch_cpt', False)
    # -------------------------------------------------------------------------

    with st.sidebar:
        
        st.markdown(f'<div style="text-align: center; font-size: 1.5em; font-weight: 700; color: {COLOR_DEEP_NAVY}; margin-bottom: 15px;">Mapping Modes</div>', unsafe_allow_html=True)

        mode_mapping = {
            'Interactive Disease Mapping': 'Interactive Disease Mapping',
            'Batch Processing': 'Batch Processing'
        }
        
        for label, mode_key in mode_mapping.items():
            button_style = 'primary' if st.session_state.app_mode == mode_key else 'secondary'
            
            if st.button(label, key=mode_key, use_container_width=True, type=button_style):
                st.session_state.app_mode = mode_key
                st.session_state.mapping_triggered = False
                st.session_state.batch_processed = False
        
        st.button('Clinical Text (Inactive)', key='Clinical Text', use_container_width=True, disabled=True)
        
        st.markdown("---")
        
        # Sidebar Filters based on the selected mode
        if st.session_state.app_mode == 'Interactive Disease Mapping':
            st.markdown(f'<h4 style="color: {COLOR_DEEP_NAVY}; margin-top: 10px;">Search Filters</h4>', unsafe_allow_html=True)
            
            st.selectbox(
                'Result count: Top k results',
                options=[3, 5, 10, 20],
                index=1,
                key='interactive_top_k'
            )
            
            st.markdown('**Code type:**')
            col_cm, col_pcs, col_cpt = st.columns(3)

            # -----------------------------------------------------------------
            # NEW: Mutually-exclusive checkboxes (Interactive)
            # -----------------------------------------------------------------
            with col_cm:
                st.checkbox(
                    'ICD-10 CM',
                    value=st.session_state.interactive_cm,
                    key='interactive_cm',
                    on_change=_set_code_type,
                    args=('interactive_cm',)
                )
            with col_pcs:
                st.checkbox(
                    'ICD-10 PCS',
                    value=st.session_state.interactive_pcs,
                    key='interactive_pcs',
                    on_change=_set_code_type,
                    args=('interactive_pcs',)
                )
            with col_cpt:
                st.checkbox(
                    'CPT',
                    value=st.session_state.interactive_cpt,
                    key='interactive_cpt',
                    on_change=_set_code_type,
                    args=('interactive_cpt',)
                )
            # -----------------------------------------------------------------

    # --------------------------------------------------------------------------------
    # KEY FIX: Customized Header with Color (Aligned and Styled)
    # --------------------------------------------------------------------------------
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: -10px;">
            <p style="font-size: 30px; color: {COLOR_DEEP_NAVY};">☰</p> 
            <h1 style="font-size: 2.2em; font-weight: 800; color: {COLOR_DEEP_NAVY}; line-height: 1;">
                Disease 
                <span style="color: {COLOR_BRAND_MAGENTA};">Mapper</span>
            </h1>
        </div>
        """, unsafe_allow_html=True
    )
    st.markdown('<span class="st-subtitle-onepiece">by OnePiece</span>', unsafe_allow_html=True)
    st.markdown("---")


    if st.session_state.app_mode == 'Interactive Disease Mapping':
        
        st.markdown(
            f'<h3 style="color: {COLOR_DEEP_NAVY};">Interactive Disease Mapping</h3>',
            unsafe_allow_html=True
        )

        input_col, button_col = st.columns([4, 1])
        with input_col:
            disease_name = st.text_input("Input: Disease name", "TROUBLE SLEEPING", key='disease_input', help="Enter a clinical term or disease name.")
        with button_col:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True) 
            if st.button("MAP CODE", key='map_code_btn', type='primary', use_container_width=True):
                st.session_state.mapping_triggered = True

        

        if st.session_state.mapping_triggered:
            # Existing Card (kept same)
            # st.markdown('<div class="st-card-modern">', unsafe_allow_html=True)
            # results_html = get_sample_results(mode='interactive')
            # st.markdown(results_html, unsafe_allow_html=True)
            # st.markdown('</div>', unsafe_allow_html=True)

            # -----------------------------------------------------------------
            # NEW: Run the selected search function on MAP CODE and show DataFrame
            # -----------------------------------------------------------------
            active_model_key = (
                'ICD-10 CM' if st.session_state.get('interactive_cm', False) else
                'ICD-10 PCS' if st.session_state.get('interactive_pcs', False) else
                'CPT' if st.session_state.get('interactive_cpt', False) else None
            )

            st.markdown("#### Search Results (DataFrame)")
            if not active_model_key:
                st.warning("Please select a Code Type (ICD-10 CM / ICD-10 PCS / CPT).")
            else:
                try:
                    top_k = st.session_state.get('interactive_top_k', 5)
                    if active_model_key == 'ICD-10 CM':
                        df = icd_10_cm_search_bar(disease_name)
                        
                    elif active_model_key == 'ICD-10 PCS':
                        df = search_icd10_pcs_search_bar(disease_name)
                    else:  # CPT
                        df = cpt_search_bar(disease_name)

                    if df is not None:
                        st.markdown("### Mapping Results")
                        st.dataframe(df.head(top_k), use_container_width=True)
                    else:
                        st.info("No results returned by the selected search function.")
                except Exception as e:
                    st.error(f"Error while fetching results: {e}")
            # -----------------------------------------------------------------
            
    # --------------------------------------------------------------------------------
    # KEY FIX: Batch Processing - Centralized Upload and Code Type Filters
    # --------------------------------------------------------------------------------
    elif st.session_state.app_mode == 'Batch Processing':
        
        st.markdown(
            f'<h3 style="color: {COLOR_DEEP_NAVY};">Batch Processing</h3>',
            unsafe_allow_html=True
        )

        st.markdown('<div class="st-card-modern" style="padding: 30px;">', unsafe_allow_html=True)
        st.markdown(f'<h4 style="color: {COLOR_DEEP_NAVY}; margin-bottom: 10px; text-align: center;">Upload File and Configure Batch</h4>', unsafe_allow_html=True)

        uploaded_file = st.file_uploader("Upload CSV", type=['csv'], help="Upload a CSV file with disease names.", key='file_uploader')
        
        st.markdown("---")

        config_col1, config_col2, config_col3 = st.columns([1, 2, 1])
        
        with config_col1:
            st.selectbox(
                'Top k results per term',
                options=[5, 10, 25],
                index=0,
                key='batch_top_k'
            )

        with config_col2:
            st.markdown('<p style="font-weight: 600; margin-bottom: 0px;">Code Type Filters</p>', unsafe_allow_html=True)
            col_cm, col_pcs, col_cpt = st.columns(3)

            # -----------------------------------------------------------------
            # NEW: Mutually-exclusive checkboxes (Batch)
            # -----------------------------------------------------------------
            with col_cm:
                st.checkbox(
                    'ICD-10 CM',
                    value=st.session_state.batch_cm,
                    key='batch_cm',
                    on_change=_set_batch_code_type,
                    args=('batch_cm',)
                )
            with col_pcs:
                st.checkbox(
                    'ICD-10 PCS',
                    value=st.session_state.batch_pcs,
                    key='batch_pcs',
                    on_change=_set_batch_code_type,
                    args=('batch_pcs',)
                )
            with col_cpt:
                st.checkbox(
                    'CPT',
                    value=st.session_state.batch_cpt,
                    key='batch_cpt',
                    on_change=_set_batch_code_type,
                    args=('batch_cpt',)
                )
            # -----------------------------------------------------------------

        with config_col3:
            st.markdown('<div style="height: 30px;"></div>', unsafe_allow_html=True)
            if uploaded_file is None:
                st.button('Process Batch', key='process_disabled_btn', disabled=True, type='primary', use_container_width=True)
            else:
                if st.button('Process Batch', key='process_batch_btn', type='primary', use_container_width=True):
                    st.session_state.batch_processed = True
                
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.get('batch_processed', False):
            st.markdown(f'<h3 style="color: {COLOR_DEEP_NAVY}; margin-top: 30px;">Processed Batch Results</h3>', unsafe_allow_html=True)
            
            st.download_button(
                "Export Results (CSV)",
                data="Original Input Term,CODE,Confidence\nExample,A01.0,0.95", 
                file_name="disease_mapper_batch_results.csv",
                mime="text/csv",
                key='download_results_btn',
                help="Download the complete mapping results."
            )
            
            st.markdown('<div class="st-card-modern">', unsafe_allow_html=True)
            # results_html = get_sample_results(mode='batch')
            # st.markdown(results_html, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# --- 4. MAIN APP LOGIC ---

if __name__ == '__main__':
    st.set_page_config(layout="wide", page_title="Disease Mapper - Cognitio Analytics")
    set_custom_css()
    
    if st.session_state.page == 'landing':
        landing_page()
    else:
        app_interface()