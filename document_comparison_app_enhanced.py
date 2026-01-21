"""
Document Comparison Application - Enhanced with SharePoint Support
A Streamlit app to compare external documents with internal shared folder files.

New Features:
- SharePoint Link integration (client-side, works in air-gapped environments)
- All existing features preserved (Direct Path, File Explorer, External Upload)
"""

import streamlit as st
import os
from pathlib import Path
from urllib.parse import urlparse, unquote

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
        padding-top: 5rem !important;
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
    
    /* SharePoint specific styles */
    .sp-download-btn {
        background-color: var(--primary-color);
        color: white;
        padding: 0.75rem 1.5rem;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
        font-size: 1rem;
        box-shadow: 0 4px 6px rgba(227, 24, 55, 0.2);
        transition: all 0.3s;
        text-decoration: none;
        display: inline-block;
    }
    
    .sp-download-btn:hover {
        background-color: #c91530;
        box-shadow: 0 6px 8px rgba(227, 24, 55, 0.3);
        transform: translateY(-1px);
    }
    
    .sp-info-box {
        background-color: #e7f3ff;
        border-left: 4px solid #1e88e5;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
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


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

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


def convert_sharepoint_to_download_link(sp_link):
    """
    Convert SharePoint viewing link to direct download link.
    
    Examples:
    Input:  https://company.sharepoint.com/sites/site/doc.pdf
    Output: https://company.sharepoint.com/sites/site/doc.pdf?download=1
    
    Args:
        sp_link (str): SharePoint document URL
        
    Returns:
        str: Direct download URL
    """
    if not sp_link:
        return None
    
    sp_link = sp_link.strip()
    
    # Already has download parameter
    if 'download=' in sp_link.lower():
        return sp_link
    
    # Add download parameter
    separator = '&' if '?' in sp_link else '?'
    return f"{sp_link}{separator}download=1"


def extract_filename_from_url(url):
    """Extract filename from SharePoint URL for display."""
    try:
        parsed = urlparse(url)
        filename = unquote(parsed.path.split('/')[-1])
        return filename if filename else "document"
    except:
        return "document"


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

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
if 'sp_uploaded_files' not in st.session_state:
    st.session_state.sp_uploaded_files = []
if 'sp_link' not in st.session_state:
    st.session_state.sp_link = ""


# ============================================================================
# MAIN LAYOUT - Two Columns
# ============================================================================

col1, col2 = st.columns(2)

# ============================================================================
# LEFT COLUMN: INTERNAL SOURCE
# ============================================================================

with col1:
    st.markdown("""
        <div class="card-container">
            <div class="section-title">
                <span>📁</span> Internal Source
            </div>
    """, unsafe_allow_html=True)
    
    # Browse mode selection - Browse Files or SharePoint
    browse_mode = st.radio(
        "Select browse method:",
        options=["Browse Files", "SharePoint Link"],
        horizontal=True,
        key="browse_mode_radio"
    )
    st.session_state.browse_mode = browse_mode
    
    # ========================================================================
    # MODE 1: BROWSE FILES (SIMPLE FILE UPLOAD)
    # ========================================================================
    
    if browse_mode == "Browse Files":
        st.markdown("**📂 Upload Internal Files**")
        st.caption("Drag and drop files or click to browse")
        
        # File uploader for internal files
        uploaded_internal_files = st.file_uploader(
            "Select internal files:",
            accept_multiple_files=True,
            type=['pdf', 'docx'],
            key="internal_file_upload",
            label_visibility="collapsed"
        )
        
        if uploaded_internal_files:
            # Store uploaded files in session state
            st.session_state.selected_internal_files = uploaded_internal_files
            st.success(f"✅ {len(uploaded_internal_files)} file(s) uploaded")
            for file in uploaded_internal_files:
                file_size_kb = file.size / 1024
                st.caption(f"📄 {file.name} ({file_size_kb:.1f} KB)")
            
            # Clear button for Browse Files mode
            if st.button("🗑️ Clear", key="clear_browse_files"):
                st.session_state.selected_internal_files = []
                st.rerun()
    
    # ========================================================================
    # MODE 2: SHAREPOINT LINK
    # ========================================================================
    
    elif browse_mode == "SharePoint Link":
        st.markdown("""
        <div class="sp-info-box">
            <strong>📎 SharePoint Document Access</strong><br/>
            <small>Since the server cannot access SharePoint directly, you'll download files using your browser:</small>
            <ol style="margin: 0.5rem 0 0 0; padding-left: 1.5rem;">
                <li>Paste SharePoint link below</li>
                <li>Click to download (uses your browser's network)</li>
                <li>Upload the downloaded file</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
        # SharePoint link input
        sp_link = st.text_input(
            "📎 Paste SharePoint Document Link:",
            value=st.session_state.sp_link,
            placeholder="https://yourcompany.sharepoint.com/sites/site/Documents/file.pdf",
            key="sp_link_input",
            help="Paste the full URL of your SharePoint document"
        )
        
        if sp_link:
            st.session_state.sp_link = sp_link
            
            # Convert to download link
            download_link = convert_sharepoint_to_download_link(sp_link)
            
            # Extract filename from URL for display
            filename = extract_filename_from_url(sp_link)
            
            st.success(f"✅ Link processed: `{filename}`")
            
            # Step 1: Download button
            st.markdown("**Step 1: Download from SharePoint**")
            st.markdown(
                f"""
                <a href="{download_link}" target="_blank" rel="noopener noreferrer" class="sp-download-btn">
                    📥 Open SharePoint & Download File
                </a>
                <p style="font-size: 0.85rem; color: #6c757d; margin-top: 0.5rem;">
                    This will open SharePoint in a new tab. Download the file to your computer.
                </p>
                """,
                unsafe_allow_html=True
            )
            
            st.markdown("---")
            st.markdown("**Step 2: Upload the Downloaded File**")
        
        # File uploader for SharePoint-downloaded files (PDF and DOCX only)
        sp_uploaded = st.file_uploader(
            "Upload SharePoint file(s):",
            accept_multiple_files=True,
            type=['pdf', 'docx'],
            key="sp_file_upload",
            label_visibility="collapsed"
        )
        
        if sp_uploaded:
            st.success(f"✅ {len(sp_uploaded)} SharePoint file(s) uploaded and ready")
            
            # Display uploaded files
            for file in sp_uploaded:
                file_size_kb = file.size / 1024
                st.caption(f"📄 {file.name} ({file_size_kb:.1f} KB)")
            
            # Store in session state
            st.session_state.sp_uploaded_files = sp_uploaded
            
            # Clear button for SharePoint mode
            if st.button("🗑️ Clear", key="clear_sharepoint_files"):
                st.session_state.sp_uploaded_files = []
                st.session_state.sp_link = ""
                st.rerun()
    
    # ========================================================================
    # SHOW SELECTED FILES (ALL MODES)
    # ========================================================================
    
    # Calculate total selected files
    total_local = len(st.session_state.selected_internal_files)
    total_sp = len(st.session_state.sp_uploaded_files) if browse_mode == "SharePoint Link" else 0
    total_selected = total_local + total_sp
    
    if total_selected > 0:
        st.markdown("---")
        st.success(f"✓ {total_selected} file(s) selected")
        with st.expander("View selected files"):
            # Show local files
            for f in st.session_state.selected_internal_files:
                if hasattr(f, 'name'):  # Uploaded file object
                    st.caption(f"📄 {f.name}")
                else:  # File path string
                    st.caption(f"📄 {os.path.basename(f)}")
            
            # Show SharePoint files
            if browse_mode == "SharePoint Link" and st.session_state.sp_uploaded_files:
                for f in st.session_state.sp_uploaded_files:
                    st.caption(f"📄 {f.name} 🔗 (from SharePoint)")
        
        if st.button("Clear Selection", key="clear_internal"):
            st.session_state.selected_internal_files = []
            st.session_state.sp_uploaded_files = []
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)  # Close Internal Card


# ============================================================================
# RIGHT COLUMN: EXTERNAL DOCUMENTS
# ============================================================================

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
            
    st.markdown("</div>", unsafe_allow_html=True)  # Close External Card


# ============================================================================
# RUN BUTTON
# ============================================================================

# Spacing
st.markdown("<br>", unsafe_allow_html=True)

# Run Button - centered
col_left, col_center, col_right = st.columns([2, 1, 2])
with col_center:
    run_button = st.button("Run", use_container_width=True)


# ============================================================================
# HANDLE RUN BUTTON CLICK
# ============================================================================

if run_button:
    st.markdown("---")
    
    # Validation - check for internal files (local or SharePoint)
    has_local_files = len(st.session_state.selected_internal_files) > 0
    has_sp_files = len(st.session_state.sp_uploaded_files) > 0
    has_internal = has_local_files or has_sp_files
    
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
                
                # Show local files
                for f in st.session_state.selected_internal_files:
                    if hasattr(f, 'name'):  # Uploaded file object
                        st.write(f"• {f.name}")
                    else:  # File path string
                        st.write(f"• {os.path.basename(f)}")
                
                # Show SharePoint files
                if has_sp_files:
                    for file in st.session_state.sp_uploaded_files:
                        st.write(f"• {file.name} 🔗")  # 🔗 indicates from SharePoint
            
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
            
            **SharePoint files are available in:** `st.session_state.sp_uploaded_files`
            They can be processed the same way as external uploaded files.
            """)
            
            # Sample metrics (placeholder)
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            with metric_col1:
                total_internal = len(st.session_state.selected_internal_files) + len(st.session_state.sp_uploaded_files)
                st.metric("Internal Files", f"{total_internal}")
            with metric_col2:
                st.metric("External Files", f"{len(st.session_state.external_files or [])}")
            with metric_col3:
                st.metric("Match Score", "Pending")


# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #888888; font-size: 0.8rem;'>"
    "Document Comparison Tool | OCBC © 2026 "
    "</p>",
    unsafe_allow_html=True
)
