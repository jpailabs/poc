"""
Document Comparison Application
A Streamlit app to compare external documents with internal shared folder files.
"""

import streamlit as st
import os
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="OCBC Document Comparison",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Enterprise Styling
st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global Variables */
    :root {
        --primary-color: #E31837;
        --secondary-color: #333333;
        --bg-color: #F8F9FA;
        --card-bg: #FFFFFF;
        --text-color: #212529;
        --muted-text: #6c757d;
        --border-color: #e9ecef;
        --shadow-sm: 0 2px 4px rgba(0,0,0,0.05);
        --shadow-md: 0 4px 6px rgba(0,0,0,0.07);
    }
    
    /* Global Reset & Typography */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: var(--text-color);
        background-color: var(--bg-color);
    }
    
    /* App Container */
    .stApp {
        background-color: var(--bg-color);
    }
    
    .main {
        padding: 2rem;
        max-width: 1400px;
        margin: 0 auto;
    }
    
    /* Hide Streamlit Status & Header */
    /* Hide Streamlit Status & Header */
    [data-testid="stStatusWidget"] { display: none !important; }
    header[data-testid="stHeader"] { background-color: transparent !important; }
    
    /* Hide Deploy Button & Toolbar */
    .stDeployButton {
        display: none;
        visibility: hidden;
    }
    [data-testid="stToolbar"] {
        visibility: hidden;
    }
    [data-testid="stDecoration"] {
        visibility: hidden;
    }
    
    /* Enterprise Header */
    /* Enterprise Header - Sticky */
    .enterprise-header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 999;
        background-color: white;
        padding: 1rem 2rem;
        box-shadow: var(--shadow-md);
        display: flex;
        align-items: center;
        border-bottom: 4px solid var(--primary-color);
        height: 80px;
    }
    
    /* Adjust main content to start below header */
    .block-container {
        padding-top: 5rem !important; /* Make space for fixed header */
        padding-bottom: 2rem !important;
    }
    
    /* Container for header content */
    .header-content {
        max-width: 1400px;
        width: 100%;
        margin: 0 auto;
        display: flex;
        align-items: center;
    }
    
    .logo-text {
        color: var(--primary-color);
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin: 0;
        line-height: 1;
    }
    
    .app-title {
        color: var(--secondary-color);
        font-size: 1.2rem;
        font-weight: 500;
        margin-left: 1rem;
        padding-left: 1rem;
        border-left: 2px solid var(--border-color);
    }
    
    /* Cards */
    .card-container {
        background-color: var(--card-bg);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: var(--shadow-sm);
        height: 100%;
        border: 1px solid var(--border-color);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .card-container:hover {
        box-shadow: var(--shadow-md);
        border-color: #dee2e6;
    }
    
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--secondary-color);
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 0.75rem;
    }
    
    /* Input Styling */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        border-radius: 6px;
        border: 1px solid #ced4da;
    }
    
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus-within {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 0.2rem rgba(227, 24, 55, 0.15);
    }
    
    /* File Browser */
    .file-browser-box {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 1rem;
        margin-top: 1rem;
    }
    
    .path-display {
        font-family: 'Monaco', 'Consolas', monospace;
        font-size: 0.85rem;
        color: #555;
        background: white;
        padding: 0.5rem;
        border: 1px solid #ddd;
        border-radius: 4px;
        display: block;
        margin-bottom: 0.5rem;
    }
    
    /* Small Buttons */
    .small-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.4rem 0.8rem;
        font-size: 0.85rem;
        font-weight: 500;
        color: #495057;
        background-color: white;
        border: 1px solid #ced4da;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s;
        text-decoration: none !important;
    }
    
    .small-btn:hover {
        background-color: #e9ecef;
        color: var(--primary-color);
        border-color: #adb5bd;
    }
    
    /* Primary Action Button */
    .stButton > button {
        background-color: var(--primary-color);
        color: white;
        font-weight: 600;
        padding: 0.75rem 2rem;
        border: none;
        border-radius: 8px;
        width: 100%;
        transition: all 0.3s;
        box-shadow: 0 4px 6px rgba(227, 24, 55, 0.2);
    }
    
    .stButton > button:hover {
        background-color: #c91530;
        box-shadow: 0 6px 8px rgba(227, 24, 55, 0.3);
        color: white;
    }
    
    /* Upload Area */
    .stFileUploader {
        border: 2px dashed #ced4da;
        border-radius: 8px;
        padding: 1rem;
        background-color: #f8f9fa;
        transition: border-color 0.3s;
    }
    
    .stFileUploader:hover {
        border-color: var(--primary-color);
    }
