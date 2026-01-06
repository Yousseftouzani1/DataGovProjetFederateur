"""
Sensitivity Calculator - Cahier des Charges Section 4.4
Implements the full sensitivity scoring formula

Formula: S_total = α·L_legal + β·R_risk + γ·I_impact
Where: α=0.4, β=0.3, γ=0.3
"""

class SensitivityCalculator:
    """
    Calculate sensitivity scores using Cahier formula (Section 4.4)
    Maps to 4 levels: CRITICAL, HIGH, MEDIUM, LOW
    """
    
    # Legal obligation scores [0,1] - RGPD + Loi 09-08 Maroc
    LEGAL_SCORES = {
        # Identity - Critical under RGPD Art.6 + Loi 09-08
        "CIN_MAROC": 1.0,
        "CNSS": 1.0,
        "PASSPORT_MA": 1.0,
        "CARTE_SEJOUR": 1.0,
        "NUMERO_SECURITE_SOCIALE": 1.0,
        
        # Health - RGPD Art.9 (sensitive data)
        "CARTE_RAMED": 1.0,
        "NUMERO_AMO": 1.0,
        "NUMERO_DOSSIER_MEDICAL": 1.0,
        "CARTE_HANDICAP": 1.0,
        "NUMERO_PATIENT": 1.0,
        "NUMERO_MUTUELLE": 0.9,
        
        # Financial - High legal protection
        "IBAN_MA": 0.9,
        "RIB_MAROC": 0.9,
        "CARTE_BANCAIRE": 1.0,
        "CVV": 1.0,
        "NUMERO_COMPTE_BANCAIRE": 0.9,
        "SALAIRE": 0.8,
        "SWIFT_CODE": 0.7,
        "MONTANT_TRANSACTION": 0.4,
        
        # Contact - Medium legal protection
        "PHONE_MA": 0.6,
        "PHONE_FIXE_MA": 0.5,
        "EMAIL": 0.6,
        "EMAIL_PROFESSIONNEL": 0.5,
        "ADRESSE_COMPLETE": 0.7,
        "CODE_POSTAL_MA": 0.3,
        "FAX_MA": 0.4,
        "URL_PERSONNEL": 0.3,
        "ADRESSE_IP": 0.5,
        
        # Education - Medium protection
        "MASSAR": 0.7,
        "CNE": 0.7,
        "DIPLOME_NUMERO": 0.5,
        "NOTE_EXAMEN": 0.6,
        "NUMERO_ETUDIANT": 0.6,
        
        # Professional - Variable
        "MATRICULE_EMPLOYEE": 0.5,
        "CONTRAT_TRAVAIL_ID": 0.6,
        "NUMERO_BADGE": 0.3,
        "ICE": 0.5,
        "NUMERO_RC": 0.4,
        "PATENTE": 0.4,
        
        # Biometric - CRITICAL under RGPD Art.9
        "PHOTO_HASH": 1.0,
        "EMPREINTE_DIGITALE_ID": 1.0,
        "NUMERO_DNA": 1.0,
        
        # Other
        "DATE_NAISSANCE": 0.7,
        "IMMATRICULATION_VEHICULE": 0.4,
        "PERMIS_CONDUIRE": 0.6,
        "CARTE_ELECTORALE": 0.5,
        "NUMERO_FACTURE": 0.2,
    }
    
    # Privacy risk scores [0,1] - Risk of re-identification
    RISK_SCORES = {
        # Very high re-identification risk
        "CIN_MAROC": 0.95,
        "CNSS": 0.95,
        "PASSPORT_MA": 0.9,
        "CARTE_BANCAIRE": 0.95,
        "NUMERO_AMO": 0.9,
        "NUMERO_SECURITE_SOCIALE": 0.95,
        
        # High risk
        "IBAN_MA": 0.8,
        "RIB_MAROC": 0.8,
        "PHONE_MA": 0.7,
        "EMAIL": 0.7,
        "MASSAR": 0.75,
        "CNE": 0.75,
        "CARTE_RAMED": 0.8,
        "NUMERO_DOSSIER_MEDICAL": 0.85,
        
        # Medium risk
        "SALAIRE": 0.6,
        "ADRESSE_COMPLETE": 0.65,
        "PERMIS_CONDUIRE": 0.6,
        "DATE_NAISSANCE": 0.5,
        "NUMERO_MUTUELLE": 0.7,
        "MATRICULE_EMPLOYEE": 0.5,
        
        # Lower risk
        "CODE_POSTAL_MA": 0.3,
        "IMMATRICULATION_VEHICULE": 0.4,
        "NUMERO_FACTURE": 0.2,
        "PHONE_FIXE_MA": 0.4,
        "FAX_MA": 0.3,
        "EMAIL_PROFESSIONNEL": 0.5,
        "NUMERO_BADGE": 0.3,
        
        # Biometric - extremely high risk
        "PHOTO_HASH": 1.0,
        "EMPREINTE_DIGITALE_ID": 1.0,
        "NUMERO_DNA": 1.0,
        
        # Professional - variable
        "ICE": 0.4,
        "NUMERO_RC": 0.4,
        "PATENTE": 0.4,
        "CONTRAT_TRAVAIL_ID": 0.6,
        
        # Education
        "DIPLOME_NUMERO": 0.5,
        "NOTE_EXAMEN": 0.5,
        "NUMERO_ETUDIANT": 0.6,
        
        # Technical
        "ADRESSE_IP": 0.6,
        "URL_PERSONNEL": 0.4,
        
        # Financial
        "CVV": 0.9,
        "SWIFT_CODE": 0.5,
        "NUMERO_COMPTE_BANCAIRE": 0.8,
        "MONTANT_TRANSACTION": 0.3,
        
        # Sensitive
        "CARTE_SEJOUR": 0.8,
        "CARTE_ELECTORALE": 0.6,
        "CARTE_HANDICAP": 0.9,
        "NUMERO_PATIENT": 0.85,
    }
    
    # Impact if leaked scores [0,1] - Potential harm
    IMPACT_SCORES = {
        # Maximum impact - identity theft, fraud
        "CARTE_BANCAIRE": 1.0,
        "CVV": 1.0,
        "CIN_MAROC": 0.9,
        "IBAN_MA": 0.95,
        "RIB_MAROC": 0.95,
        "NUMERO_COMPTE_BANCAIRE": 0.95,
        
        # Very high impact - discrimination, stigma
        "CARTE_HANDICAP": 0.95,
        "NUMERO_DOSSIER_MEDICAL": 0.9,
        "NUMERO_DNA": 1.0,
        "EMPREINTE_DIGITALE_ID": 0.95,
        "PHOTO_HASH": 0.85,
        "CARTE_RAMED": 0.8,
        "NUMERO_AMO": 0.85,
        
        # High impact
        "CNSS": 0.85,
        "SALAIRE": 0.8,
        "PASSPORT_MA": 0.85,
        "NUMERO_SECURITE_SOCIALE": 0.9,
        "CARTE_SEJOUR": 0.8,
        
        # Medium impact
        "PHONE_MA": 0.6,
        "EMAIL": 0.5,
        "ADRESSE_COMPLETE": 0.7,
        "MASSAR": 0.6,
        "CNE": 0.6,
        "PERMIS_CONDUIRE": 0.5,
        "DATE_NAISSANCE": 0.5,
        
        # Lower impact
        "IMMATRICULATION_VEHICULE": 0.4,
        "CODE_POSTAL_MA": 0.3,
        "NUMERO_FACTURE": 0.2,
        "PHONE_FIXE_MA": 0.4,
        "FAX_MA": 0.3,
        
        # Professional
        "MATRICULE_EMPLOYEE": 0.4,
        "CONTRAT_TRAVAIL_ID": 0.6,
        "NUMERO_BADGE": 0.2,
        "ICE": 0.5,
        "NUMERO_RC": 0.4,
        "PATENTE": 0.4,
        "EMAIL_PROFESSIONNEL": 0.4,
        
        # Education
        "DIPLOME_NUMERO": 0.5,
        "NOTE_EXAMEN": 0.6,
        "NUMERO_ETUDIANT": 0.5,
        
        # Technical
        "ADRESSE_IP": 0.5,
        "URL_PERSONNEL": 0.3,
        
        # Health continued
        "NUMERO_MUTUELLE": 0.75,
        "NUMERO_PATIENT": 0.85,
        "CARTE_ELECTORALE": 0.5,
        
        # Financial continued
        "SWIFT_CODE": 0.6,
        "MONTANT_TRANSACTION": 0.4,
    }
    
    def calculate(self, entity_type: str) -> dict:
        """
        Calculate sensitivity using Cahier formula (Section 4.4)
        
        Returns:
            dict: {
                "level": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
                "score": float (0-1),
                "breakdown": {"legal": float, "risk": float, "impact": float}
            }
        """
        # Get component scores (default to 0.5 if unknown)
        L = self.LEGAL_SCORES.get(entity_type, 0.5)
        R = self.RISK_SCORES.get(entity_type, 0.5)
        I = self.IMPACT_SCORES.get(entity_type, 0.5)
        
        # Cahier formula with weights
        # α=0.4 (legal), β=0.3 (risk), γ=0.3 (impact)
        S_total = 0.4 * L + 0.3 * R + 0.3 * I
        
        # Map to discrete levels (Cahier thresholds)
        if S_total >= 0.85:
            level = "critical"
        elif S_total >= 0.6:
            level = "high"
        elif S_total >= 0.3:
            level = "medium"
        else:
            level = "low"
        
        return {
            "level": level,
            "score": round(S_total, 3),
            "breakdown": {
                "legal": round(L, 2),
                "risk": round(R, 2),
                "impact": round(I, 2)
            }
        }
    
    def get_all_sensitivities(self) -> dict:
        """Get calculated sensitivities for all known entities"""
        result = {}
        all_entities = set(self.LEGAL_SCORES.keys()) | set(self.RISK_SCORES.keys()) | set(self.IMPACT_SCORES.keys())
        
        for entity_type in all_entities:
            result[entity_type] = self.calculate(entity_type)
        
        return result
