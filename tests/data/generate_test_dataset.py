"""
Moroccan PII Test Dataset Generator
Generates 500+ realistic test samples for Presidio evaluation
Cahier Section 5.9 - Test Dataset Requirement
"""

import pandas as pd
import random
import json
from datetime import datetime

# Set random seed for reproducibility
random.seed(42)

def generate_moroccan_cin():
    """Generate realistic Moroccan CIN (2 letters + 6 digits)"""
    letters = ''.join(random.choices('ABCDEFGHIJKLMNPQRSTUVWXYZ', k=2))
    numbers = ''.join(random.choices('0123456789', k=6))
    return f"{letters}{numbers}"

def generate_moroccan_phone():
    """Generate Moroccan phone number in various formats"""
    prefix = random.choice(['6', '7', '5'])
    number = random.randint(10000000, 99999999)
    
    formats = [
        f"+212{prefix}{number}",
        f"0{prefix}{number}",
        f"00212{prefix}{number}",
        f"+212 {prefix} {str(number)[:2]} {str(number)[2:4]} {str(number)[4:6]} {str(number)[6:]}",
    ]
    return random.choice(formats)

def generate_moroccan_iban():
    """Generate Moroccan IBAN (MA + 2 digits + 4 letters + 20 alphanumeric)"""
    check_digits = random.randint(10, 99)
    bank_code = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=4))
    account = ''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=20))
    return f"MA{check_digits}{bank_code}{account}"

def generate_cnss():
    """Generate CNSS number (12 digits)"""
    return ''.join(random.choices('0123456789', k=12))

def generate_passport():
    """Generate Moroccan passport (2 letters + 6-7 digits)"""
    letters = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=2))
    numbers = ''.join(random.choices('0123456789', k=random.choice([6, 7])))
    return f"{letters}{numbers}"

