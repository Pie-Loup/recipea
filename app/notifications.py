import json
import jwt
from flask import Blueprint, request, jsonify, current_app
from pywebpush import webpush, WebPushException
from supabase import create_client
import os

# Create a Blueprint for notification routes
notifications_bp = Blueprint('notifications', __name__)

def get_env_variable(var_name, default=None):
    """Get an environment variable or raise an error if not set."""
    value = os.environ.get(var_name, default)
    if value is None:
        raise RuntimeError(f"{var_name} is not set in environment variables and no default provided.")
    return value

# Load environment variables
supabase_url = get_env_variable('SUPABASE_URL')
supabase_service_key = get_env_variable('SUPABASE_SERVICE_KEY')
VAPID_PUBLIC_KEY = get_env_variable('VAPID_PUBLIC_KEY')
VAPID_PRIVATE_KEY = get_env_variable('VAPID_PRIVATE_KEY')
VAPID_CLAIMS = {
    "sub": f"mailto:{get_env_variable('CONTACT_EMAIL', 'push.notifications@sauce.cool')}"
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

@notifications_bp.route('/test-notification', methods=['POST'])
@login_required
def test_notification():
    """Endpoint pour tester les notifications push"""
    try:
        # Récupérer l'ID de l'utilisateur connecté
        token = request.cookies.get('sb-access-token')
        if not token:
            return jsonify({"error": "Not authenticated"}), 401
            
        # Décoder le token pour obtenir l'ID utilisateur
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id = payload.get('sub')
        
        # Créer une connexion Supabase avec la clé service pour contourner RLS
        supabase = create_client(supabase_url, supabase_service_key)
        
        # Récupérer les souscriptions push de l'utilisateur
        subscriptions = supabase.table('push_subscriptions')\
            .select('*')\
            .eq('user_id', user_id)\
            .execute()
        
        if not subscriptions.data:
            return jsonify({"message": "No push subscriptions found. Please enable notifications first."}), 200
        
        # Préparer une notification de test
        notification_data = {
            "title": "🧪 Test Notification",
            "body": "Ceci est un test de notification push. Si vous voyez ceci, ça fonctionne !",
            "icon": "/static/icon.png",
            "badge": "/static/badge.png",
            "data": {
                "type": "test",
                "url": "/feed"
            }
        }
        
        # Envoyer la notification à toutes les souscriptions de l'utilisateur
        notifications_sent = 0
        for subscription in subscriptions.data:
            try:
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
                    vapid_claims=VAPID_CLAIMS
                )
                notifications_sent += 1
            except WebPushException as e:
                print(f"WebPush failed for subscription {subscription['id']}: {e}")
                if e.response and e.response.status_code in [404, 410]:
                    # Supprimer la souscription invalide
                    supabase.table('push_subscriptions')\
                        .delete()\
                        .eq('id', subscription['id'])\
                        .execute()
        
        return jsonify({
            "message": f"Test notification sent successfully to {notifications_sent} device(s)",
            "subscriptions_found": len(subscriptions.data),
            "notifications_sent": notifications_sent
        }), 200
        
    except Exception as e:
        print(f"Error sending test notification: {e}")
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

# Service worker route
@notifications_bp.route('/sw.js')
def service_worker():
    response = current_app.send_file('sw.js')
    # Ajouter les headers de cache appropriés
    response.headers['Cache-Control'] = 'no-cache'
    return response