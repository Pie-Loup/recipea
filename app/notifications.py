import json
import jwt
from flask import Blueprint, request, jsonify, current_app
from pywebpush import webpush, WebPushException
from supabase import create_client
from urllib.parse import urlparse
import os

# Create a Blueprint for notification routes
notifications_bp = Blueprint('notifications', __name__)

def get_env_variable(var_name, default=None):
    """Get an environment variable or raise an error if not set."""
    value = os.environ.get(var_name, default)
    if value is None:
        raise RuntimeError(f"{var_name} is not set in environment variables and no default provided.")
    return value

def load_vapid_private_key():
    """Load VAPID private key from environment or file"""
    # Try to get from environment first
    vapid_key = os.environ.get('VAPID_PRIVATE_KEY')
    
    if vapid_key:
        # If it looks like a file path, read the file
        if vapid_key.endswith('.pem') and os.path.exists(vapid_key):
            with open(vapid_key, 'r') as f:
                key_content = f.read().strip()
                print("✅ VAPID private key loaded from file")
                return key_content
        else:
            # Return the key directly
            print("✅ VAPID private key loaded from environment variable")
            return vapid_key
    
    # Fallback to reading from vapid_private.pem file
    vapid_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'vapid_private.pem')
    if os.path.exists(vapid_file):
        with open(vapid_file, 'r') as f:
            key_content = f.read().strip()
            print(f"✅ VAPID private key loaded from file: {vapid_file}")
            return key_content
    
    raise RuntimeError("❌ VAPID_PRIVATE_KEY not found in environment or file")

# Load environment variables
supabase_url = get_env_variable('SUPABASE_URL')
supabase_service_key = get_env_variable('SUPABASE_SERVICE_KEY')
VAPID_PUBLIC_KEY = get_env_variable('VAPID_PUBLIC_KEY')
VAPID_PRIVATE_KEY = load_vapid_private_key()
CONTACT_EMAIL = get_env_variable('CONTACT_EMAIL', 'push.notifications@sauce.cool')

def get_vapid_claims(endpoint):
    """Generate VAPID claims with correct audience for the given endpoint"""
    parsed_url = urlparse(endpoint)
    audience = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    return {
        "sub": f"mailto:{CONTACT_EMAIL}",
        "aud": audience
    }

def verify_supabase_jwt(token):
    """Verify and decode Supabase JWT token"""
    try:
        SUPABASE_JWT_SECRET = get_env_variable("SUPABASE_JWT_SECRET")
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience=["authenticated"],
            options={"verify_exp": True}
        )
        return payload
    except Exception as e:
        print("Token verification failed:", str(e))
        return None

def login_required(f):
    """Decorator to require authentication for routes"""
    from functools import wraps
    from flask import redirect, url_for, current_app
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get("sb-access-token") or request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token or not verify_supabase_jwt(token):
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@notifications_bp.route('/vapid-public-key')
def get_vapid_public_key():
    return jsonify({"publicKey": VAPID_PUBLIC_KEY})

@notifications_bp.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    print("\n=== New Subscription Request ===")
    token = request.cookies.get("sb-access-token")
    print(f"Token present: {'yes' if token else 'no'}")
    
    try:
        decoded_token = verify_supabase_jwt(token)
        user_id = decoded_token['sub']
        print(f"Successfully decoded token. User ID: {user_id}")
    except Exception as e:
        print(f"Error decoding token: {str(e)}")
        return jsonify({"error": "Invalid token"}), 401
    
    subscription_data = request.get_json()
    print("\nReceived subscription data:")
    print(f"- endpoint: {subscription_data.get('endpoint', 'NOT FOUND')[:50]}...")
    print(f"- keys present: {', '.join(subscription_data.get('keys', {}).keys())}")
    
    if not subscription_data or not all(k in subscription_data for k in ('endpoint', 'keys')):
        print("Error: Missing required subscription data")
        return jsonify({"error": "Invalid subscription data: missing endpoint or keys"}), 400
    
    # Utiliser la clé service pour contourner RLS
    supabase = create_client(supabase_url, supabase_service_key)
    
    try:
        print("Checking if subscription exists")
        # Vérifier si la souscription existe déjà
        existing = supabase.table('push_subscriptions')\
            .select('id')\
            .eq('user_id', user_id)\
            .eq('endpoint', subscription_data['endpoint'])\
            .execute()
            
        subscription_data_db = {
            'user_id': user_id,
            'endpoint': subscription_data['endpoint'],
            'p256dh': subscription_data['keys']['p256dh'],
            'auth': subscription_data['keys']['auth']
        }
        
        if existing.data:
            print("Updating existing subscription")
            result = supabase.table('push_subscriptions')\
                .update(subscription_data_db)\
                .eq('user_id', user_id)\
                .eq('endpoint', subscription_data['endpoint'])\
                .execute()
        else:
            print("Inserting new subscription")
            result = supabase.table('push_subscriptions')\
                .insert(subscription_data_db)\
                .execute()
                
        print("Database operation result:", result)
        return jsonify({"message": "Successfully subscribed to push notifications"}), 201
    except Exception as e:
        print("Error subscribing to push notifications:")
        print(str(e))
        return jsonify({"error": str(e)}), 500

