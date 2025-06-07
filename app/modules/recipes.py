from flask import Blueprint, request, jsonify, render_template, redirect, url_for
import tempfile
import os
import json
import io
from pydub import AudioSegment
import threading
import uuid
import time
import httpx
from supabase import create_client
from modules.prompts import prompt_voice, prompt_text, prompt_photo, prompt_update

# Create a Blueprint for recipe-related routes
recipes_bp = Blueprint('recipes', __name__)

# These will be set when the blueprint is registered
_client = None
_supabase_config = None
_task_store = None
_verify_jwt_func = None
_login_required_decorator = None

def init_recipes_blueprint(client, supabase_anon_key, supabase_url, supabase_service_key, 
                          task_store, verify_jwt_func, login_required_decorator):
    """Initialize the recipes blueprint with dependencies from the main app"""
    global _client, _supabase_config, _task_store, _verify_jwt_func, _login_required_decorator
    _client = client
    _supabase_config = (supabase_anon_key, supabase_url, supabase_service_key)
    _task_store = task_store
    _verify_jwt_func = verify_jwt_func
    _login_required_decorator = login_required_decorator

def get_client():
    """Get the Gemini client"""
    return _client

def get_supabase_config():
    """Get Supabase configuration"""
    return _supabase_config

def get_task_store():
    """Get task store"""
    return _task_store

def verify_supabase_jwt(token):
    """Verify JWT token"""
    return _verify_jwt_func(token)

def login_required(f):
    """Apply login required decorator"""
    return _login_required_decorator(f)

def create_task(task_id, status='pending', result=None, error=None):
    """Create or update a task in the store"""
    task_store = get_task_store()
    task_store[task_id] = {
        'status': status,
        'result': result,
        'error': error,
        'created_at': time.time()
    }

def get_task(task_id):
    """Get a task from the store"""
    task_store = get_task_store()
    return task_store.get(task_id)

def cleanup_old_tasks():
    """Clean up tasks older than 1 hour"""
    task_store = get_task_store()
    current_time = time.time()
    to_remove = []
    for task_id, task in task_store.items():
        if current_time - task['created_at'] > 3600:  # 1 hour
            to_remove.append(task_id)
    
    for task_id in to_remove:
        del task_store[task_id]

# Synchronous functions for recipe generation
def _generate_recipe_from_voice_sync(audio_files_data):
    """Synchronous version of voice recipe generation"""
    client = get_client()
    
    # Create a temporary file for the combined audio
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
        # Initialize combined audio segment
        combined = None
        
        # Process each audio file data
        for audio_file_data in audio_files_data:
            # Create a BytesIO object from the saved data
            audio_data = io.BytesIO(audio_file_data['data'])
            # Load the audio segment
            segment = AudioSegment.from_file(audio_data)
            
            # Add to combined segment
            if combined is None:
                combined = segment
            else:
                combined += segment
        
        if combined:
            # Export the combined audio to the temporary file
            combined.export(temp_audio.name, format='wav')
            
            # Upload the combined file to Gemini
            audio_file = client.files.upload(file=temp_audio.name)

            # Generate recipe using Gemini API with file and prompt
            response = client.models.generate_content(
                model="gemini-2.5-flash-preview-05-20",
                config={"response_mime_type": "application/json"},
                contents=[audio_file, prompt_voice]
            )

            if response.text:
                # Convert Gemini's response text to a dictionary and return it directly
                recipe_json = json.loads(response.text)
                if not all(key in recipe_json for key in ['title', 'ingredients', 'steps', 'questions', 'is_recipe']):
                    raise ValueError('Invalid recipe format')
                return recipe_json
            else:
                raise ValueError('No response from Gemini API')
        else:
            raise ValueError('No valid audio files provided')
    
    # Clean up the temporary file
    try:
        os.unlink(temp_audio.name)
    except OSError:
        pass

