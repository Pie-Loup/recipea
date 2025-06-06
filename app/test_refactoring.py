#!/usr/bin/env python3
"""
Test script to verify the refactoring worked correctly
"""
import sys
from unittest.mock import MagicMock, patch
import ast

def mock_all_external_dependencies():
    """Mock all external dependencies to allow testing import structure"""
    mock_modules = [
        'supabase', 'pydub', 'google', 'google.cloud', 'google.cloud.texttospeech',
        'google.cloud.speech', 'google.cloud.translate_v2', 'PIL', 'PIL.Image',
        'vertexai', 'vertexai.generative_models', 'flask_login', 'pywebpush',
        'asyncio', 'threading', 'uuid', 'datetime', 'time'
    ]
    
    for module in mock_modules:
        if module not in sys.modules:
            sys.modules[module] = MagicMock()
    
    # Mock specific attributes that are used
    sys.modules['supabase'].create_client = MagicMock()
    sys.modules['vertexai.generative_models'].GenerativeModel = MagicMock()
    sys.modules['flask_login'].login_required = lambda f: f
    sys.modules['pywebpush'].webpush = MagicMock()
    sys.modules['pywebpush'].WebPushException = Exception

def check_syntax(filename):
    """Check if a file has valid Python syntax"""
    try:
        with open(filename, 'r') as f:
            content = f.read()
        ast.parse(content)
        print(f"✓ {filename}: Syntax is valid")
        return True
    except SyntaxError as e:
        print(f"✗ {filename}: Syntax error - {e}")
        return False
    except Exception as e:
        print(f"✗ {filename}: Error - {e}")
        return False

def check_imports():
    """Test the import structure"""
    try:
        print("\nTesting import structure...")
        
        # Test recipes.py import first (should work independently)
        import recipes
        print("✓ recipes.py imports successfully")
        
        # Test app.py import
        import app
        print("✓ app.py imports successfully")
        
        # Check if blueprint is registered
        flask_app = app.app
        blueprints = list(flask_app.blueprints.keys())
        print(f"✓ Registered blueprints: {blueprints}")
        
        if 'recipes' in blueprints:
            print("✓ Recipes blueprint is registered")
        else:
            print("✗ Recipes blueprint is NOT registered")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_routes():
    """Check if all expected routes are present"""
    try:
        import app
        flask_app = app.app
        
        routes = []
        for rule in flask_app.url_map.iter_rules():
            routes.append(f"{list(rule.methods)} {rule.rule}")
        
        print(f"\n✓ Total routes registered: {len(routes)}")
        
        # Expected recipe routes
        expected_recipe_routes = [
            '/generate_recipe_from_voice',
            '/generate_recipe_from_photo', 
            '/generate_recipe_from_text',
            '/update_recipe',
            '/api/task/<task_id>',
            '/save_recipe',
            '/api/feed/recipes',
            '/create-recipe',
            '/create-recipe/photo',
            '/create-recipe/text',
            '/voice-recipe'
        ]
        
        found_routes = []
        missing_routes = []
        
        for expected_route in expected_recipe_routes:
            route_found = False
            for route in routes:
                if expected_route.replace('<task_id>', '<string:task_id>') in route:
                    route_found = True
                    found_routes.append(expected_route)
                    break
            if not route_found:
                missing_routes.append(expected_route)
        
        print(f"✓ Recipe routes found: {len(found_routes)}")
        for route in found_routes:
            print(f"  - {route}")
        
        if missing_routes:
            print(f"✗ Missing routes: {len(missing_routes)}")
            for route in missing_routes:
                print(f"  - {route}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Route check error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Recipe Refactoring")
    print("=" * 40)
    
    # Mock dependencies
    mock_all_external_dependencies()
    
    # Test 1: Syntax check
    print("1. Checking syntax...")
    syntax_ok = True
    for filename in ['app.py', 'recipes.py']:
        if not check_syntax(filename):
            syntax_ok = False
    
    if not syntax_ok:
        print("❌ Syntax errors found!")
        return False
    
    # Test 2: Import structure
    print("\n2. Checking import structure...")
    if not check_imports():
        print("❌ Import structure test failed!")
        return False
    
    # Test 3: Route registration
    print("\n3. Checking route registration...")
    if not check_routes():
        print("❌ Route registration test failed!")
        return False
    
    print("\n" + "=" * 40)
    print("🎉 All tests passed! Refactoring successful!")
    print("\nSummary:")
    print("- ✅ Syntax is valid for both files")
    print("- ✅ No circular import issues")
    print("- ✅ Recipes blueprint is properly registered")
    print("- ✅ All recipe routes are available")
    print("- ✅ Code organization improved with separation of concerns")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