@notifications_bp.route('/send-notification', methods=['POST'])
@login_required
def send_notification():
    """Endpoint générique pour envoyer des notifications push"""
    try:
        # Récupérer l'ID de l'utilisateur connecté
        token = request.cookies.get('sb-access-token')
        if not token:
            return jsonify({"error": "Not authenticated"}), 401
            
        # Décoder le token pour obtenir l'ID utilisateur
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id = payload.get('sub')
        
        # Récupérer les données de notification depuis la requête
        request_data = request.get_json()
        if not request_data or 'notification_data' not in request_data:
            return jsonify({"error": "Missing notification_data in request"}), 400
        
        notification_data = request_data['notification_data']
        
        # Valider les données de notification requises
        if not notification_data or not isinstance(notification_data, dict):
            return jsonify({"error": "notification_data must be a valid dictionary"}), 400
        
        if 'title' not in notification_data or 'body' not in notification_data:
            return jsonify({"error": "notification_data must contain at least 'title' and 'body'"}), 400
        
        # Créer une connexion Supabase avec la clé service pour contourner RLS
        supabase = create_client(supabase_url, supabase_service_key)
        
        # Récupérer les souscriptions push de l'utilisateur
        subscriptions = supabase.table('push_subscriptions')\
            .select('*')\
            .eq('user_id', user_id)\
            .execute()
        
        if not subscriptions.data:
            return jsonify({"message": "No push subscriptions found. Please enable notifications first."}), 200
        
        # Envoyer la notification à toutes les souscriptions de l'utilisateur
        notifications_sent = 0
        for subscription in subscriptions.data:
            try:
                # Generate VAPID claims with correct audience for this endpoint
                vapid_claims = get_vapid_claims(subscription['endpoint'])
                
                print(f"Sending push notification to endpoint: {subscription['endpoint'][:50]}...")
                print(f"VAPID claims: {vapid_claims}")
                
                webpush(
                    subscription_info={
                        "endpoint": subscription['endpoint'],
                        "keys": {
                            "p256dh": subscription['p256dh'],
                            "auth": subscription['auth']
                        }
                    },
                    data=json.dumps(notification_data),
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims=vapid_claims
                )
                notifications_sent += 1
                print(f"✅ Successfully sent notification to subscription {subscription['id']}")
            except WebPushException as e:
                print(f"❌ WebPush failed for subscription {subscription['id']}: {e}")
                print(f"Response status: {e.response.status_code if e.response else 'No response'}")
                print(f"Response body: {e.response.text if e.response else 'No response body'}")
                if e.response and e.response.status_code in [404, 410]:
                    # Supprimer la souscription invalide
                    print(f"🗑️ Removing invalid subscription {subscription['id']}")
                    supabase.table('push_subscriptions')\
                        .delete()\
                        .eq('id', subscription['id'])\
                        .execute()
            except Exception as e:
                print(f"❌ Unexpected error sending push notification: {e}")
                import traceback
                traceback.print_exc()
        
        return jsonify({
            "message": f"Notification sent successfully to {notifications_sent} device(s)",
            "subscriptions_found": len(subscriptions.data),
            "notifications_sent": notifications_sent
        }), 200
        
    except Exception as e:
        print(f"Error sending notification: {e}")
        return jsonify({"error": str(e)}), 500

