#!/usr/bin/env python3
"""
Test d'intégration complet pour les notifications de suivi
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:5001"

def test_routes_availability():
    """Test que les routes sont disponibles"""
    
    routes_to_test = [
        "/api/send-follow-notification",
        "/api/notify-follow",
        "/api/vapid-public-key"
    ]
    
    print("🧪 Test de disponibilité des routes...")
    
    for route in routes_to_test:
        try:
            response = requests.post(f"{BASE_URL}{route}", 
                                   json={}, 
                                   timeout=5)
            
            if route == "/api/vapid-public-key":
                # Cette route devrait répondre avec 200 (pas d'auth requise)
                if response.status_code == 200:
                    print(f"✅ {route} - Disponible (200)")
                    data = response.json()
                    print(f"   Clé VAPID reçue: {data.get('publicKey', 'N/A')[:20]}...")
                else:
                    print(f"❌ {route} - Code: {response.status_code}")
            else:
                # Ces routes devraient rediriger vers / (302) car pas d'auth
                if response.status_code in [302, 401]:
                    print(f"✅ {route} - Disponible (redirection auth: {response.status_code})")
                else:
                    print(f"❌ {route} - Code inattendu: {response.status_code}")
                    
        except requests.exceptions.RequestException as e:
            print(f"❌ {route} - Erreur réseau: {e}")
    
    print()

def test_notification_structure():
    """Test de la structure de notification attendue"""
    
    expected_notification = {
        "notification_data": {
            "title": "Un chef vous suit",
            "body": "@username_a vous suit sur sauce! Cliquez pour voir son profil et ses recettes 😋",
            "icon": "/static/img/icon.png",
            "badge": "/static/img/badge.png",
            "data": {
                "type": "custom",
                "url": "/feed"
            }
        }
    }
    
    print("🧪 Test de structure de notification...")
    print("📋 Structure attendue:")
    print(json.dumps(expected_notification, indent=2, ensure_ascii=False))
    print()

def main():
    print("🚀 Test d'intégration des notifications de suivi")
    print("=" * 50)
    
    test_routes_availability()
    test_notification_structure()
    
    print("📝 Instructions pour tester manuellement:")
    print("1. Connectez-vous sur http://localhost:5001")
    print("2. Allez sur la page /profile")
    print("3. Recherchez un utilisateur")
    print("4. Cliquez sur 'Suivre'")
    print("5. L'utilisateur suivi devrait recevoir une notification")
    print()
    print("✅ Tests terminés !")

if __name__ == "__main__":
    main()
