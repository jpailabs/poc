"""
Document Comparison Application - Enhanced with SharePoint Support
A Streamlit app to compare external documents with internal shared folder files.

New Features:
- SharePoint Link integration (client-side, works in air-gapped environments)
- All existing features preserved (Direct Path, File Explorer, External Upload)
"""

import streamlit as st
import os
import requests
import time
from pathlib import Path
from urllib.parse import urlparse, unquote

# ============================================================================
# CONFIGURATION - ALLOWED SHAREPOINT PREFIXES
# ============================================================================
# Add or remove SharePoint URL prefixes that are allowed for document comparison.
# Users can only paste URLs that start with one of these prefixes.
# To add a new allowed prefix, simply add it to this list.

ALLOWED_SHAREPOINT_PREFIXES = [
    "https://intranet-16.com",
    "https://oc.sharepoint.com",
    "https://jjt.sharepoint.com",
    # Add more allowed prefixes below as needed:
    # "https://another-allowed-domain.com",
]

# ============================================================================
# CONFIGURATION - API ENDPOINT
# ============================================================================
# Set the API URL via environment variable or use default
# For deployment: export API_BASE_URL="https://your-api-server.com"
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
API_SUBMIT_JOB = f"{API_BASE_URL}/submit_job"
API_CHECK_STATUS = f"{API_BASE_URL}/check_status"
API_DOWNLOAD_RESULTS = f"{API_BASE_URL}/download_results"

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
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: flex-start;
        padding-left: 1rem;
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


