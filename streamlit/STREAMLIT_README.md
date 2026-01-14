# Streamlit Frontend for RAG Backend

This is a modern, user-friendly web interface for the RAG (Retrieval Augmented Generation) backend system.

## Features

### 🎨 Design
- **Responsive Layout**: Sidebar (1/3 width) for file management + Chat area (2/3 width)
- **Card-based UI**: All widgets wrapped in rounded-corner cards with subtle shadows
- **Generous Padding**: Comfortable spacing throughout the interface
- **Modern Styling**: Clean, professional appearance with intuitive user interactions

### 👤 User Management
- Automatic user ID generation
- User identification displayed in the sidebar

### 📤 File Upload & Management
- Upload multiple PDF files at once
- Real-time status tracking with visual indicators:
  - 🟢 **Green**: Processing complete
  - 🟡 **Yellow**: Currently processing
  - 🔴 **Red**: Error or pending
- File status refreshes automatically every 5 seconds
- View all uploaded files with their current status

### 💬 Chat Interface
- Clean, modern chat interface with message history
- User messages styled in blue, assistant messages in gray
- Automatic message scrolling as new messages arrive
- Type and send messages with the send button
- Contextual RAG system integration for accurate responses

### 🔌 API Integration
- Automatic health check for backend connectivity
- Graceful error handling with user-friendly messages
- Timeout protection for file uploads and queries
- Real-time status synchronization

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Backend First
In one terminal window:
```bash
python setup.py run --debug
# Or use: python main.py
```

The backend will start on `http://localhost:8080`

### 3. Run the Streamlit Frontend
In another terminal window:
```bash
streamlit run streamlit_app.py
```

The frontend will be available at `http://localhost:8501`

### 🚀 Run Both Simultaneously
For convenience, use the all-in-one script:
```bash
chmod +x run_all.sh
./run_all.sh
```

This will:
1. Start the FastAPI backend on port 8080
2. Start the Streamlit frontend on port 8501
3. Automatically clean up when you exit

## Usage Guide

### 1. Upload Documents
1. Look at the **"📤 Upload PDF Files"** card in the sidebar
2. Click to select one or more PDF files from your device
3. Click the **"📬 Upload to Server"** button
4. Wait for the upload to complete

### 2. Monitor Upload Progress
- Uploaded files appear in the **"📁 Uploaded Files"** section below
- Each file shows a status indicator:
  - 🟡 Yellow: Currently being parsed and indexed
  - 🟢 Green: Ready for querying
- Status updates automatically every 5 seconds

### 3. Ask Questions
1. Type your question in the text box at the bottom
2. Click the **"➤"** button or press Enter
3. The AI will search your documents and provide an answer
4. Messages appear in the chat history with proper formatting

### 4. Monitor Backend Connection
- Check the **"API Status"** indicator at the bottom of the sidebar
- ✅ Connected: Backend is running and ready
- ❌ Disconnected: Backend is not available

## Configuration

### Backend URL
To use a different backend URL, modify the `API_BASE_URL` in `streamlit_app.py`:

```python
API_BASE_URL = "http://your-server:8080"
```

### Port Configuration
- **Backend**: Default port 8080 (set in `config.py`)
- **Frontend**: Default port 8501 (Streamlit default)

To change Streamlit port:
```bash
streamlit run streamlit_app.py --server.port=8080
```

## Features in Detail

### Session State Management
- **User ID**: Persistent across session, auto-generated on first load
- **Uploaded Files**: Stored in memory with metadata and status tracking
- **Chat History**: Maintained throughout the session
- **Status Cache**: Automatic cache refreshing every 5 seconds

### Error Handling
- Graceful handling of connection failures
- User-friendly error messages
- Automatic retry recommendations
- API health status display

### Performance
- Debounced status refreshes (5-second intervals)
- Efficient message rendering
- Non-blocking file uploads
- Responsive UI with loading indicators

## API Endpoints Used

The frontend communicates with these backend endpoints:

- `GET /health` - Check backend availability
- `POST /ingest` - Upload and ingest PDF files
- `POST /query` - Send queries to the RAG system
- `GET /status` - Check file processing status

## Troubleshooting

### Backend Not Connected
```
⚠️ Backend API is not available
```
**Solution**: 
1. Make sure the backend is running: `python setup.py run --debug`
2. Verify it's listening on port 8080
3. Check for any error messages in the backend terminal

### Files Not Uploading
**Solution**:
1. Ensure file size is reasonable
2. Check that it's a valid PDF
3. Maximum 10 files per upload request
4. Check backend logs for specific errors

### Status Not Updating
**Solution**:
1. Status refreshes every 5 seconds automatically
2. Click the 🔄 Refresh button in the sidebar
3. Check backend logs for processing issues

### Messages Not Sending
**Solution**:
1. Ensure at least one document has been uploaded and processed (status: 🟢)
2. Type a clear question
3. Check the chat is connected to the backend

## Advanced Usage

### For Docker Deployment
If running in Docker, update the API base URL:
```python
API_BASE_URL = "http://backend-service:8080"
```

### Enabling Debug Mode
To see detailed logging:
```bash
streamlit run streamlit_app.py --logger.level=debug
```

## Browser Support
- Chrome/Chromium 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance Tips
- Upload files in batches of 5-10 for optimal performance
- Clear chat history periodically for better performance
- Use the refresh button if the UI feels sluggish
- For large documents, ensure backend has sufficient resources

## License
Same as the RAG Backend project

## Support
For issues, check the logs in both the backend and Streamlit terminals.