def generate_test_dataset(num_samples=500):
    """Generate complete test dataset"""
    
    print("="*70)
    print("MOROCCAN PII TEST DATASET GENERATOR")
    print("="*70)
    print(f"\nGenerating {num_samples} test samples...")
    
    data = []
    
    # ========================================================================
    # CATEGORY 1: Single CIN (100 samples)
    # ========================================================================
    print("\n[1/7] Generating CIN samples (100)...")
    for i in range(100):
        cin = generate_moroccan_cin()
        templates = [
            f"Mon CIN est {cin}",
            f"Carte d'identité numéro: {cin}",
            f"CIN: {cin}",
            f"Numéro CIN {cin}",
            f"Je m'appelle Ahmed, mon CIN est {cin}",
            f"Veuillez enregistrer le CIN {cin}",
            f"Document CIN {cin} valide jusqu'en 2030",
        ]
        text = random.choice(templates)
        data.append({
            "text": text,
            "expected_entities": json.dumps(["CIN_MAROC"]),
            "entity_values": json.dumps([cin]),
            "entity_count": 1,
            "category": "single_cin"
        })
    
    # ========================================================================
    # CATEGORY 2: Single Phone (100 samples)
    # ========================================================================
    print("[2/7] Generating Phone samples (100)...")
    for i in range(100):
        phone = generate_moroccan_phone()
        templates = [
            f"Téléphone: {phone}",
            f"Appelez-moi au {phone}",
            f"Contact: {phone}",
            f"Mon numéro est {phone}",
            f"Pour me joindre: {phone}",
            f"Mobile: {phone}",
            f"Tel portable {phone}",
        ]
        text = random.choice(templates)
        data.append({
            "text": text,
            "expected_entities": json.dumps(["PHONE_MA"]),
            "entity_values": json.dumps([phone]),
            "entity_count": 1,
            "category": "single_phone"
        })
    
    # ========================================================================
    # CATEGORY 3: Single IBAN (75 samples)
    # ========================================================================
    print("[3/7] Generating IBAN samples (75)...")
    for i in range(75):
        iban = generate_moroccan_iban()
        templates = [
            f"IBAN: {iban}",
            f"Mon compte bancaire: {iban}",
            f"RIB IBAN {iban}",
            f"Compte: {iban}",
        ]
        text = random.choice(templates)
        data.append({
            "text": text,
            "expected_entities": json.dumps(["IBAN_MA"]),
            "entity_values": json.dumps([iban]),
            "entity_count": 1,
            "category": "single_iban"
        })
    
    # ========================================================================
    # CATEGORY 4: Single CNSS (75 samples)
    # ========================================================================
    print("[4/7] Generating CNSS samples (75)...")
    for i in range(75):
        cnss = generate_cnss()
        templates = [
            f"Mon numéro CNSS est {cnss}",
            f"CNSS: {cnss}",
            f"Numéro de sécurité sociale: {cnss}",
            f"Affilié CNSS {cnss}",
        ]
        text = random.choice(templates)
        data.append({
            "text": text,
            "expected_entities": json.dumps(["CNSS"]),
            "entity_values": json.dumps([cnss]),
            "entity_count": 1,
            "category": "single_cnss"
        })
    
    # ========================================================================
    # CATEGORY 5: Multiple Entities (100 samples)
    # ========================================================================
    print("[5/7] Generating Multiple Entity samples (100)...")
    for i in range(100):
        entities = []
        values = []
        
        # Random combination of 2-3 entities
        num_entities = random.choice([2, 3])
        
        if num_entities >= 2:
            cin = generate_moroccan_cin()
            phone = generate_moroccan_phone()
            entities.extend(["CIN_MAROC", "PHONE_MA"])
            values.extend([cin, phone])
            text = f"Informations: CIN {cin}, Tel: {phone}"
        
        if num_entities == 3:
            iban = generate_moroccan_iban()
            entities.append("IBAN_MA")
            values.append(iban)
            text += f", IBAN: {iban}"
        
        data.append({
            "text": text,
            "expected_entities": json.dumps(entities),
            "entity_values": json.dumps(values),
            "entity_count": len(entities),
            "category": "multiple_entities"
        })
    
    # ========================================================================
    # CATEGORY 6: Edge Cases (50 samples)
    # ========================================================================
    print("[6/7] Generating Edge Case samples (50)...")
    
    edge_cases = [
        # Partial CIN (should NOT match)
        {"text": "Code AB123", "expected_entities": json.dumps([]), "entity_values": json.dumps([]), "entity_count": 0, "category": "edge_partial_cin"},
        {"text": "Reference XY12345", "expected_entities": json.dumps([]), "entity_values": json.dumps([]), "entity_count": 0, "category": "edge_partial_cin"},
        
        # CIN with spaces (should match after normalization)
        {"text": f"CIN: {generate_moroccan_cin()[:2]} {generate_moroccan_cin()[2:]}", "expected_entities": json.dumps(["CIN_MAROC"]), "entity_values": json.dumps(["varies"]), "entity_count": 1, "category": "edge_cin_spaces"},
        
        # Phone with various spacing
        {"text": "+212 6 12 34 56 78", "expected_entities": json.dumps(["PHONE_MA"]), "entity_values": json.dumps(["+212612345678"]), "entity_count": 1, "category": "edge_phone_spaces"},
        {"text": "0612 345 678", "expected_entities": json.dumps(["PHONE_MA"]), "entity_values": json.dumps(["0612345678"]), "entity_count": 1, "category": "edge_phone_spaces"},
        
        # False positive prevention
        {"text": "The weather is nice today AB123.", "expected_entities": json.dumps([]), "entity_values": json.dumps([]), "entity_count": 0, "category": "edge_false_positive"},
        {"text": "Product code: MA123456", "expected_entities": json.dumps([]), "entity_values": json.dumps([]), "entity_count": 0, "category": "edge_false_positive"},
        {"text": "Random text 0612 without context", "expected_entities": json.dumps([]), "entity_values": json.dumps([]), "entity_count": 0, "category": "edge_false_positive"},
        
        # Numbers without PII context
        {"text": "The price is 123456789012", "expected_entities": json.dumps([]), "entity_values": json.dumps([]), "entity_count": 0, "category": "edge_numeric"},
        {"text": "Code: 987654321", "expected_entities": json.dumps([]), "entity_values": json.dumps([]), "entity_count": 0, "category": "edge_numeric"},
    ]
    
    # Replicate edge cases to reach 50
    for _ in range(5):
        for case in edge_cases:
            data.append(case)
            if len([d for d in data if d['category'].startswith('edge')]) >= 50:
                break
        if len([d for d in data if d['category'].startswith('edge')]) >= 50:
            break
    
    # ========================================================================
    # CATEGORY 7: No PII (50 samples)
    # ========================================================================
    print("[7/7] Generating No-PII samples (50)...")
    
    no_pii_texts = [
        "Bonjour, comment allez-vous?",
        "Le temps est très agréable aujourd'hui.",
        "J'aime beaucoup ce restaurant.",
        "La réunion est prévue pour demain.",
        "Le projet avance bien.",
        "Merci pour votre aide.",
        "C'est une excellente idée.",
        "Le document est prêt.",
        "La formation commence lundi.",
        "Le rapport sera envoyé ce soir.",
    ]
    
    for i in range(50):
        text = random.choice(no_pii_texts)
        data.append({
            "text": text,
            "expected_entities": json.dumps([]),
            "entity_values": json.dumps([]),
            "entity_count": 0,
            "category": "no_pii"
        })
    
    # ========================================================================
    # CREATE DATAFRAME AND SAVE
    # ========================================================================
    df = pd.DataFrame(data)
    
    # Shuffle dataset
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    output_file = "moroccan_pii_test_dataset.csv"
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    # Print statistics
    print("\n" + "="*70)
    print("DATASET GENERATION COMPLETE")
    print("="*70)
    print(f"\n✅ Generated {len(df)} test samples")
    print(f"✅ Saved to: {output_file}")
    print(f"✅ File size: {len(df) * df.memory_usage(deep=True).sum() / 1024:.2f} KB")
    
    print(f"\n📊 Category Breakdown:")
    print(df['category'].value_counts().to_string())
    
    print(f"\n📊 Entity Count Distribution:")
    print(df['entity_count'].value_counts().sort_index().to_string())
    
    print(f"\n✅ Dataset ready for evaluation!")
    
    return df

if __name__ == "__main__":
    generate_test_dataset(500)