def _generate_recipe_from_photo_sync(temp_file_path):
    """Synchronous version of photo recipe generation"""
    client = get_client()
    
    try:
        # Upload the photo to Gemini
        photo = client.files.upload(file=temp_file_path)

        # Generate recipe using Gemini API with photo and prompt
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-05-20",
            config={"response_mime_type": "application/json"},
            contents=[photo, prompt_photo]
        )

        if response.text:
            # Convert Gemini's response text to a dictionary and return it
            recipe_json = json.loads(response.text)
            if not all(key in recipe_json for key in ['title', 'ingredients', 'steps', 'other_elements', 'is_recipe']):
                raise ValueError('Invalid recipe format')
            return recipe_json
        else:
            raise ValueError('No response from Gemini API')
    finally:
        # Clean up the temporary file
        try:
            os.unlink(temp_file_path)
        except OSError:
            pass

def _generate_recipe_from_text_sync(text_input):
    """Synchronous version of text recipe generation"""
    client = get_client()
    
    # Generate recipe using Gemini API with text and prompt
    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-05-20",
        config={"response_mime_type": "application/json"},
        contents=[text_input, prompt_text]
    )

    if response.text:
        # Convert Gemini's response text to a dictionary and return it
        recipe_json = json.loads(response.text)
        if not all(key in recipe_json for key in ['title', 'ingredients', 'steps', 'other_elements', 'is_recipe']):
            raise ValueError('Invalid recipe format')
        return recipe_json
    else:
        raise ValueError('No response from Gemini API')

def _update_recipe_sync(recipe, user_comments):
    """Synchronous version of recipe update"""
    client = get_client()
    
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
        # Convert Gemini's response text to a dictionary and return it
        recipe_json = json.loads(response.text)
        if not all(key in recipe_json for key in ['ingredients', 'steps', 'other_elements']):
            raise ValueError('Invalid recipe format')
        return recipe_json
    else:
        raise ValueError('No response from Gemini API')

def generate_recipe_async(task_id, generation_type, **kwargs):
    """Generic async recipe generation function"""
    try:
        if generation_type == 'voice':
            result = _generate_recipe_from_voice_sync(**kwargs)
        elif generation_type == 'photo':
            result = _generate_recipe_from_photo_sync(**kwargs)
        elif generation_type == 'text':
            result = _generate_recipe_from_text_sync(**kwargs)
        elif generation_type == 'update':
            result = _update_recipe_sync(**kwargs)
        else:
            raise ValueError(f"Unknown generation type: {generation_type}")
        
        create_task(task_id, 'completed', result)
    except Exception as e:
        create_task(task_id, 'failed', error=str(e))

