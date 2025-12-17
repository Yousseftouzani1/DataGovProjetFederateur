"""
Apache Ranger – Policy Builders
================================

Ce fichier contient UNIQUEMENT des fonctions de construction de policies Ranger.
Il ne contient :
- aucune logique métier applicative
- aucun appel réseau
- aucune dépendance à FastAPI


Transformer les règles de gouvernance (PII, SPI, CRITICAL)
en policies Apache Ranger conformes à l’API REST officielle.

Conforme au cahier de charges – Section 12.4
"""

# ====================================================================
# 1 ACCESS POLICY (ALLOW / DENY)
# ====================================================================

def build_access_policy(
    policy_name: str,
    database: str,
    table: str,
    users: list,
    allow: bool
) -> dict:
    """
    Crée une policy Ranger de type ACCESS (Allow / Deny)

    Cas d’usage (CDC) :
    - SPI critique → accès restreint
    - CRITICAL → accès refusé aux rôles non autorisés

    Paramètres :
    - policy_name : nom unique de la policy
    - database    : base de données cible
    - table       : table concernée
    - users       : liste des utilisateurs / rôles Ranger
    - allow       : True = autoriser / False = refuser

    Retour :
    - JSON prêt à être envoyé à l’API Ranger
    """

    return {
        # Type 0 = Access Policy (Ranger standard)
        "policyType": 0,

        # Nom lisible et explicite (important pour l’audit)
        "name": policy_name,

        # Activation immédiate
        "isEnabled": True,

        # Ressources protégées
        "resources": {
            "database": {
                "values": [database],
                "isExcludes": False,
                "isRecursive": False
            },
            "table": {
                "values": [table],
                "isExcludes": False,
                "isRecursive": False
            }
        },

        # Règles d’accès
        "policyItems": [
            {
                # Type d’accès (lecture uniquement ici)
                "accesses": [
                    {
                        "type": "select",
                        "isAllowed": allow
                    }
                ],

                # Utilisateurs ou rôles concernés
                "users": users,

                # Aucune condition supplémentaire
                "conditions": [],

                # Délégation interdite
                "delegateAdmin": False
            }
        ]
    }

# ====================================================================
# 2 DATA MASKING POLICY (PII / SPI)
# ====================================================================

def build_masking_policy(
    policy_name: str,
    database: str,
    table: str,
    columns: list,
    users: list,
    mask_type: str
) -> dict:
    """
    Crée une policy Ranger de type DATA MASKING

    Cas d’usage (CDC) :
    - PII → MASK
    - SPI → HASH
    - Données très sensibles → NULLIFY (optionnel)

    Paramètres :
    - policy_name : nom unique de la policy
    - database    : base de données
    - table       : table concernée
    - columns     : colonnes à masquer
    - users       : rôles / utilisateurs
    - mask_type   : MASK | HASH | NULLIFY

    Retour :
    - JSON compatible Ranger API
    """

    return {
        # Type 1 = Masking Policy
        "policyType": 1,

        "name": policy_name,
        "isEnabled": True,

        # Ressources ciblées (jusqu’au niveau colonne)
        "resources": {
            "database": {
                "values": [database],
                "isExcludes": False,
                "isRecursive": False
            },
            "table": {
                "values": [table],
                "isExcludes": False,
                "isRecursive": False
            },
            "column": {
                "values": columns,
                "isExcludes": False,
                "isRecursive": False
            }
        },

        # Règles de masquage
        "policyItems": [
            {
                # Autorisation de lecture (mais masquée)
                "accesses": [
                    {
                        "type": "select",
                        "isAllowed": True
                    }
                ],

                # Utilisateurs concernés
                "users": users,

                # Configuration du masquage
                "dataMaskInfo": {
                    # MASK | HASH | NULLIFY
                    "dataMaskType": mask_type,

                    # Pas de condition dynamique ici
                    "conditionExpr": "",

                    # Pas d’expression custom
                    "valueExpr": ""
                },

                "delegateAdmin": False
            }
        ]
    }

# ====================================================================
# 3 ROW-LEVEL FILTER POLICY (filtrage par ligne)
# ====================================================================

def build_row_filter_policy(
    policy_name: str,
    database: str,
    table: str,
    users: list,
    filter_expression: str
) -> dict:
    """
    Crée une policy Ranger de type ROW FILTER

    Cas d’usage (CDC) :
    - Filtrer dynamiquement les lignes sensibles
    - Exemple :
      role != 'admin' → WHERE is_sensitive = false

    Paramètres :
    - policy_name      : nom unique
    - database         : base de données
    - table            : table cible
    - users            : rôles concernés
    - filter_expression: clause SQL WHERE (sans le WHERE)

    Retour :
    - JSON Ranger API
    """

    return {
        # Type 2 = Row Filter Policy
        "policyType": 2,

        "name": policy_name,
        "isEnabled": True,

        "resources": {
            "database": {
                "values": [database],
                "isExcludes": False,
                "isRecursive": False
            },
            "table": {
                "values": [table],
                "isExcludes": False,
                "isRecursive": False
            }
        },

        "policyItems": [
            {
                "users": users,

                # Expression SQL appliquée dynamiquement
                "rowFilterInfo": {
                    "filterExpr": filter_expression
                },

                "delegateAdmin": False
            }
        ]
    }

# ====================================================================
# 4 UTILITAIRE – Validation simple des types
# ====================================================================

def validate_mask_type(mask_type: str):
    """
    Vérifie que le type de masquage est supporté par Ranger.
    Sécurité supplémentaire avant envoi API.
    """

    allowed = {"MASK", "HASH", "NULLIFY"}

    if mask_type not in allowed:
        raise ValueError(
            f"Invalid mask_type '{mask_type}'. "
            f"Allowed values: {allowed}"
        )
