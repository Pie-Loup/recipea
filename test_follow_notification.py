#!/usr/bin/env python3
"""
Script de test pour les nouvelles routes de notification de suivi
"""

import requests
import json

BASE_URL = "http://localhost:5001"

def test_vapid_key():
    """Test que la clé VAPID est accessible"""
    try:
        response = requests.get(f"{BASE_URL}/api/vapid-public-key")
        if response.status_code == 200:
            print("✅ Route VAPID accessible")
            print(f"   Clé publique: {response.json().get('publicKey', 'Non trouvée')[:20]}...")
            return True
        else:
            print(f"❌ Erreur route VAPID: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur de connexion VAPID: {e}")
        return False

def test_routes_exist():
    """Test que nos nouvelles routes existent et retournent une erreur d'authentification (ce qui est normal)"""
    routes_to_test = [
        "/api/send-follow-notification",
        "/api/notify-follow"
    ]
    
    for route in routes_to_test:
        try:
            response = requests.post(f"{BASE_URL}{route}", json={})
            # On s'attend à une erreur 401 (non authentifié) ou 302 (redirection)
            if response.status_code in [401, 302]:
                print(f"✅ Route {route} existe et demande l'authentification")
            elif response.status_code == 400:
                print(f"✅ Route {route} existe (erreur 400 = données manquantes)")
            else:
                print(f"⚠️  Route {route} retourne un code inattendu: {response.status_code}")
                print(f"   Réponse: {response.text[:100]}")
        except Exception as e:
            print(f"❌ Erreur pour la route {route}: {e}")

def main():
    print("🧪 Test des nouvelles routes de notification de suivi")
    print("=" * 50)
    
    print("\n1. Test de la clé VAPID:")
    test_vapid_key()
    
    print("\n2. Test de l'existence des nouvelles routes:")
    test_routes_exist()
    
    print("\n✅ Tests terminés!")
    print("\nPour tester complètement les routes, vous devez:")
    print("1. Être connecté avec un token Supabase valide")
    print("2. Avoir des utilisateurs dans la base de données")
    print("3. Avoir des souscriptions push actives")

if __name__ == "__main__":
    main()
