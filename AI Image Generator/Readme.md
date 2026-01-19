# 🎨 DreamStream AI - Backend Setup Guide

Complete backend for the DreamStream AI image generator using Flask, Google Gemini, and Imagen APIs.

---

## 📁 Project Structure

```
dreamstream-backend/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create this)
├── .env.example          # Example environment file
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

---

## 🚀 Quick Start

### Step 1: Create Project Directory

```bash
mkdir dreamstream-backend
cd dreamstream-backend
```

### Step 2: Create Virtual Environment

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your Google API key:
   ```
   GOOGLE_API_KEY=your_actual_api_key_here
   ```

**Get your API key:** https://aistudio.google.com/app/apikey

### Step 5: Run the Backend

```bash
python app.py
```

You should see:
```
🚀 DreamStream AI Backend Starting...
📡 API Key Loaded: ✓
🌐 Server running on http://127.0.0.1:5000
```

---

## 🧪 Test the Backend

### Test 1: Health Check
```bash
curl http://127.0.0.1:5000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "DreamStream AI Backend",
  "version": "1.0.0"
}
```

### Test 2: Enhance Prompt
```bash
curl -X POST http://127.0.0.1:5000/api/enhance-prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a cat in space"}'
```

### Test 3: Generate Image
```bash
curl -X POST http://127.0.0.1:5000/api/generate-image \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a beautiful sunset over mountains", "style": "photorealistic"}'
```

---

## 🔌 API Endpoints

### `GET /api/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "DreamStream AI Backend",
  "version": "1.0.0"
}
```

---

### `POST /api/enhance-prompt`
Enhance a user prompt using Gemini AI.

**Request:**
```json
{
  "prompt": "a cat in space"
}
```

**Response:**
```json
{
  "success": true,
  "enhanced_prompt": "A fluffy orange tabby cat floating gracefully in the depths of space..."
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Error message here"
}
```

---

### `POST /api/generate-image`
Generate an image using Imagen AI.

**Request:**
```json
{
  "prompt": "a beautiful sunset",
  "style": "photorealistic"
}
```

**Response:**
```json
{
  "success": true,
  "image": "base64_encoded_image_data...",
  "prompt_used": "a beautiful sunset, photorealistic style"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Error message here"
}
```

---

## 🌐 Frontend Integration

Update your frontend `index.html` to call the backend instead of Google APIs directly.

### Replace the API functions in the `<script>` section:

```javascript
// NEW: Backend API base URL
const API_BASE_URL = 'http://127.0.0.1:5000/api';

// REMOVE: state.apiKey (no longer needed)

// REPLACE: callTextAPI function
async function callTextAPI(prompt) {
    try {
        const response = await fetch(`${API_BASE_URL}/enhance-prompt`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ prompt })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Failed to enhance prompt');
        }
        
        return data.enhanced_prompt;
    } catch (error) {
        console.error("Enhance API Error:", error);
        throw error;
    }
}

// REPLACE: callImageAPI function
async function callImageAPI(prompt, style = '') {
    try {
        const response = await fetch(`${API_BASE_URL}/generate-image`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ prompt, style })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Failed to generate image');
        }
        
        return data.image;
    } catch (error) {
        console.error("Image API Error:", error);
        throw error;
    }
}
```

### Update the handleGenerate function:

```javascript
async function handleGenerate() {
    if (state.isGenerating) return;

    const prompt = els.promptInput.value.trim();
    if (!prompt) {
        showNotification("Please describe what you want to see!", "error");
        return;
    }

    setLoading(true);

    try {
        // Pass style to backend
        const style = els.styleSelect.value;
        const base64Image = await callImageAPI(prompt, style);
        const imageUrl = `data:image/png;base64,${base64Image}`;

        displayImage(imageUrl);
        addToHistory(imageUrl, prompt);
        state.currentImageBlob = base64Image;

    } catch (error) {
        showError(error.message || "Failed to generate image");
    } finally {
        setLoading(false);
    }
}
```

---

## 🔒 Security Features

✅ **API key hidden** - Never exposed to frontend  
✅ **CORS enabled** - Only your frontend can access the API  
✅ **Input validation** - All inputs are validated  
✅ **Error handling** - Graceful error responses  
✅ **Timeout protection** - Prevents hanging requests  

---

## 🐛 Troubleshooting

### "GOOGLE_API_KEY not found"
- Make sure `.env` file exists in the backend directory
- Verify the API key is correctly set: `GOOGLE_API_KEY=your_key`
- Restart the Flask server after adding the key

### CORS errors in browser
- Ensure backend is running on `http://127.0.0.1:5000`
- Check that frontend origin is in the CORS allowed list
- Open browser console to see exact CORS error

### "Connection refused"
- Backend is not running - start it with `python app.py`
- Wrong port - verify `http://127.0.0.1:5000`

### Images not generating
- Check API key is valid at https://aistudio.google.com/app/apikey
- Monitor backend console for error messages
- Imagen can take 30-60 seconds - be patient

---

## 📦 Production Deployment

For production use:

1. **Change debug mode:**
   ```python
   app.run(debug=False, host='0.0.0.0', port=5000)
   ```

2. **Update CORS origins:**
   ```python
   CORS(app, resources={
       r"/api/*": {
           "origins": ["https://yourdomain.com"],
           ...
       }
   })
   ```

3. **Use production server:**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

4. **Deploy to cloud:** Heroku, Railway, Render, or Google Cloud Run

---

## 📝 Notes

- Image generation typically takes 5-15 seconds
- Prompt enhancement takes 2-5 seconds
- Maximum prompt length: 1000 characters
- Rate limits apply based on your Google AI API quota

---

## 🎯 Next Steps

1. ✅ Backend is running
2. ✅ API endpoints tested
3. ⬜ Update frontend to use backend
4. ⬜ Test full integration
5. ⬜ Deploy to production

---

**Need help?** Check the Flask logs for detailed error messages.

**API Issues?** Visit https://ai.google.dev/gemini-api/docs for Google AI documentation.