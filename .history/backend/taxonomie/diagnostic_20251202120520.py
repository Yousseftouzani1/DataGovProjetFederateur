"""
Script de diagnostic pour identifier les problèmes
"""

import sys
import importlib

print("=" * 60)
print("DIAGNOSTIC DU MOTEUR DE DÉTECTION")
print("=" * 60)

# 1. Vérifier Python
print(f"\n✓ Version Python: {sys.version}")

# 2. Vérifier les imports
modules_required = [
    "fastapi",
    "uvicorn",
    "pydantic",
    "requests"
]

print("\n📦 Vérification des modules:")
all_ok = True
for module in modules_required:
    try:
        mod = importlib.import_module(module)
        version = getattr(mod, "__version__", "version inconnue")
        print(f"  ✓ {module}: {version}")
    except ImportError as e:
        print(f"  ✗ {module}: MANQUANT")
        all_ok = False

if not all_ok:
    print("\n⚠️  Modules manquants. Installez-les avec:")
    print("  pip install -r requirements.txt")
    sys.exit(1)

# 3. Vérifier le fichier taxonomie.json
print("\n📄 Vérification de la taxonomie:")
from pathlib import Path
import json

taxonomy_file = Path(__file__).parent / "taxonomie.json"
if taxonomy_file.exists():
    print(f"  ✓ Fichier trouvé: {taxonomy_file}")
    try:
        with open(taxonomy_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"  ✓ JSON valide: {len(data.get('categories', []))} catégories")
    except Exception as e:
        print(f"  ✗ Erreur de parsing: {e}")
else:
    print(f"  ⚠️  Fichier non trouvé (taxonomie embarquée sera utilisée)")

# 4. Tester l'import du moteur
print("\n🔧 Test d'import du moteur:")
try:
    import re
    from enum import Enum
    print("  ✓ Imports standards OK")
    
    # Tester une création simple
    class TestEngine:
        def __init__(self):
            self.patterns = {}
    
    engine = TestEngine()
    print("  ✓ Création d'objet OK")
    
except Exception as e:
    print(f"  ✗ Erreur: {e}")
    import traceback
    traceback.print_exc()

# 5. Test de port
print("\n🌐 Test de disponibilité du port:")
import socket

def check_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0

ports = [8000, 8001, 8002]
for port in ports:
    if check_port(port):
        print(f"  ⚠️  Port {port}: OCCUPÉ")
    else:
        print(f"  ✓ Port {port}: LIBRE")

# 6. Test de création du moteur réel
print("\n🎯 Test de création du moteur:")
try:
    # Simuler une taxonomie minimale
    test_taxonomy = {
        "categories": [
            {
                "class": "TEST",
                "class_en": "TEST",
                "type": "PII",
                "subclasses": [
                    {
                        "name": "Test",
                        "regex_patterns": ["\\btest\\b"],
                        "sensitivity_level": "low"
                    }
                ]
            }
        ]
    }
    
    # Compiler un pattern simple
    pattern = re.compile(r"\btest\b", re.IGNORECASE)
    test_text = "This is a test"
    matches = list(pattern.finditer(test_text))
    
    print(f"  ✓ Compilation regex OK: {len(matches)} match(es)")
    print(f"  ✓ Le moteur devrait fonctionner")
    
except Exception as e:
    print(f"  ✗ Erreur: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("DIAGNOSTIC TERMINÉ")
print("=" * 60)

print("\n📝 PROCHAINES ÉTAPES:")
print("  1. Si tous les tests sont ✓, essayez de démarrer le serveur:")
print("     python classifier.py")
print("  2. Regardez les messages d'erreur dans le terminal du serveur")
print("  3. Partagez-moi les erreurs si le serveur ne démarre pas")