@notifications_bp.route('/unsubscribe', methods=['POST'])
@login_required
def unsubscribe():
    """Endpoint pour désabonner l'utilisateur des notifications push"""
    try:
        # Récupérer l'ID de l'utilisateur connecté
        token = request.cookies.get('sb-access-token')
        if not token:
            return jsonify({"error": "Not authenticated"}), 401
            
        # Décoder le token pour obtenir l'ID utilisateur
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id = payload.get('sub')
        
        # Récupérer les données de l'abonnement depuis le frontend
        subscription_data = request.get_json()
        if not subscription_data or 'endpoint' not in subscription_data:
            return jsonify({"error": "Missing subscription endpoint"}), 400
        
        # Créer une connexion Supabase avec la clé service pour contourner RLS
        supabase = create_client(supabase_url, supabase_service_key)
        
        # Supprimer l'abonnement de la base de données
        result = supabase.table('push_subscriptions')\
            .delete()\
            .eq('user_id', user_id)\
            .eq('endpoint', subscription_data['endpoint'])\
            .execute()
        
        print(f"Unsubscribe result: {result}")
        
        return jsonify({
            "message": "Successfully unsubscribed from push notifications",
            "deleted_count": len(result.data) if result.data else 0
        }), 200
        
    except Exception as e:
        print(f"Error unsubscribing from push notifications: {e}")
        return jsonify({"error": str(e)}), 500

