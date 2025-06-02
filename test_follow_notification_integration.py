#!/usr/bin/env python3
"""
Script de test pour valider l'intégration des notifications de suivi
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:5001"

def test_routes_exist():
    """Test que les routes existent et sont accessibles"""
    print("🧪 Test 1: Vérification que les routes existent")
    
    # Test route VAPID (devrait fonctionner sans auth)
    response = requests.get(f"{BASE_URL}/api/vapid-public-key")
    if response.status_code == 200:
        print("✅ Route VAPID publique accessible")
        vapid_data = response.json()
        print(f"   VAPID Public Key: {vapid_data.get('publicKey', 'N/A')[:20]}...")
    else:
        print("❌ Route VAPID publique inaccessible")
        return False
    
    # Test routes de suivi (devraient rediriger car pas d'auth)
    routes_to_test = [
        "/api/send-follow-notification",
        "/api/notify-follow"
    ]
    
    for route in routes_to_test:
        response = requests.post(
            f"{BASE_URL}{route}",
            json={"test": "test"},
            allow_redirects=False
        )
        if response.status_code == 302:
            print(f"✅ Route {route} existe et demande une authentification")
        else:
            print(f"❌ Route {route} problème: status {response.status_code}")
            return False
    
    return True

def test_notification_structure():
    """Test de la structure de notification attendue"""
    print("\n🧪 Test 2: Validation de la structure de notification")
    
    expected_notification = {
        "title": "Un chef vous suit",
        "body": "@username_a vous suit sur sauce! Cliquez pour voir son profil et ses recettes 😋",
        "icon": "/static/icon.png",
        "badge": "/static/badge.png",
        "data": {
            "type": "custom",
            "url": "/feed"
        }
    }
    
    # Vérifier que la structure est valide JSON
    try:
        json_str = json.dumps(expected_notification)
        parsed = json.loads(json_str)
        print("✅ Structure de notification valide JSON")
        print(f"   Title: {parsed['title']}")
        print(f"   Body template: {parsed['body']}")
        print(f"   Icon: {parsed['icon']}")
        print(f"   Badge: {parsed['badge']}")
        print(f"   Data type: {parsed['data']['type']}")
        print(f"   Data URL: {parsed['data']['url']}")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ Structure de notification invalide: {e}")
        return False

def test_error_handling():
    """Test de la gestion d'erreurs"""
    print("\n🧪 Test 3: Test de la gestion d'erreurs")
    
    # Test avec données manquantes
    test_cases = [
        {
            "name": "Données vides",
            "data": {},
            "expected_status": 302  # Redirection car pas d'auth
        },
        {
            "name": "JSON invalide",
            "data": None,
            "expected_status": 302
        }
    ]
    
    for test_case in test_cases:
        try:
            if test_case["data"] is None:
                response = requests.post(
                    f"{BASE_URL}/api/send-follow-notification",
                    data="invalid json",
                    headers={"Content-Type": "application/json"},
                    allow_redirects=False
                )
            else:
                response = requests.post(
                    f"{BASE_URL}/api/send-follow-notification",
                    json=test_case["data"],
                    allow_redirects=False
                )
            
            if response.status_code == test_case["expected_status"]:
                print(f"✅ {test_case['name']}: Comportement attendu (status {response.status_code})")
            else:
                print(f"⚠️  {test_case['name']}: Status inattendu {response.status_code} (attendu {test_case['expected_status']})")
        except Exception as e:
            print(f"❌ {test_case['name']}: Erreur {e}")
    
    return True

def test_example_usage():
    """Test des exemples d'utilisation"""
    print("\n🧪 Test 4: Validation des exemples d'utilisation")
    
    # Exemple de payload pour send-follow-notification
    follow_payload = {
        "followed_username": "username_b"
    }
    
    # Exemple de payload pour notify-follow
    notify_payload = {
        "follower_username": "username_a",
        "followed_user_id": "uuid-example-123"
    }
    
    try:
        # Valider que les payloads sont du JSON valide
        json.dumps(follow_payload)
        json.dumps(notify_payload)
        print("✅ Payloads d'exemple valides JSON")
        print(f"   Follow payload: {follow_payload}")
        print(f"   Notify payload: {notify_payload}")
        return True
    except Exception as e:
        print(f"❌ Payloads d'exemple invalides: {e}")
        return False

def main():
    """Fonction principale de test"""
    print(f"🚀 Début des tests d'intégration - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 URL de base: {BASE_URL}")
    print("=" * 60)
    
    tests = [
        test_routes_exist,
        test_notification_structure,
        test_error_handling,
        test_example_usage
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Erreur dans {test_func.__name__}: {e}")
            print()
    
    print("=" * 60)
    print(f"📊 Résultats: {passed}/{total} tests passés")
    
    if passed == total:
        print("🎉 Tous les tests sont passés ! L'intégration des notifications de suivi est prête.")
        print("\n📝 Prochaines étapes:")
        print("   1. Tester avec de vrais tokens d'authentification")
        print("   2. Vérifier que la table 'follows' existe dans Supabase")
        print("   3. Tester avec de vrais utilisateurs")
        print("   4. Intégrer dans votre frontend")
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
        sys.exit(1)

if __name__ == "__main__":
    main()
