#!/usr/bin/env python3
"""
Script pour générer de nouvelles clés VAPID
"""

from pywebpush import webpush
import os

def generate_vapid_keys():
    """Génère de nouvelles clés VAPID"""
    try:
        # Générer les clés VAPID
        vapid_private_key, vapid_public_key = webpush.generate_vapid_keys()
        
        # Sauvegarder la clé privée
        with open('vapid_private.pem', 'w') as f:
            f.write(vapid_private_key)
        
        # Sauvegarder la clé publique
        with open('vapid_public.txt', 'w') as f:
            f.write(vapid_public_key)
        
        print("✅ Nouvelles clés VAPID générées:")
        print(f"📄 Clé privée sauvegardée dans: vapid_private.pem")
        print(f"📄 Clé publique sauvegardée dans: vapid_public.txt")
        print(f"\n🔑 Clé publique: {vapid_public_key}")
        print("\n⚠️  N'oubliez pas de mettre à jour vos variables d'environnement!")
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération des clés VAPID: {e}")

if __name__ == "__main__":
    generate_vapid_keys()
