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
        margin-bottom: 20px;
        text-align: center;
    }
    
    /* Input area styling */
    .input-container {
        display: flex;
        gap: 10px;
        margin-top: 20px;
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
    # Sidebar - User Info, File Upload, and File Status
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
        
        # Uploaded Files Section
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f'<div class="card-title">📁 Uploaded Files ({len(st.session_state.uploaded_files)})</div>', unsafe_allow_html=True)
        
        if st.session_state.uploaded_files:
            # Refresh status periodically
            if time.time() - st.session_state.status_refresh_time > 5:
                for file_id in st.session_state.uploaded_files:
                    status_info = get_file_status(file_id)
                    if status_info:
                        files_list = status_info.get("files", [])
                        for file_data in files_list:
                            if file_data["batch_job_file_id"] == file_id:
                                # Determine overall status
                                parsing_status = file_data.get("parsing_status", "pending")
                                dataprep_status = file_data.get("dataprep_status", "pending")
                                
                                if parsing_status == "completed" and dataprep_status == "completed":
                                    overall_status = "completed"
                                elif parsing_status in ["in_progress", "processing"] or dataprep_status in ["in_progress", "processing"]:
                                    overall_status = "processing"
                                else:
                                    overall_status = parsing_status
                                
                                st.session_state.uploaded_files[file_id]["status"] = overall_status
                                break
                
                st.session_state.status_refresh_time = time.time()
            
            for file_id, file_info in st.session_state.uploaded_files.items():
                status = file_info.get("status", "pending")
                filename = file_info.get("filename", "Unknown")
                symbol, badge_class = get_status_color_and_symbol(status)
                
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(
                        f'<div class="file-item"><span title="{filename}">{filename[:30]}...</span></div>',
                        unsafe_allow_html=True
                    )
                with col2:
                    st.markdown(
                        f'<div style="text-align: center; font-size: 20px;">{symbol}</div>',
                        unsafe_allow_html=True
                    )
        else:
            st.info("No files uploaded yet. Upload a PDF to get started!")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Sidebar footer
        st.divider()
        
        # API Status
        api_status = "✅ Connected" if check_api_health() else "❌ Disconnected"
        st.markdown(f"**API Status:** {api_status}")
        
        if st.button("🔄 Refresh", key="refresh_btn"):
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
