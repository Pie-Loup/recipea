from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify, render_template, redirect, url_for
import tempfile
from google import genai
from prompts import prompt_voice, prompt_photo, prompt_text
import io
from pydub import AudioSegment
import httpx

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set in environment variables.")

app = Flask(__name__)
client = genai.Client(api_key=GEMINI_API_KEY)

SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET")
if not SUPABASE_JWT_SECRET:
    raise RuntimeError("SUPABASE_JWT_SECRET is not set in environment variables.")
SUPABASE_PROJECT_ID = os.environ.get("SUPABASE_PROJECT_ID")
if not SUPABASE_PROJECT_ID:
    raise RuntimeError("SUPABASE_PROJECT_ID is not set in environment variables.")
supabase_anon_key = os.environ.get('SUPABASE_ANON_KEY')
if not supabase_anon_key:
    raise RuntimeError("SUPABASE_ANON_KEY is not set in environment variables.")
supabase_url = os.environ.get('SUPABASE_URL')
if not supabase_url:
    raise RuntimeError("SUPABASE_URL is not set in environment variables.")

def verify_supabase_jwt(token):
    print("Verifying token:", token[:20] + "..." if token else None)  # Debug log
    # You can use PyJWT to verify, or call Supabase's /user endpoint
    # Here is a simple example using PyJWT:
    import jwt
    try:
        # Note: Supabase JWTs use HS256 algorithm and have specific claims
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience=["authenticated"],
            options={"verify_exp": True}
        )
        print("Token verification success:", payload.get('sub'))  # Debug log
        return payload
    except Exception as e:
        print("Token verification failed:", str(e))  # Debug log
        return None

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get("sb-access-token") or request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token or not verify_supabase_jwt(token):
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def check_user_has_username(token):
    headers = {
        "apikey": supabase_anon_key,
        "Authorization": f"Bearer {token}"
    }
    
    response = httpx.get(
        f"{supabase_url}/rest/v1/profiles",
        headers=headers,
        params={
            "id": f"eq.{verify_supabase_jwt(token)['sub']}",
            "select": "username"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        return len(data) > 0
    return False

def get_site_url():
    return request.scheme + "://" + request.host

@app.route('/')
def index():
    site_url = get_site_url()
    return render_template('index.html', 
                         supabase_anon_key=supabase_anon_key, 
                         supabase_url=supabase_url,
                         site_url=site_url)

@app.route('/username-setup')
@login_required
def username_setup():
    return render_template('username.html', supabase_anon_key=supabase_anon_key, supabase_url=supabase_url)

@app.route('/feed')
@login_required
def feed():
    token = request.cookies.get("sb-access-token")
    if not check_user_has_username(token):
        return redirect(url_for('username_setup'))
    return render_template('feed.html', supabase_anon_key=supabase_anon_key, supabase_url=supabase_url)

@app.route('/recipe_generator')
@login_required
def recipe_generator():
    # Redirect old route to new create-recipe page
    return redirect(url_for('create_recipe'))

@app.route('/profile')
@login_required
def profile():
    token = request.cookies.get("sb-access-token")
    if not check_user_has_username(token):
        return redirect(url_for('username_setup'))
    return render_template('profile.html', supabase_anon_key=supabase_anon_key, supabase_url=supabase_url)

@app.route('/generate_recipe_from_voice', methods=['POST'])
@login_required
def generate_recipe_from_voice():
    try:
        # Get all audio files from the request
        audio_files = request.files.getlist('audio')
        if not audio_files:
            return jsonify({'error': 'No audio files provided'}), 400

        # Create a temporary file for the combined audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
            # Initialize combined audio segment
            combined = None
            
            # Process each audio file
            for audio_file in audio_files:
                if audio_file.filename == '':
                    continue
                    
                # Read the audio file into memory
                audio_data = io.BytesIO(audio_file.read())
                try:
                    # Load the audio segment
                    segment = AudioSegment.from_file(audio_data)
                    
                    # Add to combined segment
                    if combined is None:
                        combined = segment
                    else:
                        combined += segment
                except Exception as e:
                    return jsonify({'error': f'Error processing audio file {audio_file.filename}: {str(e)}'}), 500
            
            if combined:
                # Export the combined audio to the temporary file
                combined.export(temp_audio.name, format='wav')
                
                # Upload the combined file to Gemini
                try:
                    audio_file = client.files.upload(file=temp_audio.name)

                    # Generate recipe using Gemini API with file and prompt
                    response = client.models.generate_content(
                        model="gemini-2.5-flash-preview-05-20",
                        config={"response_mime_type": "application/json"},
                        contents=[audio_file, prompt_voice]
                    )

                    if response.text:
                        try:
                            # Convert Gemini's response text to a dictionary and return it directly
                            recipe_json = eval(response.text)
                            if not all(key in recipe_json for key in ['ingredients', 'steps', 'questions']):
                                return jsonify({'error': 'Invalid recipe format'}), 500
                            return jsonify(recipe_json)
                        except Exception as e:
                            return jsonify({'error': f'Invalid JSON format: {str(e)}'}), 500
                    else:
                        return jsonify({'error': 'No response from Gemini API'}), 500

                finally:
                    # Clean up the temporary file
                    try:
                        os.unlink(temp_audio.name)
                    except:
                        pass

    except Exception as e:
        return jsonify({'error': f'Error generating recipe: {str(e)}'}), 500

@app.route('/create-recipe')
@login_required
def create_recipe():
    token = request.cookies.get("sb-access-token")
    return render_template('create_recipe.html', supabase_anon_key=supabase_anon_key, supabase_url=supabase_url)

@app.route('/create-recipe/photo')
@login_required
def create_recipe_photo():
    token = request.cookies.get("sb-access-token")
    return render_template('photo_recipe_generator.html', supabase_anon_key=supabase_anon_key, supabase_url=supabase_url)

@app.route('/create-recipe/text')
@login_required
def create_recipe_text():
    token = request.cookies.get("sb-access-token")
    return render_template('text_recipe_generator.html', supabase_anon_key=supabase_anon_key, supabase_url=supabase_url)

@app.route('/voice-recipe')
@login_required
def voice_recipe():
    token = request.cookies.get("sb-access-token")
    return render_template('voice_recipe_generator.html', supabase_anon_key=supabase_anon_key, supabase_url=supabase_url)

@app.route('/generate_recipe_from_photo', methods=['POST'])
@login_required
def generate_recipe_from_photo():
    try:
        # Get the photo file from the request
        photo_file = request.files.get('photo')
        if not photo_file:
            return jsonify({'error': 'No photo provided'}), 400

        # Create a temporary file for the photo
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_photo:
            # Save the uploaded photo
            photo_file.save(temp_photo.name)
            
            try:
                # Upload the photo to Gemini
                photo = client.files.upload(file=temp_photo.name)

                # Generate recipe using Gemini API with photo and prompt
                response = client.models.generate_content(
                    model="gemini-2.5-flash-preview-05-20",
                    config={"response_mime_type": "application/json"},
                    contents=[photo, prompt_photo]
                )

                if response.text:
                    try:
                        # Convert Gemini's response text to a dictionary and return it
                        recipe_json = eval(response.text)
                        if not all(key in recipe_json for key in ['ingredients', 'steps', 'other_elements']):
                            return jsonify({'error': 'Invalid recipe format'}), 500
                        return jsonify(recipe_json)
                    except Exception as e:
                        return jsonify({'error': f'Invalid JSON format: {str(e)}'}), 500
                else:
                    return jsonify({'error': 'No response from Gemini API'}), 500

            finally:
                # Clean up the temporary file
                try:
                    os.unlink(temp_photo.name)
                except:
                    pass

    except Exception as e:
        return jsonify({'error': f'Error generating recipe: {str(e)}'}), 500

@app.route('/generate_recipe_from_text', methods=['POST'])
@login_required
def generate_recipe_from_text():
    try:
        # Get the text input from the request
        text_input = request.json.get('text')
        if not text_input:
            return jsonify({'error': 'No text provided'}), 400

        try:
            # Generate recipe using Gemini API with text and prompt
            response = client.models.generate_content(
                model="gemini-2.5-flash-preview-05-20",
                config={"response_mime_type": "application/json"},
                contents=[text_input, prompt_text]
            )

            if response.text:
                try:
                    # Convert Gemini's response text to a dictionary and return it
                    recipe_json = eval(response.text)
                    if not all(key in recipe_json for key in ['ingredients', 'steps', 'other_elements']):
                        return jsonify({'error': 'Invalid recipe format'}), 500
                    return jsonify(recipe_json)
                except Exception as e:
                    return jsonify({'error': f'Invalid JSON format: {str(e)}'}), 500
            else:
                return jsonify({'error': 'No response from Gemini API'}), 500

        except Exception as e:
            return jsonify({'error': f'Error calling Gemini API: {str(e)}'}), 500

    except Exception as e:
        return jsonify({'error': f'Error generating recipe: {str(e)}'}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)