from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
import requests
import os
import time
import base64
import urllib.parse
from dotenv import load_dotenv
from functools import wraps

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure CORS
CORS(app)

# Get API key from environment
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

if not GOOGLE_API_KEY:
    print("⚠️  WARNING: GOOGLE_API_KEY not found in .env file!")
else:
    print("✓ API Key loaded successfully")

# Rate limiting tracking
request_timestamps = []
MAX_REQUESTS_PER_MINUTE = 10  # Conservative limit

def rate_limit(f):
    """Decorator to rate limit API calls"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        global request_timestamps
        now = time.time()
        
        # Remove timestamps older than 1 minute
        request_timestamps = [ts for ts in request_timestamps if now - ts < 60]
        
        # Check if we've exceeded the limit
        if len(request_timestamps) >= MAX_REQUESTS_PER_MINUTE:
            return jsonify({
                "success": False,
                "error": "Rate limit reached. Please wait a moment before trying again."
            }), 429
        
        # Add current timestamp
        request_timestamps.append(now)
        
        return f(*args, **kwargs)
    return decorated_function


# ============================================
# FRONTEND ROUTE
# ============================================

@app.route('/')
def index():
    """Serve the frontend HTML"""
    try:
        static_folder = os.path.join(os.getcwd(), 'static')
        index_path = os.path.join(static_folder, 'index.html')
        
        if os.path.exists(index_path):
            return send_from_directory('static', 'index.html')
        else:
            return render_template_string('''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Setup Required</title>
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                            max-width: 800px;
                            margin: 50px auto;
                            padding: 20px;
                            background: #1a1a1a;
                            color: #fff;
                        }
                        .error-box {
                            background: #2d2d2d;
                            border-left: 4px solid #ef4444;
                            padding: 20px;
                            border-radius: 8px;
                        }
                        code {
                            background: #000;
                            padding: 2px 6px;
                            border-radius: 4px;
                            color: #22d3ee;
                        }
                    </style>
                </head>
                <body>
                    <h1>⚠️ Frontend File Not Found</h1>
                    <div class="error-box">
                        <strong>Error:</strong> index.html not found in <code>static/</code> folder
                        <br><br>
                        Run: <code>mkdir static && mv index.html static/</code>
                    </div>
                </body>
                </html>
            ''')
    except Exception as e:
        return f"Error: {str(e)}", 500


# ============================================
# HELPER FUNCTIONS
# ============================================

def call_gemini_text(prompt, retries=3):
    """Call Gemini API for text generation with retry logic"""
    for attempt in range(retries):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={GOOGLE_API_KEY}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            # Handle rate limiting
            if response.status_code == 429:
                if attempt < retries - 1:
                    wait_time = (attempt + 1) * 2  # Exponential backoff
                    print(f"Rate limited. Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise Exception("Rate limit exceeded. Please wait a minute and try again.")
            
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                raise Exception(data['error'].get('message', 'Unknown error'))
            
            if not data.get('candidates') or not data['candidates'][0].get('content'):
                raise Exception("No response from Gemini")
            
            return data['candidates'][0]['content']['parts'][0]['text']
            
        except requests.exceptions.Timeout:
            if attempt < retries - 1:
                time.sleep(2)
                continue
            raise Exception("Request timed out after multiple attempts")
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                time.sleep(2)
                continue
            raise Exception(f"API request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")


def call_imagen(prompt, retries=2):
    """Generate image using Pollinations.AI (free, no API key needed)"""
    
    for attempt in range(retries):
        try:
            # URL encode the prompt
            encoded_prompt = urllib.parse.quote(prompt)
            
            # Pollinations.AI endpoint - 100% FREE, no API key needed!
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&enhance=true"
            
            print(f"🎨 Calling Pollinations.AI (Free Image Generation)...")
            print(f"📝 Prompt: {prompt[:80]}...")
            
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            # Get image bytes and convert to base64
            image_bytes = response.content
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            print(f"✅ Image generated successfully ({len(image_bytes)} bytes)")
            
            return base64_image
            
        except requests.exceptions.Timeout:
            if attempt < retries - 1:
                print(f"⏳ Timeout, retrying (attempt {attempt + 2}/{retries})...")
                time.sleep(3)
                continue
            raise Exception("Image generation timed out. Please try again.")
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                print(f"❌ Request failed, retrying (attempt {attempt + 2}/{retries})...")
                time.sleep(3)
                continue
            raise Exception(f"Image generation failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Image generation error: {str(e)}")


# ============================================
# API ENDPOINTS
# ============================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "DreamStream AI Backend",
        "version": "1.0.0",
        "api_key_loaded": bool(GOOGLE_API_KEY),
        "image_service": "Pollinations.AI (Free)"
    }), 200


@app.route('/api/enhance-prompt', methods=['POST'])
@rate_limit
def enhance_prompt():
    """Enhance user prompt using Gemini"""
    try:
        data = request.get_json()
        
        if not data or 'prompt' not in data:
            return jsonify({
                "success": False,
                "error": "No prompt provided"
            }), 400
        
        user_prompt = data['prompt'].strip()
        
        if not user_prompt:
            return jsonify({
                "success": False,
                "error": "Prompt cannot be empty"
            }), 400
        
        if len(user_prompt) > 1000:
            return jsonify({
                "success": False,
                "error": "Prompt too long (max 1000 characters)"
            }), 400
        
        # System instruction for prompt enhancement
        system_instruction = (
            "You are an expert AI art prompt engineer. Rewrite the following user description "
            "into a detailed, high-quality image generation prompt. Include details about lighting, "
            "camera angle, texture, and mood. Keep it under 60 words. Output ONLY the raw prompt, "
            "no intro/outro text."
        )
        
        full_query = f"{system_instruction}\n\nUser Input: {user_prompt}"
        
        enhanced_text = call_gemini_text(full_query)
        
        return jsonify({
            "success": True,
            "enhanced_prompt": enhanced_text.strip()
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/generate-image', methods=['POST'])
@rate_limit
def generate_image():
    """Generate image using Pollinations.AI"""
    try:
        data = request.get_json()
        
        if not data or 'prompt' not in data:
            return jsonify({
                "success": False,
                "error": "No prompt provided"
            }), 400
        
        prompt = data['prompt'].strip()
        style = data.get('style', '').strip()
        
        if not prompt:
            return jsonify({
                "success": False,
                "error": "Prompt cannot be empty"
            }), 400
        
        if len(prompt) > 1000:
            return jsonify({
                "success": False,
                "error": "Prompt too long (max 1000 characters)"
            }), 400
        
        # Build final prompt with optional style
        final_prompt = prompt
        if style:
            final_prompt += f", {style} style"
        
        print(f"🎨 Generating image with prompt: {final_prompt[:100]}...")
        
        # Generate image using Pollinations.AI
        base64_image = call_imagen(final_prompt)
        
        print("✅ Image generation complete")
        
        return jsonify({
            "success": True,
            "image": base64_image,
            "prompt_used": final_prompt
        }), 200
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


# ============================================
# RUN SERVER
# ============================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 DreamStream AI Starting...")
    print("="*60)
    print(f"📡 Gemini API Key: {'✓ Loaded' if GOOGLE_API_KEY else '✗ NOT FOUND'}")
    print(f"🎨 Image Generation: Pollinations.AI (Free, No API Key Needed)")
    print(f"📁 Working Directory: {os.getcwd()}")
    print(f"🌐 Server: http://127.0.0.1:5000")
    print(f"⏱️  Rate Limit: {MAX_REQUESTS_PER_MINUTE} requests per minute")
    print("\n🔌 API Endpoints:")
    print("   - GET  /               (Frontend)")
    print("   - GET  /api/health")
    print("   - POST /api/enhance-prompt (Gemini)")
    print("   - POST /api/generate-image (Pollinations.AI)")
    print("\n💡 Features:")
    print("   ✅ Prompt enhancement uses your Gemini API key")
    print("   ✅ Image generation is 100% FREE (Pollinations.AI)")
    print("   ✅ No additional API keys needed for images")
    print("   ✅ Images take 5-15 seconds to generate")
    print("="*60 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000)