# Recipe generation routes
@recipes_bp.route('/generate_recipe_from_voice', methods=['POST'])
def generate_recipe_from_voice():
    # Apply login_required check manually
    token = request.cookies.get("sb-access-token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token or not verify_supabase_jwt(token):
        from flask import redirect, url_for
        return redirect(url_for('index'))
    
    try:
        # Get all audio files from the request
        audio_files = request.files.getlist('audio')
        if not audio_files:
            return jsonify({'error': 'No audio files provided'}), 400

        # Save audio files data to avoid request context issues
        audio_files_data = []
        for audio_file in audio_files:
            if audio_file.filename != '':
                # Read the file data into memory
                audio_data = audio_file.read()
                audio_files_data.append({
                    'data': audio_data,
                    'filename': audio_file.filename
                })
        
        if not audio_files_data:
            return jsonify({'error': 'No valid audio files provided'}), 400

        # Generate a unique task ID
        task_id = str(uuid.uuid4())
        
        # Create the task
        create_task(task_id, 'pending')
        
        # Start the async generation
        thread = threading.Thread(
            target=generate_recipe_async,
            args=(task_id, 'voice'),
            kwargs={'audio_files_data': audio_files_data}
        )
        thread.daemon = True
        thread.start()
        
        # Return the task ID for polling
        return jsonify({'task_id': task_id})

    except Exception as e:
        return jsonify({'error': f'Error generating recipe: {str(e)}'}), 500

@recipes_bp.route('/generate_recipe_from_photo', methods=['POST'])
def generate_recipe_from_photo():
    # Apply login_required check manually
    token = request.cookies.get("sb-access-token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token or not verify_supabase_jwt(token):
        from flask import redirect, url_for
        return redirect(url_for('index'))
    
    try:
        # Get the photo file from the request
        photo_file = request.files.get('photo')
        if not photo_file:
            return jsonify({'error': 'No photo provided'}), 400

        # Save the file data immediately to avoid request context issues
        temp_photo = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        try:
            photo_file.save(temp_photo.name)
            temp_photo.close()  # Close the file handle
            temp_file_path = temp_photo.name
        except Exception as e:
            if temp_photo:
                temp_photo.close()
            try:
                os.unlink(temp_photo.name)
            except:
                pass
            raise e

        # Generate a unique task ID
        task_id = str(uuid.uuid4())
        
        # Create the task
        create_task(task_id, 'pending')
        
        # Start the async generation
        thread = threading.Thread(
            target=generate_recipe_async,
            args=(task_id, 'photo'),
            kwargs={'temp_file_path': temp_file_path}
        )
        thread.daemon = True
        thread.start()
        
        # Return the task ID for polling
        return jsonify({'task_id': task_id})

    except Exception as e:
        return jsonify({'error': f'Error generating recipe: {str(e)}'}), 500

@recipes_bp.route('/generate_recipe_from_text', methods=['POST'])
def generate_recipe_from_text():
    # Apply login_required check manually
    token = request.cookies.get("sb-access-token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token or not verify_supabase_jwt(token):
        from flask import redirect, url_for
        return redirect(url_for('index'))
    
    try:
        # Get the text input from the request
        text_input = request.json.get('text')
        if not text_input:
            return jsonify({'error': 'No text provided'}), 400

        # Generate a unique task ID
        task_id = str(uuid.uuid4())
        
        # Create the task
        create_task(task_id, 'pending')
        
        # Start the async generation
        thread = threading.Thread(
            target=generate_recipe_async,
            args=(task_id, 'text'),
            kwargs={'text_input': text_input}
        )
        thread.daemon = True
        thread.start()
        
        # Return the task ID for polling
        return jsonify({'task_id': task_id})

    except Exception as e:
        return jsonify({'error': f'Error generating recipe: {str(e)}'}), 500

@recipes_bp.route('/update_recipe', methods=['POST'])
def update_recipe():
    # Apply login_required check manually
    token = request.cookies.get("sb-access-token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token or not verify_supabase_jwt(token):
        from flask import redirect, url_for
        return redirect(url_for('index'))
    
    try:
        # Get the recipe and user comments from the request
        data = request.json
        if not data or 'recipe' not in data or 'user_comments' not in data:
            return jsonify({'error': 'Missing recipe or user comments'}), 400

        recipe = data['recipe']
        user_comments = data['user_comments']

        # Generate a unique task ID
        task_id = str(uuid.uuid4())
        
        # Create the task
        create_task(task_id, 'pending')
        
        # Start the async generation
        thread = threading.Thread(
            target=generate_recipe_async,
            args=(task_id, 'update'),
            kwargs={'recipe': recipe, 'user_comments': user_comments}
        )
        thread.daemon = True
        thread.start()
        
        # Return the task ID for polling
        return jsonify({'task_id': task_id})

    except Exception as e:
        return jsonify({'error': f'Error updating recipe: {str(e)}'}), 500

# Route for polling task status
@recipes_bp.route('/api/task/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Get the status of an async task"""
    # Apply login_required check manually
    token = request.cookies.get("sb-access-token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token or not verify_supabase_jwt(token):
        from flask import redirect, url_for
        return redirect(url_for('index'))
    
    try:
        # Clean up old tasks first
        cleanup_old_tasks()
        
        task = get_task(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
            
        return jsonify({
            'status': task['status'],
            'result': task['result'],
            'error': task['error']
        })
    except Exception as e:
        return jsonify({'error': f'Error getting task status: {str(e)}'}), 500

@recipes_bp.route('/save_recipe', methods=['POST'])
def save_recipe():
    # Apply login_required check manually
    token = request.cookies.get("sb-access-token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token or not verify_supabase_jwt(token):
        from flask import redirect, url_for
        return redirect(url_for('index'))
    
    try:
        # Get recipe data from request
        data = request.json
        if not data or not all(key in data for key in ['title', 'ingredients', 'steps', 'origin']):
            return jsonify({'error': 'Missing required recipe data'}), 400

        # Get user id from JWT token using the verify_supabase_jwt function
        decoded = verify_supabase_jwt(token)
        if not decoded:
            return jsonify({'error': 'Invalid authentication token'}), 401
            
        user_id = decoded.get('sub')
        if not user_id:
            return jsonify({'error': 'User ID not found in token'}), 401

        # Setup Supabase client with auth headers
        supabase_anon_key, supabase_url, _ = get_supabase_config()
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

@recipes_bp.route('/api/feed/recipes', methods=['GET'])
def get_feed_recipes():
    import traceback
    # Apply login_required check manually
    token = request.cookies.get("sb-access-token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token or not verify_supabase_jwt(token):
        from flask import redirect, url_for
        return redirect(url_for('index'))
    
    try:
        # Setup Supabase client with auth headers
        supabase_anon_key, supabase_url, _ = get_supabase_config()
        supabase_client = create_client(supabase_url, supabase_anon_key)
        supabase_client.postgrest.auth(token)

        # Fetch the 10 most recent recipes with author information
        result = supabase_client.table('recipes') \
            .select('*, profiles!user_id(username)') \
            .order('created_at', desc=True) \
            .limit(10) \
            .execute()
        
        if not result.data:
            return jsonify([])

        return jsonify(result.data)

    except Exception as e:
        print(f"❌ Error in get_feed_recipes: {str(e)}")
        print(f"❌ Full traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Error fetching recipes: {str(e)}'}), 500

@recipes_bp.route('/api/recipe/<recipe_id>', methods=['GET'])
def get_recipe_detail(recipe_id):
    import traceback
    # Apply login_required check manually
    token = request.cookies.get("sb-access-token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token or not verify_supabase_jwt(token):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Setup Supabase client with auth headers
        supabase_anon_key, supabase_url, _ = get_supabase_config()
        supabase_client = create_client(supabase_url, supabase_anon_key)
        supabase_client.postgrest.auth(token)

        # Fetch the specific recipe with author information
        result = supabase_client.table('recipes') \
            .select('*, profiles!user_id(username)') \
            .eq('recipe_id', recipe_id) \
            .single() \
            .execute()
        
        if not result.data:
            return jsonify({'error': 'Recipe not found'}), 404

        return jsonify(result.data)

    except Exception as e:
        print(f"❌ Error in get_recipe_detail: {str(e)}")
        print(f"❌ Full traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Error fetching recipe: {str(e)}'}), 500

# Recipe creation page routes
@recipes_bp.route('/create-recipe')
def create_recipe():
    # Apply login_required check manually
    token = request.cookies.get("sb-access-token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token or not verify_supabase_jwt(token):
        from flask import redirect, url_for
        return redirect(url_for('index'))
    
    supabase_anon_key, supabase_url, _ = get_supabase_config()
    return render_template('create_recipe.html', supabase_anon_key=supabase_anon_key, supabase_url=supabase_url)

@recipes_bp.route('/create-recipe/photo')
def create_recipe_photo():
    # Apply login_required check manually
    token = request.cookies.get("sb-access-token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token or not verify_supabase_jwt(token):
        from flask import redirect, url_for
        return redirect(url_for('index'))
    
    supabase_anon_key, supabase_url, _ = get_supabase_config()
    return render_template('photo_recipe_generator.html', supabase_anon_key=supabase_anon_key, supabase_url=supabase_url)

@recipes_bp.route('/create-recipe/text')
def create_recipe_text():
    # Apply login_required check manually
    token = request.cookies.get("sb-access-token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token or not verify_supabase_jwt(token):
        from flask import redirect, url_for
        return redirect(url_for('index'))
    
    supabase_anon_key, supabase_url, _ = get_supabase_config()
    return render_template('text_recipe_generator.html', supabase_anon_key=supabase_anon_key, supabase_url=supabase_url)

@recipes_bp.route('/voice-recipe')
def voice_recipe():
    # Apply login_required check manually
    token = request.cookies.get("sb-access-token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token or not verify_supabase_jwt(token):
        from flask import redirect, url_for
        return redirect(url_for('index'))
    
    supabase_anon_key, supabase_url, _ = get_supabase_config()
    return render_template('voice_recipe_generator.html', supabase_anon_key=supabase_anon_key, supabase_url=supabase_url)