def validate_sharepoint_url(url):
    """
    Validate if a SharePoint URL starts with an allowed prefix.
    
    Args:
        url (str): The SharePoint URL to validate
        
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not url:
        return False, "URL cannot be empty"
    
    url = url.strip()
    
    # Check if URL starts with any allowed prefix
    for prefix in ALLOWED_SHAREPOINT_PREFIXES:
        if url.lower().startswith(prefix.lower()):
            return True, None
    
    # URL doesn't match any allowed prefix
    allowed_prefixes_display = ", ".join([f"`{p}`" for p in ALLOWED_SHAREPOINT_PREFIXES])
    error_msg = f"Access denied. The SharePoint URL must start with one of the following authorized domains: {allowed_prefixes_display}"
    return False, error_msg


def parse_multiple_urls(url_string):
    """
    Parse a semicolon-separated string of URLs into a list.
    
    Args:
        url_string (str): Semicolon-separated URLs
        
    Returns:
        list: List of trimmed, non-empty URLs
    """
    if not url_string:
        return []
    
    urls = [url.strip() for url in url_string.split(';')]
    return [url for url in urls if url]  # Filter out empty strings


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
if 'sp_input_key_counter' not in st.session_state:
    st.session_state.sp_input_key_counter = 0
if 'job_id' not in st.session_state:
    st.session_state.job_id = None
if 'job_status' not in st.session_state:
    st.session_state.job_status = None
if 'job_info' not in st.session_state:
    st.session_state.job_info = None


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
            <small>Provide SharePoint URLs for your internal HR policy documents:</small>
            <ol style="margin: 0.5rem 0 0 0; padding-left: 1.5rem;">
                <li>Paste one or more SharePoint document URLs below</li>
                <li>Separate multiple URLs with semicolons (;)</li>
                <li>Only authorized SharePoint domains are accepted</li>
            </ol>
            <small style="color: #666; margin-top: 0.5rem; display: block;">
                <em>The URLs will be sent to the comparison API for processing.</em>
            </small>
        </div>
        """, unsafe_allow_html=True)
        
        # SharePoint link input - now accepts multiple URLs
        # Using dynamic key to allow proper clearing of the input
        sp_links_input = st.text_area(
            "📎 Paste SharePoint Document Link(s):",
            value=st.session_state.sp_link,
            placeholder="https://intranet-16.com/sites/docs/file1.pdf; https://intranet-16.com/sites/docs/file2.pdf",
            key=f"sp_link_input_{st.session_state.sp_input_key_counter}",
            help="Paste one or more SharePoint URLs separated by semicolons (;). Only authorized SharePoint domains are allowed.",
            height=100
        )
        
        # Clear button for URL input - allows user to clear and paste new URLs
        if st.button("🗑️ Clear URLs", key="clear_sp_urls", help="Clear the URL input to paste new URLs"):
            st.session_state.sp_link = ""
            st.session_state.sp_uploaded_files = []
            st.session_state.sp_input_key_counter += 1  # Increment to create new widget
            st.rerun()
        
        # Only process URLs if there's input
        if sp_links_input and sp_links_input.strip():
            st.session_state.sp_link = sp_links_input
            
            # Parse multiple URLs
            urls = parse_multiple_urls(sp_links_input)
            
            if urls:
                # Validate all URLs first
                valid_urls = []
                invalid_urls = []
                
                for url in urls:
                    is_valid, error_msg = validate_sharepoint_url(url)
                    if is_valid:
                        valid_urls.append(url)
                    else:
                        invalid_urls.append((url, error_msg))
                
                # Display validation errors
                if invalid_urls:
                    st.markdown("---")
                    st.error("⚠️ **Access Restricted: Unauthorized SharePoint Domain(s) Detected**")
                    for url, error in invalid_urls:
                        truncated_url = url[:60] + "..." if len(url) > 60 else url
                        st.warning(f"🚫 `{truncated_url}`\n\n{error}")
                    
                    # Show allowed prefixes for reference
                    st.info(f"**ℹ️ Authorized SharePoint Domains:**\n" + "\n".join([f"• `{p}`" for p in ALLOWED_SHAREPOINT_PREFIXES]))
                
                # Process valid URLs
                if valid_urls:
                    st.success(f"✅ {len(valid_urls)} valid link(s) processed")
                    
                    # Step 1: Show download buttons for each valid URL
                    st.markdown("**Step 1: Download from SharePoint**")
                    
                    for i, url in enumerate(valid_urls, 1):
                        download_link = convert_sharepoint_to_download_link(url)
                        filename = extract_filename_from_url(url)
                        
                        st.markdown(
                            f"""
                            <div style="margin-bottom: 0.5rem;">
                                <span style="font-size: 0.9rem; color: #555;">📄 {i}. {filename}</span>
                                <a href="{download_link}" target="_blank" rel="noopener noreferrer" 
                                   style="margin-left: 0.5rem; padding: 0.3rem 0.6rem; background-color: var(--primary-color); 
                                          color: white; border-radius: 4px; text-decoration: none; font-size: 0.8rem;">
                                    📥 Download
                                </a>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    
                    st.caption("Click each download button to save files to your computer.")
        
        # Note: In SharePoint mode, no file upload is needed here.
        # The URLs themselves are passed to the API for processing.
    
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
    
    # Get current browse mode
    current_mode = st.session_state.browse_mode
    
    # Validation based on mode
    has_external = st.session_state.external_files and len(st.session_state.external_files) > 0
    
    # Determine home_url based on mode
    home_url = ""
    if current_mode == "Browse Files":
        has_internal = len(st.session_state.selected_internal_files) > 0
        if not has_internal:
            st.error("⚠️ Please upload internal files to compare.")
            st.stop()
        internal_filenames = [f.name for f in st.session_state.selected_internal_files]
        home_url = ";".join(internal_filenames)
    elif current_mode == "SharePoint Link":
        has_sp_urls = st.session_state.sp_link and st.session_state.sp_link.strip()
        if not has_sp_urls:
            st.error("⚠️ Please provide SharePoint URLs in the input box.")
            st.stop()
        home_url = st.session_state.sp_link.strip()
    
    if not has_external:
        st.error("⚠️ Please upload external documents to compare.")
        st.stop()
    
    # Submit Job
    st.markdown("### 📤 Submitting Comparison Job")
    
    with st.spinner("Submitting documents to comparison API..."):
        try:
            # Prepare files for upload
            files = []
            for file in st.session_state.external_files:
                file.seek(0)
                files.append(
                    ('policy_file', (file.name, file.read(), file.type))
                )
            
            # Prepare form data
            data = {
                'home_url': home_url,
                'max_level': '-1'
            }
            
            # Make POST request to submit_job
            response = requests.post(
                API_SUBMIT_JOB,
                data=data,
                files=files,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                job_id = result.get('job_id')
                
                if job_id:
                    st.session_state.job_id = job_id
                    st.session_state.job_status = "SUBMITTED"
                    st.success(f"✅ Job submitted successfully!")
                    st.info(f"**Job ID:** `{job_id}`")
                else:
                    st.error("❌ No job_id returned from API")
            else:
                error_detail = "Unknown error"
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', str(error_data))
                except:
                    error_detail = response.text
                st.error(f"❌ API Error ({response.status_code}): {error_detail}")
                
        except requests.exceptions.ConnectionError:
            st.error("❌ **Connection Error**: Could not connect to the API. Please ensure the backend server is running.")
        except requests.exceptions.Timeout:
            st.error("❌ **Timeout Error**: The API request timed out. Please try again.")
        except Exception as e:
            st.error(f"❌ **Error**: {str(e)}")


# ============================================================================
# JOB STATUS SECTION
# ============================================================================

if st.session_state.job_id:
    st.markdown("---")
    st.markdown("### 📊 Job Status")
    
    # Display current job info
    st.info(f"**Job ID:** `{st.session_state.job_id}`")
    
    # Check Status button
    col_status, col_download = st.columns(2)
    
    with col_status:
        if st.button("🔄 Check Status", use_container_width=True):
            try:
                response = requests.get(
                    f"{API_CHECK_STATUS}/{st.session_state.job_id}",
                    timeout=30
                )
                
                if response.status_code == 200:
                    status_data = response.json()
                    st.session_state.job_status = status_data.get('status', 'UNKNOWN')
                    st.session_state.job_info = status_data.get('info', {})
                else:
                    st.error(f"❌ Failed to get status: {response.status_code}")
                    
            except Exception as e:
                st.error(f"❌ Error checking status: {str(e)}")
    
    with col_download:
        if st.session_state.job_status == "COMPLETED":
            if st.button("📥 Download Results", use_container_width=True):
                try:
                    response = requests.get(
                        f"{API_DOWNLOAD_RESULTS}/{st.session_state.job_id}",
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        # Check if it's a file download or JSON with link
                        content_type = response.headers.get('content-type', '')
                        
                        if 'application/json' in content_type:
                            result = response.json()
                            download_url = result.get('download_url') or result.get('url')
                            if download_url:
                                st.success(f"📎 Download ready!")
                                st.markdown(f"[📥 Click here to download]({download_url})")
                            else:
                                st.json(result)
                        else:
                            # Direct file download
                            st.download_button(
                                label="💾 Save Results",
                                data=response.content,
                                file_name=f"comparison_results_{st.session_state.job_id[:8]}.zip",
                                mime="application/octet-stream"
                            )
                    else:
                        st.error(f"❌ Download failed: {response.status_code}")
                        
                except Exception as e:
                    st.error(f"❌ Error downloading: {str(e)}")
    
    # Display status info
    if st.session_state.job_status:
        status = st.session_state.job_status
        
        # Status badge
        if status == "COMPLETED":
            st.success(f"✅ Status: **{status}**")
        elif status == "PROGRESS" or status == "PROCESSING":
            st.warning(f"⏳ Status: **{status}**")
        elif status == "FAILED":
            st.error(f"❌ Status: **{status}**")
        else:
            st.info(f"� Status: **{status}**")
        
        # Progress info
        if st.session_state.job_info:
            info = st.session_state.job_info
            
            with st.expander("📋 Processing Details", expanded=True):
                info_col1, info_col2 = st.columns(2)
                
                with info_col1:
                    st.metric("Total Files", info.get('total_file', 'N/A'))
                    st.metric("Total Processed", info.get('total_processed', 'N/A'))
                
                with info_col2:
                    st.metric("Total PDFs", info.get('total_pdf', 'N/A'))
                    st.metric("Failed", info.get('total_failed', 'N/A'))
                
                if info.get('processing_pdf'):
                    st.caption(f"🔄 Currently processing: `{info.get('processing_pdf')}`")
                
                if info.get('status'):
                    st.caption(f"📌 Step: `{info.get('status')}`")
    
    # Clear job button
    if st.button("🗑️ Clear Job", key="clear_job"):
        st.session_state.job_id = None
        st.session_state.job_status = None
        st.session_state.job_info = None
        st.rerun()


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
