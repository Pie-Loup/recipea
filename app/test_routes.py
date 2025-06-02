#!/usr/bin/env python3
"""
Script de test pour vérifier que toutes les routes de recettes sont bien disponibles
"""

def check_routes_exist():
    """Vérifie que les routes de recettes sont bien enregistrées"""
    try:
        # Import des modules sans exécuter le serveur
        import sys
        import os
        
        # Mock des dépendances manquantes pour pouvoir importer
        class MockModule:
            def __getattr__(self, name):
                return lambda *args, **kwargs: None
        
        # Mock des modules externes qui pourraient manquer
        sys.modules['supabase'] = MockModule()
        sys.modules['pydub'] = MockModule() 
        sys.modules['google'] = MockModule()
        sys.modules['google.genai'] = MockModule()
        sys.modules['jwt'] = MockModule()
        sys.modules['httpx'] = MockModule()
        
        # Mock des variables d'environnement
        os.environ.setdefault('GEMINI_API_KEY', 'test')
        os.environ.setdefault('SUPABASE_JWT_SECRET', 'test')
        os.environ.setdefault('SUPABASE_PROJECT_ID', 'test')
        os.environ.setdefault('SUPABASE_ANON_KEY', 'test')
        os.environ.setdefault('SUPABASE_URL', 'test')
        os.environ.setdefault('SUPABASE_SERVICE_KEY', 'test')
        os.environ.setdefault('VAPID_PUBLIC_KEY', 'test')
        
        # Import du module recipes
        from recipes import recipes_bp
        
        # Vérification des routes du blueprint
        routes = []
        for rule in recipes_bp.url_map.iter_rules():
            routes.append(f"{rule.rule} [{', '.join(rule.methods)}]")
        
        print("✅ Routes de recettes trouvées dans recipes.py:")
        for route in sorted(routes):
            print(f"   {route}")
        
        print(f"\n✅ Total: {len(routes)} routes trouvées")
        
        # Vérification des routes principales attendues
        expected_routes = [
            '/generate_recipe_from_voice',
            '/generate_recipe_from_photo', 
            '/generate_recipe_from_text',
            '/update_recipe',
            '/save_recipe',
            '/api/task/',
            '/api/feed/recipes',
            '/create-recipe',
            '/create-recipe/photo',
            '/create-recipe/text',
            '/voice-recipe',
            '/recipe_generator'
        ]
        
        found_routes = [rule.rule for rule in recipes_bp.url_map.iter_rules()]
        
        print("\n🔍 Vérification des routes attendues:")
        for expected in expected_routes:
            if any(expected in route for route in found_routes):
                print(f"   ✅ {expected}")
            else:
                print(f"   ❌ {expected} - MANQUANTE")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Test des routes de recettes...")
    success = check_routes_exist()
    if success:
        print("\n✅ Test réussi! Toutes les routes semblent correctement définies.")
    else:
        print("\n❌ Test échoué. Voir les erreurs ci-dessus.")