</style>
""", unsafe_allow_html=True)

# Enterprise Header
st.markdown("""
<div class="enterprise-header">
    <div class="header-content">
        <div class="logo-text">OCBC</div>
        <div class="app-title">Document Comparison AI</div>
    </div>
</div>
""", unsafe_allow_html=True)

# File browser function
def get_directory_contents(path):
    """Get contents of a directory, returning folders and files separately."""
    folders = []
    files = []
    try:
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                folders.append(item)
            elif os.path.isfile(item_path):
                # Only show PDF and DOCX files
                if item.lower().endswith(('.pdf', '.docx')):
                    files.append(item)
        folders.sort(key=str.lower)
        files.sort(key=str.lower)
    except PermissionError:
        st.error("Permission denied to access this folder")
    except Exception as e:
        st.error(f"Error accessing folder: {str(e)}")
    return folders, files

# Create two columns for Internal and External sections
col1, col2 = st.columns(2)

# Initialize session state
if 'current_path' not in st.session_state:
    st.session_state.current_path = str(Path.home())
if 'selected_internal_files' not in st.session_state:
    st.session_state.selected_internal_files = []
if 'external_files' not in st.session_state:
    st.session_state.external_files = None
if 'direct_path' not in st.session_state:
    st.session_state.direct_path = ""
if 'browse_mode' not in st.session_state:
    st.session_state.browse_mode = "Direct Path"

# Internal Section with File Browser
with col1:
    st.markdown("""
        <div class="card-container">
            <div class="section-title">
                <span>📁</span> Internal Source
            </div>
    """, unsafe_allow_html=True)
    
    # Toggle between Direct Path and File Explorer
    browse_mode = st.radio(
        "Select browse method:",
        options=["Direct Path", "File Explorer"],
        horizontal=True,
        key="browse_mode_radio"
    )
    st.session_state.browse_mode = browse_mode
    
    # ... (Content continues below, see next blocks)

    
    # ===== DIRECT PATH MODE =====
    if browse_mode == "Direct Path":
        # Text input for direct folder path
        direct_path = st.text_input(
            "Enter folder path:",
            value=st.session_state.direct_path,
            placeholder="e.g., /Users/documents or C:\\Documents",
            key="direct_path_input"
        )
        
        if direct_path:
            st.session_state.direct_path = direct_path
            # Check if path exists
            if os.path.exists(direct_path) and os.path.isdir(direct_path):
                st.success(f"✓ Valid folder path")
                
                # List files in the path
                _, files = get_directory_contents(direct_path)
                
                if files:
                    st.markdown("**📄 Files found (PDF/DOCX):**")
                    for file in files:
                        file_path = os.path.join(direct_path, file)
                        is_selected = file_path in st.session_state.selected_internal_files
                        if st.checkbox(f"📄 {file}", value=is_selected, key=f"direct_file_{file}"):
                            if file_path not in st.session_state.selected_internal_files:
                                st.session_state.selected_internal_files.append(file_path)
                        else:
                            if file_path in st.session_state.selected_internal_files:
                                st.session_state.selected_internal_files.remove(file_path)
                else:
                    st.info("No PDF or DOCX files in this folder")
            elif direct_path:
                st.error("⚠️ Invalid folder path. Please check and try again.")
    
    # ===== FILE EXPLORER MODE =====
    else:
        # Current path display
        st.text_input(
            "Current Path",
            value=st.session_state.current_path,
            key="path_display",
            disabled=True,
            label_visibility="collapsed"
        )
        
        # Navigation buttons - small inline buttons side by side
        btn_col1, btn_col2 = st.columns([1, 4])
        with btn_col1:
            col_a, col_b = st.columns(2)
            with col_a:
                go_up = st.button("⬆️", key="go_up", help="Go up one folder")
            with col_b:
                go_home = st.button("🏠", key="go_home", help="Go to home folder")
        
        if go_up:
            parent = str(Path(st.session_state.current_path).parent)
            st.session_state.current_path = parent
            st.rerun()
        if go_home:
            st.session_state.current_path = str(Path.home())
            st.rerun()
        
        # Get directory contents
        folders, files = get_directory_contents(st.session_state.current_path)
        
        # Display folders
        if folders:
            st.markdown("**📁 Folders:**")
            folder_options = ["-- Select a folder to open --"] + folders
            selected_folder = st.selectbox(
                "Select folder",
                options=folder_options,
                key="folder_select",
                label_visibility="collapsed"
            )
            if selected_folder != "-- Select a folder to open --":
                new_path = os.path.join(st.session_state.current_path, selected_folder)
                st.session_state.current_path = new_path
                st.rerun()
        
        # Display files with checkboxes for selection
        if files:
            st.markdown("**📄 Files (PDF/DOCX):**")
            for file in files:
                file_path = os.path.join(st.session_state.current_path, file)
                is_selected = file_path in st.session_state.selected_internal_files
                if st.checkbox(f"📄 {file}", value=is_selected, key=f"explorer_file_{file}"):
                    if file_path not in st.session_state.selected_internal_files:
                        st.session_state.selected_internal_files.append(file_path)
                else:
                    if file_path in st.session_state.selected_internal_files:
                        st.session_state.selected_internal_files.remove(file_path)
        else:
            st.info("No PDF or DOCX files in this folder")
    
    # Show selected files (common for both modes)
    if st.session_state.selected_internal_files:
        st.markdown("---")
        st.success(f"✓ {len(st.session_state.selected_internal_files)} file(s) selected")
        with st.expander("View selected files"):
            for f in st.session_state.selected_internal_files:
                st.caption(f"📄 {os.path.basename(f)}")
        if st.button("Clear Selection", key="clear_internal"):
            st.session_state.selected_internal_files = []
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True) # Close Internal Card

# External Section
with col2:
    st.markdown("""
        <div class="card-container">
            <div class="section-title">
                <span>📄</span> External Documents
            </div>
    """, unsafe_allow_html=True)
    
    # File uploader for external documents
    external_files = st.file_uploader(
        "Upload External Documents",
        accept_multiple_files=True,
        type=['pdf', 'docx'],
        key="external_upload",
        label_visibility="collapsed"
    )
    
    if external_files:
        st.session_state.external_files = external_files
        st.success(f"✓ {len(external_files)} file(s) uploaded")
        for file in external_files:
            st.caption(f"📄 {file.name} ({file.size / 1024:.1f} KB)")
            
    st.markdown("</div>", unsafe_allow_html=True) # Close External Card

# Spacing
st.markdown("<br>", unsafe_allow_html=True)

# Run Button - centered
col_left, col_center, col_right = st.columns([2, 1, 2])
with col_center:
    run_button = st.button("Run", use_container_width=True)

# Handle Run button click
if run_button:
    st.markdown("---")
    
    # Validation
    has_internal = len(st.session_state.selected_internal_files) > 0
    has_external = st.session_state.external_files and len(st.session_state.external_files) > 0
    
    if not has_internal:
        st.error("⚠️ Please browse and select internal files to compare.")
    elif not has_external:
        st.error("⚠️ Please upload external documents to compare.")
    else:
        # Show comparison progress
        st.markdown("### 📊 Comparison Results")
        
        with st.spinner("Comparing documents..."):
            import time
            time.sleep(1)  # Simulate processing
            
            # Display summary
            st.success("✅ Document comparison completed!")
            
            # Results container
            result_col1, result_col2 = st.columns(2)
            
            with result_col1:
                st.markdown("**Internal Files:**")
                for f in st.session_state.selected_internal_files:
                    st.write(f"� {os.path.basename(f)}")
            
            with result_col2:
                st.markdown("**External Documents:**")
                if st.session_state.external_files:
                    for file in st.session_state.external_files:
                        st.write(f"• {file.name}")
            
            # Placeholder for actual comparison results
            st.markdown("---")
            st.markdown("### 📋 Comparison Summary")
            st.info("""
            **Note:** This is a placeholder for the comparison logic. 
            
            To implement the actual comparison, you can:
            1. Parse the uploaded files based on their type
            2. Extract text/data from documents
            3. Compare content using similarity algorithms
            4. Generate a detailed comparison report
            """)
            
            # Sample metrics (placeholder)
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            with metric_col1:
                st.metric("Internal Files", f"{len(st.session_state.selected_internal_files)}")
            with metric_col2:
                st.metric("External Files", f"{len(st.session_state.external_files or [])}")
            with metric_col3:
                st.metric("Match Score", "Pending")

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #888888; font-size: 0.8rem;'>"
    "Document Comparison Tool | OCBC © 2026"
    "</p>",
    unsafe_allow_html=True
)
