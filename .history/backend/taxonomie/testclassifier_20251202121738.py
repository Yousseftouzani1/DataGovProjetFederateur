"""
Script de test pour le moteur de détection PII/SPI
"""

import requests
import json

# Configuration
API_URL = "http://127.0.0.1:8001"

# Textes de test avec données sensibles marocaines
TEST_TEXTS = [
    {
        "name": "Test 1: Identité personnelle",
        "text": """
        Bonjour, je m'appelle Ahmed Bennani et ma CIN est AB123456.
        Je suis né le 15/03/1985 à Casablanca.
        """
    },
    {
        "name": "Test 2: Coordonnées",
        "text": """
        Vous pouvez me joindre au 0612345678 ou par email à ahmed.bennani@gmail.com
        Mon adresse est 25, Rue Hassan II, 20000 Casablanca
        """
    },
    {
        "name": "Test 3: Données financières",
        "text": """
        Mon RIB est MA64001234567890123456789012
        Ma carte bancaire se termine par 4532 1234 5678 9010
        """
    },
    {
        "name": "Test 4: Données mixtes",
        "text": """
        Dossier patient: Fatima El Amrani
        CIN: CD987654
        Date de naissance: 22/07/1990
        Téléphone: +212661234567
        Email: fatima.elamrani@hotmail.com
        Groupe sanguin: O+
        Code Massar (enfant): M123456789
        """
    },
    {
        "name": "Test 5: Sans données sensibles",
        "text": """
        Bonjour, nous organisons une réunion demain à 14h.
        Merci de confirmer votre présence.
        """
    }
]

def test_health():
    """Test de l'endpoint health"""
    print("\n" + "="*60)
    print("TEST: Health Check")
    print("="*60)
    
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(" Service opérationnel")
            print(f"   Patterns: {data.get('patterns_count', 0)}")
            print(f"   Mots-clés: {data.get('keywords_count', 0)}")
            return True
        else:
            print(f" Erreur: {response.status_code}")
            return False
    except Exception as e:
        print(f" Impossible de contacter l'API: {e}")
        return False

def test_categories():
    """Test de l'endpoint categories"""
    print("\n" + "="*60)
    print("TEST: Catégories disponibles")
    print("="*60)
    
    try:
        response = requests.get(f"{API_URL}/categories")
        if response.status_code == 200:
            data = response.json()
            print(" Catégories chargées:")
            for cat in data.get("categories", []):
                print(f"   - {cat['name']} ({cat['type']}) - {cat['subclasses_count']} sous-classes")
            return True
        else:
            print(f" Erreur: {response.status_code}")
            return False
    except Exception as e:
        print(f" Erreur: {e}")
        return False

def test_analyze():
    """Test de l'endpoint analyze avec différents textes"""
    print("\n" + "="*60)
    print("TEST: Analyse de textes")
    print("="*60)
    
    for test in TEST_TEXTS:
        print(f"\n {test['name']}")
        print("-" * 60)
        print(f"Texte: {test['text'][:100]}...")
        
        try:
            response = requests.post(
                f"{API_URL}/analyze",
                json={
                    "text": test["text"],
                    "language": "fr",
                    "anonymize": True,
                    "confidence_threshold": 0.5
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"\n Détections: {data['detections_count']}")
                print(f"   Temps: {data['execution_time_ms']} ms")
                
                if data['detections_count'] > 0:
                    print(f"\n   Résumé par catégorie:")
                    for category, count in data['summary'].items():
                        print(f"   - {category}: {count}")
                    
                    print(f"\n   Détails:")
                    for detection in data['detections']:
                        print(f"   • {detection['entity_type']}")
                        print(f"     Valeur: {detection['value']}")
                        print(f"     Sensibilité: {detection['sensitivity_level']}")
                        print(f"     Confiance: {detection['confidence_score']:.2f}")
                        print(f"     Méthode: {detection['detection_method']}")
                        if detection.get('anonymized_value'):
                            print(f"     Anonymisé: {detection['anonymized_value']}")
                        print()
                    
                    if data.get('anonymized_text'):
                        print(f"   Texte anonymisé:")
                        print(f"   {data['anonymized_text'][:200]}...")
                else:
                    print("     Aucune donnée sensible détectée")
            else:
                print(f" Erreur: {response.status_code}")
                print(f"   {response.text}")
                
        except Exception as e:
            print(f" Erreur: {e}")

def test_with_custom_threshold():
    """Test avec différents seuils de confiance"""
    print("\n" + "="*60)
    print("TEST: Seuils de confiance")
    print("="*60)
    
    text = "Ahmed Bennani, CIN: AB123456, Email: ahmed@gmail.com"
    thresholds = [0.3, 0.5, 0.7, 0.9]
    
    for threshold in thresholds:
        try:
            response = requests.post(
                f"{API_URL}/analyze",
                json={
                    "text": text,
                    "confidence_threshold": threshold
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n   Seuil {threshold}: {data['detections_count']} détections")
        except Exception as e:
            print(f" Erreur: {e}")

def main():
    """Exécute tous les tests"""
    print("\n" + "="*60)
    print("TESTS DU MOTEUR DE DÉTECTION PII/SPI")
    print("="*60)
    print("\n Assurez-vous que le serveur est démarré!")
    print("   python classifier.py")
    print("\n Conseil: Ouvrez un NOUVEAU terminal pour lancer les tests\n")
    
    # Test 1: Health check
    if not test_health():
        print("\n Le service n'est pas disponible. Arrêt des tests.")
        return
    
    # Test 2: Catégories
    test_categories()
    
    # Test 3: Analyses
    test_analyze()
    
    # Test 4: Seuils
    test_with_custom_threshold()
    
    print("\n" + "="*60)
    print("TESTS TERMINÉS")
    print("="*60)

if __name__ == "__main__":
    main()