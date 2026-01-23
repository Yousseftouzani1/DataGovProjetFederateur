
# MOROCCAN PATTERNS (CORE OF TÂCHE 2)
MOROCCAN_PATTERNS = {
    "CIN_MAROC": {
        "patterns": [r"\b[A-Z]{1,2}\d{5,8}\b"],
        "category": "IDENTITE_PERSONNELLE",
        "sensitivity": "critical",
        "domain": "IDENTITE"
    },
    "CNSS": {
        "patterns": [r"\b\d{9,12}\b"],
        "category": "PROFESSIONAL_INFO",
        "sensitivity": "critical",
        "domain": "PROFESSIONNEL",
        "context_required": ["cnss", "sécurité sociale", "الضمان"]
    },
    "PHONE_MA": {
        "patterns": [
            r"(?:\+212|00212|0)[5-7]\d{8}",
            r"\+212[\s.-]?[5-7][\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}"
        ],
        "category": "COORDONNEES",
        "sensitivity": "high",
        "domain": "CONTACT"
    },
    "IBAN_MA": {
        "patterns": [r"\bMA\d{2}[A-Z0-9\s]{20,26}\b"],
        "category": "DONNEES_FINANCIERES",
        "sensitivity": "critical",
        "domain": "FINANCIER"
    },
    "EMAIL": {
        "patterns": [r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"],
        "category": "COORDONNEES",
        "sensitivity": "high",
        "domain": "CONTACT"
    },
    "MASSAR": {
        "patterns": [r"\b[A-Z]\d{9}\b"],
        "category": "IDENTITE_PERSONNELLE",
        "sensitivity": "high",
        "domain": "EDUCATION",
        "context_required": ["massar", "élève", "scolaire"]
    },
    "PASSPORT_MA": {
        "patterns": [r"\b[A-Z]{1,2}\d{6,9}\b"],
        "category": "IDENTITE_PERSONNELLE",
        "sensitivity": "critical",
        "domain": "IDENTITE",
        "context_required": ["passeport", "passport", "جواز"]
    },
    "DATE_NAISSANCE": {
        "patterns": [
            r"(?:0[1-9]|[12][0-9]|3[01])[-/](?:0[1-9]|1[0-2])[-/](?:19|20)\d{2}",
            r"(?:19|20)\d{2}[-/](?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12][0-9]|3[01])"
        ],
        "category": "IDENTITE_PERSONNELLE",
        "sensitivity": "high",
        "domain": "IDENTITE"
    },
    "IMMATRICULATION_VEHICULE": {
        "patterns": [r"\d{1,6}[\s-]?[A-Zأ-ي][\s-]?\d{1,4}"],
        "category": "DONNEES_VEHICULE",
        "sensitivity": "medium",
        "domain": "VEHICULE"
    },
    "CARTE_SEJOUR": {
        "patterns": [r"\b[A-Z]{2}\d{6,10}\b"],
        "category": "IDENTITE_PERSONNELLE",
        "sensitivity": "critical",
        "domain": "IMMIGRATION",
        "context_required": ["séjour", "residence", "إقامة"]
    },
    
    # === IDENTITY & HEALTH (10 more) ===
    "CARTE_RAMED": {
        "patterns": [r"\bRAMED\d{10}\b"],
        "category": "IDENTITE_PERSONNELLE",
        "sensitivity": "high",
        "domain": "SANTE",
        "context_required": ["ramed", "santé", "الصحة"]
    },
    "NUMERO_AMO": {
        "patterns": [r"\b\d{13}\b"],
        "category": "IDENTITE_PERSONNELLE",
        "sensitivity": "critical",
        "domain": "SANTE",
        "context_required": ["amo", "assurance", "التأمين"]
    },
    "PERMIS_CONDUIRE": {
        "patterns": [r"\b[A-Z]\d{7}\b"],
        "category": "IDENTITE_PERSONNELLE",
        "sensitivity": "medium",
        "domain": "IDENTITE",
        "context_required": ["permis", "conduire", "رخصة"]
    },
    "NUMERO_DOSSIER_MEDICAL": {
        "patterns": [r"\bDM\d{8}\b"],
        "category": "DONNEES_SANTE",
        "sensitivity": "critical",
        "domain": "SANTE"
    },
    "CARTE_ELECTORALE": {
        "patterns": [r"\bCE[A-Z]\d{7}\b"],
        "category": "IDENTITE_PERSONNELLE",
        "sensitivity": "medium",
        "domain": "POLITIQUE"
    },
    "NUMERO_MUTUELLE": {
        "patterns": [r"\bMUT\d{8,12}\b"],
        "category": "DONNEES_SANTE",
        "sensitivity": "high",
        "domain": "SANTE"
    },
    "CARTE_HANDICAP": {
        "patterns": [r"\bCH\d{8}\b"],
        "category": "DONNEES_SANTE",
        "sensitivity": "critical",
        "domain": "SANTE",
        "context_required": ["handicap", "invalidité"]
    },
    "NUMERO_PATIENT": {
        "patterns": [r"\bPAT\d{8,10}\b"],
        "category": "DONNEES_SANTE",
        "sensitivity": "critical",
        "domain": "SANTE"
    },
    "CNE": {
        "patterns": [r"\b[A-Z]\d{9}\b"],
        "category": "IDENTITE_PERSONNELLE",
        "sensitivity": "high",
        "domain": "EDUCATION",
        "context_required": ["cne", "étudiant", "طالب", "élève"]
    },
    "NUMERO_SECURITE_SOCIALE": {
        "patterns": [r"\b[12]\d{14}\b"],
        "category": "PROFESSIONAL_INFO",
        "sensitivity": "critical",
        "domain": "PROFESSIONNEL"
    },
    
    # === FINANCIAL (8 more) ===
    "RIB_MAROC": {
        "patterns": [r"\b\d{24}\b"],
        "category": "DONNEES_FINANCIERES",
        "sensitivity": "critical",
        "domain": "FINANCIER",
        "context_required": ["rib", "relevé", "bancaire"]
    },
    "SWIFT_CODE": {
        "patterns": [r"\b[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?\b"],
        "category": "DONNEES_FINANCIERES",
        "sensitivity": "high",
        "domain": "FINANCIER"
    },
    "CARTE_BANCAIRE": {
        "patterns": [r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"],
        "category": "DONNEES_FINANCIERES",
        "sensitivity": "critical",
        "domain": "FINANCIER"
    },
    "CVV": {
        "patterns": [r"\b\d{3,4}\b"],
        "category": "DONNEES_FINANCIERES",
        "sensitivity": "critical",
        "domain": "FINANCIER",
        "context_required": ["cvv", "code", "sécurité"]
    },
    "NUMERO_FACTURE": {
        "patterns": [r"\bFAC\d{8}\b"],
        "category": "DONNEES_FINANCIERES",
        "sensitivity": "low",
        "domain": "COMMERCIAL"
    },
    "SALAIRE": {
        "patterns": [r"\d+\s?(?:DH|MAD|dirhams?)"],
        "category": "DONNEES_FINANCIERES",
        "sensitivity": "critical",
        "domain": "PROFESSIONNEL",
        "context_required": ["salaire", "rémunération", "الأجر", "paie"]
    },
    "NUMERO_COMPTE_BANCAIRE": {
        "patterns": [r"\b\d{10,16}\b"],
        "category": "DONNEES_FINANCIERES",
        "sensitivity": "critical",
        "domain": "FINANCIER",
        "context_required": ["compte", "bancaire", "account"]
    },
    "MONTANT_TRANSACTION": {
        "patterns": [r"\b\d{1,}[.,]\d{2}\s?(?:DH|MAD)\b"],
        "category": "DONNEES_FINANCIERES",
        "sensitivity": "medium",
        "domain": "FINANCIER"
    },
    
    # === CONTACT & ADDRESS (7 more) ===
    "PHONE_FIXE_MA": {
        "patterns": [r"\b05\d{8}\b"],
        "category": "COORDONNEES",
        "sensitivity": "medium",
        "domain": "CONTACT"
    },
    "FAX_MA": {
        "patterns": [r"\b(?:fax|télécopie)[:\s]*05\d{8}\b"],
        "category": "COORDONNEES",
        "sensitivity": "low",
        "domain": "CONTACT"
    },
    "ADRESSE_COMPLETE": {
        "patterns": [r"\b\d+,?\s+(?:rue|avenue|boulevard|av\.)\s+[\w\s]+,\s*\d{5}"],
        "category": "COORDONNEES",
        "sensitivity": "high",
        "domain": "CONTACT"
    },
    "CODE_POSTAL_MA": {
        "patterns": [r"\b\d{5}\b"],
        "category": "COORDONNEES",
        "sensitivity": "low",
        "domain": "CONTACT",
        "context_required": ["code postal", "cp", "ville"]
    },
    "ADRESSE_IP": {
        "patterns": [r"\b(?:\d{1,3}\.){3}\d{1,3}\b"],
        "category": "DONNEES_TECHNIQUES",
        "sensitivity": "medium",
        "domain": "INFORMATIQUE"
    },
    "URL_PERSONNEL": {
        "patterns": [r"https?://[\w\.-]+\.[a-z]{2,}"],
        "category": "COORDONNEES",
        "sensitivity": "low",
        "domain": "CONTACT"
    },
    "EMAIL_PROFESSIONNEL": {
        "patterns": [r"[a-zA-Z0-9._%+-]+@(?:entreprise|company|corp|inc|org)\.(?:ma|com)"],
        "category": "COORDONNEES",
        "sensitivity": "medium",
        "domain": "PROFESSIONNEL"
    },
    
    # === PROFESSIONAL (6 more) ===
    "MATRICULE_EMPLOYEE": {
        "patterns": [r"\bEMP[A-Z]{2}\d{6}\b"],
        "category": "PROFESSIONAL_INFO",
        "sensitivity": "medium",
        "domain": "PROFESSIONNEL"
    },
    "CONTRAT_TRAVAIL_ID": {
        "patterns": [r"\bCT\d{8}\b"],
        "category": "PROFESSIONAL_INFO",
        "sensitivity": "high",
        "domain": "PROFESSIONNEL"
    },
    "NUMERO_BADGE": {
        "patterns": [r"\bBDG\d{6}\b"],
        "category": "PROFESSIONAL_INFO",
        "sensitivity": "low",
        "domain": "PROFESSIONNEL"
    },
    "ICE": {
        "patterns": [r"\b\d{15}\b"],
        "category": "PROFESSIONAL_INFO",
        "sensitivity": "medium",
        "domain": "PROFESSIONNEL",
        "context_required": ["ice", "entreprise", "société"]
    },
    "NUMERO_RC": {
        "patterns": [r"\bRC\d{6,8}\b"],
        "category": "PROFESSIONAL_INFO",
        "sensitivity": "medium",
        "domain": "PROFESSIONNEL",
        "context_required": ["rc", "registre", "commerce"]
    },
    "PATENTE": {
        "patterns": [r"\bPAT\d{8}\b"],
        "category": "PROFESSIONAL_INFO",
        "sensitivity": "medium",
        "domain": "PROFESSIONNEL",
        "context_required": ["patente", "taxe"]
    },
    
    # === EDUCATION (3 more) ===
    "DIPLOME_NUMERO": {
        "patterns": [r"\bDIP\d{8}\b"],
        "category": "DONNEES_EDUCATION",
        "sensitivity": "medium",
        "domain": "EDUCATION"
    },
    "NOTE_EXAMEN": {
        "patterns": [r"\b\d{1,2}[.,]\d{2}\s*/\s*20\b"],
        "category": "DONNEES_EDUCATION",
        "sensitivity": "medium",
        "domain": "EDUCATION"
    },
    "NUMERO_ETUDIANT": {
        "patterns": [r"\bETU\d{8}\b"],
        "category": "DONNEES_EDUCATION",
        "sensitivity": "medium",
        "domain": "EDUCATION"
    },
    
    # === BIOMETRIC & SENSITIVE (3 more) ===
    "PHOTO_HASH": {
        "patterns": [r"\bPH[A-F0-9]{64}\b"],
        "category": "DONNEES_BIOMETRIQUES",
        "sensitivity": "critical",
        "domain": "BIOMETRIQUE"
    },
    "EMPREINTE_DIGITALE_ID": {
        "patterns": [r"\bFP[A-F0-9]{32}\b"],
        "category": "DONNEES_BIOMETRIQUES",
        "sensitivity": "critical",
        "domain": "BIOMETRIQUE"
    },
    "NUMERO_DNA": {
        "patterns": [r"\bDNA[A-F0-9]{16}\b"],
        "category": "DONNEES_BIOMETRIQUES",
        "sensitivity": "critical",
        "domain": "BIOMETRIQUE"
    }
}

# Arabic patterns
ARABIC_PATTERNS = {
    "الرقم_الوطني": {
        "patterns": [
            r"رقم البطاقة(?:.*?)[:\s]*[A-Za-z]{1,2}\d{5,8}",  # Context aware
            r"\b[A-Za-z]{1,2}\d{5,8}\b"  # Direct match attempt for Arabic context
        ],
        "category": "IDENTITE_PERSONNELLE",
        "sensitivity": "critical",
        "domain": "IDENTITE"
    },
    "رقم_الهاتف": {
        "patterns": [r"الهاتف[:\s]*(?:\+212|00212|0)[5-7]\d{8}"],
        "category": "COORDONNEES",
        "sensitivity": "high",
        "domain": "CONTACT"
    },
    "الحساب_البنكي": {
        "patterns": [r"(?:IBAN|الحساب البنكي)[:\s]*MA\d{2}[A-Z0-9\s]{20,26}"],
        "category": "DONNEES_FINANCIERES",
        "sensitivity": "critical",
        "domain": "FINANCIER"
    }
}
