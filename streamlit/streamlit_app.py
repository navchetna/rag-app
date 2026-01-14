"""
Streamlit frontend for RAG Backend
A modern chat interface with document ingestion and status tracking
"""

import streamlit as st
import requests
import time
from datetime import datetime
from typing import Optional, Dict, List
import json

# ============================================================================
# Configuration
# ============================================================================
st.set_page_config(
    page_title="RAG Chat Interface",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8080"
INGEST_ENDPOINT = f"{API_BASE_URL}/ingest"
QUERY_ENDPOINT = f"{API_BASE_URL}/query"
STATUS_ENDPOINT = f"{API_BASE_URL}/status"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"
BATCHES_ENDPOINT = f"{API_BASE_URL}/batches"
QDRANT_FILES_ENDPOINT = f"{API_BASE_URL}/batches/qdrant-files"
ADD_TO_QDRANT_ENDPOINT = f"{API_BASE_URL}/batches/add-to-qdrant"

# ============================================================================
# CSS Styling
# ============================================================================
st.markdown("""
<style>
    /* Main container padding */
    .main {
        padding: 2rem;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        padding: 2rem;
    }
    
    /* Card/Box styling with rounded corners */
    .card {
        background-color: #f8f9fa;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 15px;
        border: 1px solid #e9ecef;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .card-title {
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 12px;
        color: #2c3e50;
    }
    
    .file-item {
        background-color: white;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 8px;
        border-left: 4px solid #007bff;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .status-badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 50%;
        font-weight: bold;
        font-size: 12px;
    }
    
    .status-processing {
        background-color: #fff3cd;
        color: #856404;
    }
    
    .status-completed {
        background-color: #d4edda;
        color: #155724;
    }
    
    .status-error {
        background-color: #f8d7da;
        color: #721c24;
    }
    
    /* Message styling */
    .message-container {
        margin-bottom: 16px;
        display: flex;
        gap: 12px;
    }
    
    .message-user {
        justify-content: flex-end;
    }
    
    .message-assistant {
        justify-content: flex-start;
    }
    
    .message-bubble {
        max-width: 70%;
        padding: 12px 16px;
        border-radius: 15px;
        word-wrap: break-word;
    }
    
    .message-bubble-user {
        background-color: #007bff;
        color: white;
        border-radius: 15px 0 15px 15px;
    }
    
    .message-bubble-assistant {
        background-color: #f8f9fa;
        color: #2c3e50;
        border-radius: 0 15px 15px 15px;
        border: 1px solid #e9ecef;
    }
    
    .username-display {
        font-size: 18px;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 10px;
        text-align: center;
    }
    
    /* Input area styling */
    .input-container {
        display: flex;
        gap: 10px;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# Session State Initialization
# ============================================================================
if "username" not in st.session_state:
    st.session_state.username = None

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}  # {batch_job_file_id: file_info}

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # List of {"role": "user"/"assistant", "content": "..."}

if "current_batch_job_id" not in st.session_state:
    st.session_state.current_batch_job_id = None

if "file_status_cache" not in st.session_state:
    st.session_state.file_status_cache = {}  # {batch_job_file_id: status_info}

if "status_refresh_time" not in st.session_state:
    st.session_state.status_refresh_time = 0

if "selected_files_for_qdrant" not in st.session_state:
    st.session_state.selected_files_for_qdrant = {}  # {file_id: file_info}

if "batches_cache" not in st.session_state:
    st.session_state.batches_cache = []

if "qdrant_files_cache" not in st.session_state:
    st.session_state.qdrant_files_cache = []


# ============================================================================
# Helper Functions
# ============================================================================
# Helper Functions
# ============================================================================

def check_api_health() -> bool:
    """Check if the backend API is available"""
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        return response.status_code == 200
    except:
        return False


def fetch_batches() -> List[Dict]:
    """Fetch all batches from the backend"""
    try:
        response = requests.get(BATCHES_ENDPOINT, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result.get("batches", [])
        return []
    except Exception as e:
        st.error(f"Error fetching batches: {str(e)}")
        return []


def fetch_qdrant_files() -> List[Dict]:
    """Fetch files that are in Qdrant"""
    try:
        response = requests.get(QDRANT_FILES_ENDPOINT, timeout=10)
        if response.status_code == 200:
            result = response.json()
            return result.get("files", [])
        return []
    except Exception as e:
        st.error(f"Error fetching Qdrant files: {str(e)}")
        return []


def add_files_to_qdrant(files: List[Dict], user_id: str) -> Optional[Dict]:
    """Add selected files to Qdrant via DataPrep"""
    try:
        payload = {
            "files": files,
            "user_id": user_id
        }
        response = requests.post(
            ADD_TO_QDRANT_ENDPOINT,
            json=payload,
            timeout=300  # 5 minutes for processing
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error adding files to Qdrant: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error adding files to Qdrant: {str(e)}")
        return None


def get_parsing_status_icon(status: str) -> str:
    """Get icon for parsing status"""
    status_lower = status.lower()
    if status_lower == "completed":
        return "✅"
    elif status_lower in ["in_progress", "processing"]:
        return "⏳"
    elif status_lower == "failed":
        return "❌"
    else:
        return "⏸️"


def upload_files(files: List, user_id: str) -> Optional[Dict]:
    """Upload files to the backend"""
    try:
        file_data = [("files", (f.name, f.getbuffer())) for f in files]
        response = requests.post(
            INGEST_ENDPOINT,
            files=file_data,
            data={"user_id": user_id},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            st.error(f"Upload failed: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error uploading files: {str(e)}")
        return None


def get_file_status(batch_job_file_id: str) -> Optional[Dict]:
    """Get the status of a specific file"""
    try:
        response = requests.get(
            STATUS_ENDPOINT,
            params={"batch_job_file_id": batch_job_file_id},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Error fetching file status: {str(e)}")
        return None


def get_status_color_and_symbol(status: str) -> tuple[str, str]:
    """Get color and symbol for status badge"""
    status_lower = status.lower()
    
    if status_lower in ["completed", "done"]:
        return "🟢", "status-completed"
    elif status_lower in ["processing", "in_progress", "pending"]:
        return "🟡", "status-processing"
    else:
        return "🔴", "status-error"


def query_rag_system(query_text: str, user_id: str, use_context: bool = True) -> Optional[str]:
    """Send a query to the RAG system"""
    try:
        payload = {
            "query": query_text,
            "user_id": user_id,
            "use_context": use_context
        }
        
        response = requests.post(
            QUERY_ENDPOINT,
            json=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "No response received")
        else:
            return f"Error: {response.text}"
    except Exception as e:
        return f"Error querying system: {str(e)}"


# ============================================================================
# Main Application Logic
# ============================================================================

# Show login screen if no username
if not st.session_state.username:
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
            <div style="
                text-align: center;
                padding: 60px 40px;
                margin-top: 80px;
            ">
                <h1 style="font-size: 48px; margin-bottom: 10px;">🤖</h1>
                <h2 style="font-size: 32px; color: #2c3e50; margin-bottom: 10px;">RAG Chat</h2>
                <p style="font-size: 16px; color: #6c757d; margin-bottom: 40px;">
                    Enter your name to get started
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        username_input = st.text_input(
            "Your Name",
            placeholder="Enter your name...",
            key="login_input",
            label_visibility="collapsed"
        )
        
        col_left, col_right = st.columns([1, 1])
        with col_right:
            if st.button("Enter", use_container_width=True, type="primary"):
                if username_input.strip():
                    st.session_state.username = username_input.strip()
                    st.session_state.user_id = username_input.strip()
                    st.rerun()
                else:
                    st.error("Please enter your name")

# Main app content (only shown after login)
else:
    # ============================================================================
    # Sidebar - User Info, File Upload, Batch Browser, and Qdrant Files
    # ============================================================================
    
    with st.sidebar:
        # User Info Card
        st.markdown("""
            <div class="card">
                <div class="username-display">
                    👤 User
                </div>
                <p style="text-align: center; font-size: 12px; color: #6c757d;">
                    {}<br>
                    <code style="font-size: 11px;">{}</code>
                </p>
            </div>
        """.format(st.session_state.username, st.session_state.user_id), unsafe_allow_html=True)
        
        # File Upload Section
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">📤 Upload PDF Files</div>', unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader(
            "Select PDF files to process",
            type=["pdf"],
            accept_multiple_files=True,
            key="pdf_uploader",
            label_visibility="collapsed"
        )
        
        if uploaded_files:
            if st.button("📬 Upload to Server", key="upload_btn"):
                with st.spinner("Uploading files..."):
                    result = upload_files(uploaded_files, st.session_state.user_id)
                    
                    if result:
                        st.session_state.current_batch_job_id = result.get("batch_job_id")
                        batch_file_ids = result.get("batch_job_file_ids", [])
                        
                        # Store files in session state
                        for i, file_id in enumerate(batch_file_ids):
                            if i < len(uploaded_files):
                                st.session_state.uploaded_files[file_id] = {
                                    "filename": uploaded_files[i].name,
                                    "batch_job_file_id": file_id,
                                    "status": "pending",
                                    "uploaded_at": datetime.now(),
                                }
                        
                        st.success(f"✅ Uploaded {len(uploaded_files)} file(s)")
                        st.session_state.status_refresh_time = time.time()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.divider()
        
        # ============================================================================
        # Parsed Batches Browser Section
        # ============================================================================
        st.markdown("### 📂 Parsed Batches")
        
        # Refresh button for batches
        col_refresh, col_count = st.columns([1, 2])
        with col_refresh:
            if st.button("🔄 Refresh Batches", key="refresh_batches_btn"):
                st.session_state.batches_cache = fetch_batches()
                st.session_state.qdrant_files_cache = fetch_qdrant_files()
                st.rerun()
        
        # Fetch batches if cache is empty
        if not st.session_state.batches_cache:
            st.session_state.batches_cache = fetch_batches()
        
        batches = st.session_state.batches_cache
        
        with col_count:
            st.markdown(f"**{len(batches)} batch(es)**")
        
        if batches:
            # Get list of file_ids already in Qdrant
            if not st.session_state.qdrant_files_cache:
                st.session_state.qdrant_files_cache = fetch_qdrant_files()
            qdrant_file_ids = {f["batch_job_file_id"] for f in st.session_state.qdrant_files_cache}
            
            for batch in batches:
                batch_id = batch.get("batch_id", "Unknown")
                batch_status = batch.get("status", "unknown")
                file_count = batch.get("file_count", 0)
                files = batch.get("files", [])
                
                # Create batch display name (truncate if too long)
                batch_display = batch_id[:30] + "..." if len(batch_id) > 30 else batch_id
                
                with st.expander(f"📁 {batch_display} ({file_count} files)"):
                    st.markdown(f"**Status:** {batch_status}")
                    st.markdown(f"**Created:** {batch.get('created_at', 'N/A')[:19]}")
                    
                    st.markdown("---")
                    st.markdown("**Files:**")
                    
                    for file_info in files:
                        file_id = file_info.get("file_id", "")
                        filename = file_info.get("filename", "Unknown")
                        parsing_status = file_info.get("parsing_status", "pending")
                        output_tree_path = file_info.get("output_tree_path")
                        
                        status_icon = get_parsing_status_icon(parsing_status)
                        
                        # Check if already in Qdrant
                        in_qdrant = file_id in qdrant_file_ids
                        
                        col_check, col_name, col_status = st.columns([1, 4, 1])
                        
                        with col_check:
                            # Only allow selection if parsing is completed and not already in Qdrant
                            if parsing_status.lower() == "completed" and output_tree_path and not in_qdrant:
                                is_selected = file_id in st.session_state.selected_files_for_qdrant
                                if st.checkbox("", value=is_selected, key=f"select_{file_id}", label_visibility="collapsed"):
                                    st.session_state.selected_files_for_qdrant[file_id] = {
                                        "batch_id": batch_id,
                                        "file_id": file_id,
                                        "filename": filename,
                                        "output_tree_path": output_tree_path
                                    }
                                else:
                                    if file_id in st.session_state.selected_files_for_qdrant:
                                        del st.session_state.selected_files_for_qdrant[file_id]
                            elif in_qdrant:
                                st.markdown("✓", help="Already in Qdrant")
                            else:
                                st.markdown("", help="Parsing not complete")
                        
                        with col_name:
                            filename_display = filename[:25] + "..." if len(filename) > 25 else filename
                            if in_qdrant:
                                st.markdown(f"~~{filename_display}~~ *(in Qdrant)*")
                            else:
                                st.markdown(filename_display)
                        
                        with col_status:
                            st.markdown(status_icon)
        else:
            st.info("No parsed batches found. Upload PDFs to create batches.")
        
        st.divider()
        
        # ============================================================================
        # Add to Qdrant Button
        # ============================================================================
        selected_count = len(st.session_state.selected_files_for_qdrant)
        
        st.markdown(f"### 📥 Selected Files ({selected_count})")
        
        if st.session_state.selected_files_for_qdrant:
            # Show selected files
            for file_id, file_info in st.session_state.selected_files_for_qdrant.items():
                filename = file_info.get("filename", "Unknown")
                st.markdown(f"• {filename[:30]}...")
            
            if st.button("➕ Add Files to Qdrant", key="add_to_qdrant_btn", type="primary", use_container_width=True):
                with st.spinner(f"Adding {selected_count} file(s) to Qdrant..."):
                    files_to_add = list(st.session_state.selected_files_for_qdrant.values())
                    result = add_files_to_qdrant(files_to_add, st.session_state.user_id)
                    
                    if result:
                        successful = result.get("successful", 0)
                        failed = result.get("failed", 0)
                        
                        if successful > 0:
                            st.success(f"✅ Added {successful} file(s) to Qdrant!")
                        if failed > 0:
                            st.warning(f"⚠️ {failed} file(s) failed to add.")
                        
                        # Clear selections and refresh caches
                        st.session_state.selected_files_for_qdrant = {}
                        st.session_state.qdrant_files_cache = fetch_qdrant_files()
                        st.session_state.batches_cache = fetch_batches()
                        st.rerun()
            
            if st.button("🗑️ Clear Selection", key="clear_selection_btn"):
                st.session_state.selected_files_for_qdrant = {}
                st.rerun()
        else:
            st.info("Select files from batches above to add to Qdrant.")
        
        st.divider()
        
        # ============================================================================
        # Files in Qdrant Section
        # ============================================================================
        st.markdown("### 🗂️ Files in Qdrant")
        
        # Fetch Qdrant files
        if not st.session_state.qdrant_files_cache:
            st.session_state.qdrant_files_cache = fetch_qdrant_files()
        
        qdrant_files = st.session_state.qdrant_files_cache
        
        if qdrant_files:
            st.markdown(f"**{len(qdrant_files)} file(s) available as context**")
            
            for qf in qdrant_files:
                filename = qf.get("filename", "Unknown")
                filename_display = filename[:30] + "..." if len(filename) > 30 else filename
                st.markdown(f"✅ {filename_display}")
        else:
            st.info("No files in Qdrant yet. Add parsed files to enable RAG context.")
        
        st.divider()
        
        # API Status
        api_status = "✅ Connected" if check_api_health() else "❌ Disconnected"
        st.markdown(f"**API Status:** {api_status}")
        
        if st.button("🔄 Refresh All", key="refresh_all_btn"):
            st.session_state.batches_cache = fetch_batches()
            st.session_state.qdrant_files_cache = fetch_qdrant_files()
            st.rerun()
    
    
    # ============================================================================
    # Main Chat Area
    # ============================================================================
    
    # Check API health
    if not check_api_health():
        st.error("⚠️ Backend API is not available. Please check if the server is running on port 8080.")
    else:
        # Chat container
        st.markdown('<div class="card">', unsafe_allow_html=True)
        
        # Chat title
        st.markdown("### 💬 Chat")
        
        # Chat history display
        chat_container = st.container()
        
        with chat_container:
            # Display existing messages
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    st.markdown(f'<div style="text-align: right; margin-bottom: 12px;"><div class="message-bubble message-bubble-user" style="display: inline-block;">{message["content"]}</div></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div style="text-align: left; margin-bottom: 12px;"><div class="message-bubble message-bubble-assistant" style="display: inline-block;">{message["content"]}</div></div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Input area
        col1, col2 = st.columns([5, 1])
        
        with col1:
            user_input = st.text_input(
                "Type your message...",
                placeholder="Ask me anything about your documents!",
                key="user_input",
                label_visibility="collapsed"
            )
        
        with col2:
            send_button = st.button("➤", key="send_btn", use_container_width=True)
        
        # Process user input
        if send_button and user_input:
            # Add user message to history
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_input
            })
            
            # Get AI response
            with st.spinner("🤔 Thinking..."):
                response = query_rag_system(
                    user_input,
                    st.session_state.user_id,
                    use_context=True
                )
            
            # Add assistant message to history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response
            })
            
            # Clear input and refresh
            st.rerun()
        
        # Display helpful hint if no messages
        if not st.session_state.chat_history:
            st.info(
                "👋 Welcome! Upload PDF files from the sidebar, then ask me questions about them. "
                "I'll use the documents to provide accurate answers."
            )
