#!/usr/bin/env python3
"""
Script de test simple pour vérifier les endpoints de notification de suivi
"""

import requests
import json

BASE_URL = "http://localhost:5001"

def test_vapid_endpoint():
    """Test l'endpoint VAPID public key"""
    print("🔑 Test de l'endpoint VAPID...")
    try:
        response = requests.get(f"{BASE_URL}/api/vapid-public-key")
        if response.status_code == 200:
            data = response.json()
            if "publicKey" in data:
                print(f"✅ VAPID endpoint OK - Clé publique: {data['publicKey'][:20]}...")
                return True
            else:
                print("❌ Clé publique manquante dans la réponse")
        else:
            print(f"❌ Erreur {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
    return False

def test_notification_endpoints():
    """Test les endpoints de notification (sans auth)"""
    print("\n🔔 Test des endpoints de notification...")
    
    endpoints = [
        "/api/send-follow-notification",
        "/api/notify-follow"
    ]
    
    for endpoint in endpoints:
        try:
            # Test sans authentification - devrait rediriger
            response = requests.post(f"{BASE_URL}{endpoint}", 
                                   json={"test": "data"},
                                   allow_redirects=False)
            
            if response.status_code == 302:
                print(f"✅ {endpoint} - Redirection OK (authentification requise)")
            else:
                print(f"⚠️  {endpoint} - Code: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {endpoint} - Erreur: {e}")

def check_docker_status():
    """Vérifie si le serveur Docker répond"""
    print("🐳 Vérification du serveur...")
    try:
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code == 200:
            print("✅ Serveur accessible")
            return True
        else:
            print(f"⚠️  Serveur répond avec le code {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Serveur non accessible - Vérifiez que Docker est lancé")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
    return False

def main():
    print("🧪 Test des Endpoints de Notification de Suivi")
    print("=" * 50)
    
    if not check_docker_status():
        print("\n💡 Pour démarrer le serveur:")
        print("   cd /Users/pie-loup/molotov/sauce")
        print("   docker-compose up")
        return
    
    # Tests des endpoints
    test_vapid_endpoint()
    test_notification_endpoints()
    
    print("\n📝 Instructions pour test manuel complet:")
    print("1. Ouvrir http://localhost:5001")
    print("2. Se connecter avec deux comptes différents")
    print("3. Activer les notifications push")
    print("4. Tester le suivi d'utilisateur depuis /profile")
    print("5. Vérifier la réception des notifications")
    
    print("\n📚 Documentation complète: manual_test_guide.md")

if __name__ == "__main__":
    main()
