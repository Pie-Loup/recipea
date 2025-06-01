from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify, render_template, redirect, url_for
import tempfile
from google import genai
import json
from pydub import AudioSegment
import io
import jwt
import httpx
from dotenv import load_dotenv
from prompts import prompt_voice, prompt_text, prompt_photo, prompt_update
from supabase import create_client
from notifications import notifications_bp

load_dotenv()

def get_env_variable(var_name, default=None):
    """Get an environment variable or raise an error if not set."""
    value = os.environ.get(var_name, default)
    if value is None:
        raise RuntimeError(f"{var_name} is not set in environment variables and no default provided.")
    return value

# Load environment variables
GEMINI_API_KEY = get_env_variable("GEMINI_API_KEY")

SUPABASE_JWT_SECRET = get_env_variable("SUPABASE_JWT_SECRET")
SUPABASE_PROJECT_ID = get_env_variable("SUPABASE_PROJECT_ID")
supabase_anon_key = get_env_variable('SUPABASE_ANON_KEY')
supabase_url = get_env_variable('SUPABASE_URL')
supabase_service_key = get_env_variable('SUPABASE_SERVICE_KEY')

VAPID_PUBLIC_KEY = get_env_variable('VAPID_PUBLIC_KEY')

app = Flask(__name__)
client = genai.Client(api_key=GEMINI_API_KEY)

# Register the notifications blueprint
app.register_blueprint(notifications_bp, url_prefix='/api')

def verify_supabase_jwt(token):
    try:
        # Note: Supabase JWTs use HS256 algorithm and have specific claims
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience=["authenticated"],
            options={"verify_exp": True}
        )
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
                         site_url=site_url,
                         vapid_public_key=VAPID_PUBLIC_KEY)

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
    return render_template('feed.html', 
                         supabase_anon_key=supabase_anon_key, 
                         supabase_url=supabase_url,
                         vapid_public_key=VAPID_PUBLIC_KEY)

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
                            recipe_json = json.loads(response.text)
                            if not all(key in recipe_json for key in ['title', 'ingredients', 'steps', 'questions', 'is_recipe']):
                                return jsonify({'error': 'Invalid recipe format'}), 500
                            # If it's not a recipe, return directly to ask user to try again
                            if not recipe_json.get('is_recipe', False):
                                return jsonify(recipe_json)  # Frontend will show message to try again
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
                        recipe_json = json.loads(response.text)
                        if not all(key in recipe_json for key in ['title', 'ingredients', 'steps', 'other_elements', 'is_recipe']):
                            return jsonify({'error': 'Invalid recipe format'}), 500
                        # If it's not a recipe, return directly to ask user to try again
                        if not recipe_json.get('is_recipe', False):
                            return jsonify(recipe_json)  # Frontend will show message to try again
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
                    recipe_json = json.loads(response.text)
                    if not all(key in recipe_json for key in ['title', 'ingredients', 'steps', 'other_elements', 'is_recipe']):
                        return jsonify({'error': 'Invalid recipe format'}), 500
                    # If it's not a recipe, return directly to ask user to try again
                    if not recipe_json.get('is_recipe', False):
                        return jsonify(recipe_json)  # Frontend will show message to try again
                    return jsonify(recipe_json)
                except Exception as e:
                    return jsonify({'error': f'Invalid JSON format: {str(e)}'}), 500
            else:
                return jsonify({'error': 'No response from Gemini API'}), 500

        except Exception as e:
            return jsonify({'error': f'Error calling Gemini API: {str(e)}'}), 500

    except Exception as e:
        return jsonify({'error': f'Error generating recipe: {str(e)}'}), 500

@app.route('/update_recipe', methods=['POST'])
@login_required
def update_recipe():
    try:
        # Get the recipe and user comments from the request
        data = request.json
        if not data or 'recipe' not in data or 'user_comments' not in data:
            return jsonify({'error': 'Missing recipe or user comments'}), 400

        recipe = data['recipe']
        user_comments = data['user_comments']

        try:
            # Convert recipe dict to structured text
            recipe_text = f"""Voici la recette actuelle:

Ingrédients:
{chr(10).join(f"- {i}" for i in recipe['ingredients'])}

Étapes:
{chr(10).join(f"{i+1}. {s}" for i, s in enumerate(recipe['steps']))}

Autres éléments:
{chr(10).join(f"- {e}" for e in recipe.get('other_elements', []))}
"""

            # Generate updated recipe using Gemini API with recipe text, comments and prompt
            response = client.models.generate_content(
                model="gemini-2.5-flash-preview-05-20",
                config={"response_mime_type": "application/json"},
                contents=[recipe_text, user_comments, prompt_update]
            )

            if response.text:
                try:
                    # Convert Gemini's response text to a dictionary and return it
                    recipe_json = json.loads(response.text)
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
        return jsonify({'error': f'Error updating recipe: {str(e)}'}), 500

@app.route('/save_recipe', methods=['POST'])
@login_required
def save_recipe():
    try:
        # Get recipe data from request
        data = request.json
        if not data or not all(key in data for key in ['title', 'ingredients', 'steps', 'origin']):
            return jsonify({'error': 'Missing required recipe data'}), 400

        # Get the user's supabase JWT token
        token = request.cookies.get("sb-access-token")
        if not token:
            return jsonify({'error': 'Not authenticated'}), 401

        # Get user id from JWT token using the verify_supabase_jwt function
        decoded = verify_supabase_jwt(token)
        if not decoded:
            return jsonify({'error': 'Invalid authentication token'}), 401
            
        user_id = decoded.get('sub')
        if not user_id:
            return jsonify({'error': 'User ID not found in token'}), 401

        # Setup Supabase client with auth headers
        supabase_client = create_client(supabase_url, supabase_anon_key)
        # Set the Authorization header for the request
        supabase_client.postgrest.auth(token)

        # Insert the recipe into the database
        recipe_data = {
            'title': data['title'],
            'ingredients': data['ingredients'],
            'steps': data['steps'],
            'other_elements': data.get('other_elements', []),
            'state': 'to_test',
            'origin': data['origin'],
            'user_id': user_id
        }

        result = supabase_client.table('recipes').insert(recipe_data).execute()
        
        if result.data:
            return jsonify({'success': True, 'recipe_id': result.data[0]['recipe_id']})
        else:
            return jsonify({'error': 'Failed to save recipe'}), 500

    except Exception as e:
        return jsonify({'error': f'Error saving recipe: {str(e)}'}), 500

@app.route('/api/feed/recipes', methods=['GET'])
@login_required
def get_feed_recipes():
    try:
        # Get the user's supabase JWT token
        token = request.cookies.get("sb-access-token")
        if not token:
            return jsonify({'error': 'Not authenticated'}), 401

        # Setup Supabase client with auth headers
        supabase_client = create_client(supabase_url, supabase_anon_key)
        supabase_client.postgrest.auth(token)

        # Fetch the 10 most recent recipes with author information
        result = supabase_client.table('recipes') \
            .select('*, user_profiles!user_id(username)') \
            .order('created_at', desc=True) \
            .limit(10) \
            .execute()
        
        if not result.data:
            return jsonify([])

        return jsonify(result.data)

    except Exception as e:
        return jsonify({'error': f'Error fetching recipes: {str(e)}'}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)