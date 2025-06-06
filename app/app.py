from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify, render_template, redirect, url_for
from google import genai
import jwt
import httpx
from dotenv import load_dotenv
from notifications import notifications_bp
from recipes import recipes_bp, init_recipes_blueprint
import time

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

# Store for async tasks - in production, use Redis or a database
task_store = {}

def create_task(task_id, status='pending', result=None, error=None):
    """Create or update a task in the store"""
    task_store[task_id] = {
        'status': status,
        'result': result,
        'error': error,
        'created_at': time.time()
    }

def get_task(task_id):
    """Get a task from the store"""
    return task_store.get(task_id)

def cleanup_old_tasks():
    """Clean up tasks older than 1 hour"""
    current_time = time.time()
    to_remove = []
    for task_id, task in task_store.items():
        if current_time - task['created_at'] > 3600:  # 1 hour
            to_remove.append(task_id)
    
    for task_id in to_remove:
        del task_store[task_id]

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

# Register the notifications blueprint
app.register_blueprint(notifications_bp, url_prefix='/api')

# Initialize and register the recipes blueprint
init_recipes_blueprint(
    client, 
    supabase_anon_key, 
    supabase_url, 
    supabase_service_key,
    task_store, 
    verify_supabase_jwt, 
    login_required
)
app.register_blueprint(recipes_bp)

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

@app.route('/profile')
@login_required
def profile():
    token = request.cookies.get("sb-access-token")
    if not check_user_has_username(token):
        return redirect(url_for('username_setup'))
    return render_template('profile.html', 
                         supabase_anon_key=supabase_anon_key, 
                         supabase_url=supabase_url,
                         vapid_public_key=VAPID_PUBLIC_KEY)

@app.route('/camera')
@login_required
def camera():
    token = request.cookies.get("sb-access-token")
    if not check_user_has_username(token):
        return redirect(url_for('username_setup'))
    return render_template('camera.html', supabase_anon_key=supabase_anon_key, supabase_url=supabase_url)

@app.route('/user/<username>')
@login_required
def user_profile(username):
    token = request.cookies.get("sb-access-token")
    if not check_user_has_username(token):
        return redirect(url_for('username_setup'))
    return render_template('user_profile.html', 
                         username=username,
                         supabase_anon_key=supabase_anon_key, 
                         supabase_url=supabase_url,
                         vapid_public_key=VAPID_PUBLIC_KEY)

@app.route('/recipe/<recipe_id>')
@login_required
def recipe_detail(recipe_id):
    token = request.cookies.get("sb-access-token")
    if not check_user_has_username(token):
        return redirect(url_for('username_setup'))
    return render_template('recipe_detail.html', 
                         recipe_id=recipe_id,
                         supabase_anon_key=supabase_anon_key, 
                         supabase_url=supabase_url,
                         vapid_public_key=VAPID_PUBLIC_KEY)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True, threaded=True)