def send_follow_notification(follower_username, followed_user_id):
    """
    Fonction interne pour envoyer une notification de suivi
    """
    try:
        # Créer une connexion Supabase avec la clé service pour contourner RLS
        supabase = create_client(supabase_url, supabase_service_key)
        
        # Récupérer les souscriptions push de l'utilisateur suivi
        subscriptions = supabase.table('push_subscriptions')\
            .select('*')\
            .eq('user_id', followed_user_id)\
            .execute()
        
        if not subscriptions.data:
            print(f"No push subscriptions found for user {followed_user_id}")
            return False
        
        # Données de la notification de suivi
        notification_data = {
            "title": "Un chef vous suit",
            "body": f"@{follower_username} vous suit sur sauce! Cliquez pour voir son profil et ses recettes 😋",
            "icon": "/static/icon.png",
            "badge": "/static/badge.png",
            "data": {
                "type": "custom",
                "url": "/feed"
            }
        }
        
        # Envoyer la notification à toutes les souscriptions de l'utilisateur suivi
        notifications_sent = 0
        for subscription in subscriptions.data:
            try:
                # Generate VAPID claims with correct audience for this endpoint
                vapid_claims = get_vapid_claims(subscription['endpoint'])
                
                print(f"Sending follow notification to endpoint: {subscription['endpoint'][:50]}...")
                print(f"VAPID claims: {vapid_claims}")
                
                webpush(
                    subscription_info={
                        "endpoint": subscription['endpoint'],
                        "keys": {
                            "p256dh": subscription['p256dh'],
                            "auth": subscription['auth']
                        }
                    },
                    data=json.dumps(notification_data),
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims=vapid_claims
                )
                notifications_sent += 1
                print(f"✅ Successfully sent follow notification to subscription {subscription['id']}")
            except WebPushException as e:
                print(f"❌ WebPush failed for subscription {subscription['id']}: {e}")
                print(f"Response status: {e.response.status_code if e.response else 'No response'}")
                print(f"Response body: {e.response.text if e.response else 'No response body'}")
                if e.response and e.response.status_code in [404, 410]:
                    # Supprimer la souscription invalide
                    print(f"🗑️ Removing invalid subscription {subscription['id']}")
                    supabase.table('push_subscriptions')\
                        .delete()\
                        .eq('id', subscription['id'])\
                        .execute()
            except Exception as e:
                print(f"❌ Unexpected error sending follow notification: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"Follow notification sent to {notifications_sent} device(s) for user {followed_user_id}")
        return notifications_sent > 0
        
    except Exception as e:
        print(f"Error sending follow notification: {e}")
        import traceback
        traceback.print_exc()
        return False

@notifications_bp.route('/send-follow-notification', methods=['POST'])
@login_required
def send_follow_notification_endpoint():
    """Endpoint pour envoyer une notification de suivi quand un utilisateur suit un autre"""
    try:
        # Récupérer l'ID de l'utilisateur connecté (celui qui suit)
        token = request.cookies.get('sb-access-token')
        if not token:
            return jsonify({"error": "Not authenticated"}), 401
            
        # Décoder le token pour obtenir l'ID utilisateur
        follower_payload = verify_supabase_jwt(token)
        if not follower_payload:
            return jsonify({"error": "Invalid token"}), 401
            
        follower_user_id = follower_payload.get('sub')
        
        # Récupérer les données depuis la requête
        request_data = request.get_json()
        if not request_data:
            return jsonify({"error": "Missing request data"}), 400
        
        followed_username = request_data.get('followed_username')
        if not followed_username:
            return jsonify({"error": "Missing followed_username"}), 400
        
        # Créer une connexion Supabase avec la clé service pour contourner RLS
        supabase = create_client(supabase_url, supabase_service_key)
        
        # Récupérer le profil de l'utilisateur qui suit pour obtenir son username
        follower_profile = supabase.table('user_profiles')\
            .select('username')\
            .eq('id', follower_user_id)\
            .execute()
        
        if not follower_profile.data:
            return jsonify({"error": "Follower profile not found"}), 404
        
        follower_username = follower_profile.data[0]['username']
        
        # Récupérer l'ID de l'utilisateur suivi à partir de son username
        followed_profile = supabase.table('user_profiles')\
            .select('id')\
            .eq('username', followed_username)\
            .execute()
        
        if not followed_profile.data:
            return jsonify({"error": "Followed user not found"}), 404
        
        followed_user_id = followed_profile.data[0]['id']
        
        # Vérifier si l'utilisateur ne se suit pas lui-même
        if follower_user_id == followed_user_id:
            return jsonify({"error": "You cannot follow yourself"}), 400
        
        # Vérifier si la relation de suivi existe déjà
        existing_follow = supabase.table('follows')\
            .select('id')\
            .eq('follower_id', follower_user_id)\
            .eq('following_id', followed_user_id)\
            .execute()
        
        if existing_follow.data:
            return jsonify({"message": "Already following this user"}), 200
        
        # Créer la relation de suivi
        follow_result = supabase.table('follows')\
            .insert({
                'follower_id': follower_user_id,
                'following_id': followed_user_id
            })\
            .execute()
        
        if not follow_result.data:
            return jsonify({"error": "Failed to create follow relationship"}), 500
        
        # Envoyer la notification
        notification_sent = send_follow_notification(follower_username, followed_user_id)
        
        if notification_sent:
            return jsonify({
                "message": f"Successfully followed @{followed_username} and notification sent",
                "followed_user": followed_username,
                "follower_user": follower_username
            }), 201
        else:
            return jsonify({
                "message": f"Successfully followed @{followed_username} but no notification could be sent (user may not have notifications enabled)",
                "followed_user": followed_username,
                "follower_user": follower_username
            }), 201
        
    except Exception as e:
        print(f"Error in follow endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@notifications_bp.route('/notify-follow', methods=['POST'])
@login_required
def notify_follow_only():
    """Endpoint pour envoyer uniquement la notification de suivi (sans créer la relation de suivi)"""
    try:
        # Récupérer les données depuis la requête
        request_data = request.get_json()
        if not request_data:
            return jsonify({"error": "Missing request data"}), 400
        
        follower_username = request_data.get('follower_username')
        followed_user_id = request_data.get('followed_user_id')
        
        if not follower_username or not followed_user_id:
            return jsonify({"error": "Missing follower_username or followed_user_id"}), 400
        
        # Envoyer la notification
        notification_sent = send_follow_notification(follower_username, followed_user_id)
        
        if notification_sent:
            return jsonify({
                "message": f"Follow notification sent successfully to user {followed_user_id}",
                "follower_username": follower_username,
                "followed_user_id": followed_user_id
            }), 200
        else:
            return jsonify({
                "message": f"No notification could be sent to user {followed_user_id} (user may not have notifications enabled)",
                "follower_username": follower_username,
                "followed_user_id": followed_user_id
            }), 200
        
    except Exception as e:
        print(f"Error in notify-follow endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Service worker route
@notifications_bp.route('/sw.js')
def service_worker():
    response = current_app.send_file('sw.js')
    # Ajouter les headers de cache appropriés
    response.headers['Cache-Control'] = 'no-cache'
    return response