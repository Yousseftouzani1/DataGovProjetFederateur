# Guide d'Utilisation Complet - Plateforme DataGov

## Projet Federateur ENSIAS - Data Governance Platform

**Version** : Production v2.0
**Date** : Fevrier 2026
**Equipe** : Nisrine IBNOU-KADY, Younes Bazzaoui, Youssef Elgarch, Youssef Touzani
**Encadrants** : Prof. Karim Baina, Mme. Manal Gasmi

---

## Table des Matieres

1. [Presentation Generale](#1-presentation-generale)
2. [Acces a la Plateforme](#2-acces-a-la-plateforme)
3. [Authentification et Inscription](#3-authentification-et-inscription)
4. [Architecture des Roles](#4-architecture-des-roles)
5. [Guide Role : Administrateur (Admin)](#5-guide-role--administrateur-admin)
6. [Guide Role : Data Steward](#6-guide-role--data-steward)
7. [Guide Role : Annotateur (Annotator)](#7-guide-role--annotateur-annotator)
8. [Guide Role : Labeler](#8-guide-role--labeler)
9. [Matrice d'Acces Detaillee](#9-matrice-dacces-detaillee)
10. [Workflows Complets](#10-workflows-complets)
11. [Navigation et Interface Commune](#11-navigation-et-interface-commune)
12. [FAQ et Depannage](#12-faq-et-depannage)

---

## 1. Presentation Generale

DataGov est une plateforme de gouvernance des donnees concue pour les entreprises marocaines. Elle permet :

- La detection automatique des donnees personnelles sensibles (PII/SPI) : CIN, Telephone, IBAN, Email, CNSS, Passeport
- L'evaluation de la qualite des donnees selon la norme ISO 25012
- Le nettoyage et la correction automatique des donnees via des modeles ML (T5, BERT, Random Forest)
- Le masquage ethique des donnees sensibles (EthiMask)
- La classification de sensibilite par ensemble de modeles
- L'annotation humaine collaborative (Human-in-the-Loop)
- L'integration avec Apache Atlas (catalogage) et Apache Ranger (controle d'acces)

La plateforme est organisee en 9 microservices independants, chacun accessible via une passerelle Nginx sur le port 8000.

### URLs d'Acces

| Interface | URL |
|-----------|-----|
| Frontend React (Interface Principale) | `http://localhost:3000` |
| Passerelle API (Nginx) | `http://localhost:8000` |
| Documentation API Auth | `http://localhost:8000/api/auth/docs` |
| Documentation API Cleaning | `http://localhost:8000/api/cleaning/docs` |
| Documentation API Quality | `http://localhost:8000/api/quality/docs` |
| Documentation API Presidio | `http://localhost:8000/api/presidio/docs` |
| Documentation API Taxonomie | `http://localhost:8000/api/taxonomie/docs` |
| Documentation API EthiMask | `http://localhost:8000/api/ethimask/docs` |
| Documentation API Correction | `http://localhost:8000/api/correction/docs` |
| Documentation API Classification | `http://localhost:8000/api/classification/docs` |
| Documentation API Annotation | `http://localhost:8000/api/annotation/docs` |
| Apache Ambari (HDP) | `http://192.168.110.134:8080` |
| Apache Atlas | `http://192.168.110.134:21000` |
| Apache Ranger | `http://192.168.110.134:6080` |
| Apache Airflow | `http://localhost:8081` |

---

## 2. Acces a la Plateforme

### 2.1 Page d'Accueil (Landing Page)

Quand vous ouvrez `http://localhost:3000` sans etre connecte, vous arrivez sur la page d'accueil publique "DataSentinel".

**Ce que vous voyez :**
- Une barre de navigation en haut avec le logo DataSentinel, le logo ENSIAS, et un bouton "Login"
- Un hero section anime avec un titre typewriter qui alterne entre "Future Data", "Privacy Ops", "Compliance", "Governance"
- Un carousel defilant des technologies utilisees : Apache Atlas, Apache Ranger, Presidio, Apache Airflow, TenSEAL, FastAPI, React, MongoDB, RabbitMQ, Docker
- 3 cartes de fonctionnalites avec images : EthiMask Encryption, PII Sentinel, Federated Governance
- 4 cartes de roles avec images : Admin, Data Steward, Annotator, Labeler
- Section equipe avec les noms des contributeurs et encadrants
- Footer avec copyright

**Actions possibles :**
- Cliquer sur "Login" ou "Launch Console" pour aller a la page de connexion
- Parcourir les informations du projet

---

## 3. Authentification et Inscription

### 3.1 Page de Connexion (Login)

**URL** : `http://localhost:3000/login`

**Ce que vous voyez :**
- Le logo anime DataGov au centre
- Un formulaire avec deux champs :
  - "Access ID" (nom d'utilisateur) avec icone utilisateur
  - "Secure Token" (mot de passe) avec icone cadenas
- Un bouton "Sign In"
- Un lien "Sign up for free" en bas
- Un bouton "Home" en haut a gauche pour retourner a la page d'accueil

**Comment se connecter :**
1. Entrez votre nom d'utilisateur dans le champ "Access ID"
2. Entrez votre mot de passe dans le champ "Secure Token"
3. Cliquez sur "Sign In"
4. Si les identifiants sont corrects, vous etes redirige vers le Dashboard
5. Si les identifiants sont incorrects, un message d'erreur rouge apparait

**Comptes pre-configures pour test :**

| Utilisateur | Mot de passe | Role |
|-------------|-------------|------|
| admin | admin123 | Administrateur |
| steward | steward123 | Data Steward |
| annotator | annotator123 | Annotateur |
| labeler | labeler123 | Labeler |

*(Note : ces comptes doivent etre crees au prealable via l'API ou l'interface d'inscription)*

### 3.2 Page d'Inscription (Signup)

**URL** : `http://localhost:3000/signup`

**Ce que vous voyez :**
- Un formulaire complet avec les champs :
  - Prenom (First Name)
  - Nom (Last Name)
  - Email (format : name@organization.com)
  - Nom d'utilisateur (Username)
  - Mot de passe (avec bouton oeil pour afficher/masquer)
  - Selection du role : 4 boutons visuels
    - "Steward" (Data Steward - Quality Expert)
    - "Annotator" (Data Validator)
    - "Labeler" (Tag Specialist)
    - "Analyst" (Policy Viewer)
- Un bouton "Create Account"
- Un lien "Sign In" pour les utilisateurs existants

**Comment s'inscrire :**
1. Remplissez tous les champs du formulaire
2. Selectionnez votre role en cliquant sur l'un des 4 boutons de role
3. Cliquez sur "Create Account"
4. Un message de succes vert apparait : "Account created successfully!"
5. Apres 2 secondes, vous etes redirige vers la page de connexion
6. **Important** : Le compte cree est en statut "pending" - l'administrateur doit l'approuver avant que l'utilisateur puisse se connecter

---

## 4. Architecture des Roles

La plateforme definit 4 roles hierarchiques, chacun avec un theme de couleur unique et des permissions specifiques :

| Role | Theme Couleur | Description | Niveau d'Acces |
|------|--------------|-------------|----------------|
| **Admin** | Rouge/Orange | Infrastructure, IAM, configuration globale | Complet |
| **Data Steward** | Vert/Emeraude | Qualite, conformite, catalogage metadata | Eleve |
| **Annotator** | Violet/Rose | Ingestion, profilage, correction assistee par IA | Moyen |
| **Labeler** | Cyan/Turquoise | Etiquetage manuel a volume eleve | Restreint |

### Theme Visuel par Role

Quand un utilisateur se connecte, l'interface entiere change de couleur selon son role :
- **Admin** : Accents rouges, gradient rouge-orange
- **Steward** : Accents vert emeraude, gradient vert
- **Annotator** : Accents violet, gradient violet-rose
- **Labeler** : Accents cyan, gradient cyan-turquoise

Le logo dans la barre laterale et le favicon du navigateur changent egalement selon le role.

---

## 5. Guide Role : Administrateur (Admin)

### 5.1 Dashboard Administrateur

**Acces** : Automatique apres connexion

**Ce que vous voyez :**

#### Section Hero de Bienvenue
- Votre avatar et nom d'utilisateur
- Badge "Administrator" en rouge-orange
- Description : "Primary Focus: Infrastructure, Identity Access Management (IAM), and math foundations"
- 3 boutons d'action rapide :
  - "User Management" --> redirige vers /users
  - "System Settings" --> redirige vers /settings
  - "Operational Status" --> reste sur le dashboard

#### Section Informations Projet
- Description de DataGov et ses fonctionnalites cles (PII Detection, ISO 25012, RBAC, Secure Data Pipeline)

#### Panneau "System Benchmarks" (exclusif Admin)
- Graphique a barres animees montrant le debit du systeme
- Indicateur "LIVE: 124 req/s"
- Stabilite du debit : 99.98%

#### Panneau "Global PII Distribution"
- Tags des types PII detectes : CIN, PHONE, IBAN, EMAIL
- Nombre de noeuds collaboratifs actifs

#### Statistiques Globales (4 cartes)
- **Total Records** : Nombre total d'enregistrements dans le systeme
- **Total Datasets** : Nombre de jeux de donnees uploades
- **Quality Score** : Score moyen de qualite ISO 25012
- **System Nodes** : Nombre de services actifs (ex: 7/9 Nodes Active)

#### Section "Governance Operations" (Admin + Steward)
- Bouton "Sync Taxonomy to Atlas" : Synchronise les definitions de taxonomie PII/SPI avec Apache Atlas
- Bouton "View Audit Logs" --> redirige vers /audit
- Bouton "Data Discovery" --> redirige vers /discovery

#### Cluster de Noeuds (Node Cluster)
- Grille de 9 services avec leur statut en temps reel :
  - Auth Service, Cleaning Engine, Quality Hub, Presidio ML, Taxonomy, EthiMask, Correction ML, Classification, Annotation
  - Chaque service affiche : nom, latence, statut (Healthy en vert / Offline en rouge)
  - Cliquer sur un service ouvre un modal avec : nom, port, description, lien vers la documentation API
- Bouton rafraichir pour recharger les statuts

#### Hierarchie des Roles
- Liste des 4 roles avec leurs descriptions
- Le role actuel est mis en evidence avec un badge "YOU"

### 5.2 Gestion des Utilisateurs (User Control)

**Acces** : Menu lateral --> "User Control" ou `/users`
**Restriction** : Admin uniquement

**Ce que vous voyez :**

#### En-tete
- Titre "User Control"
- Description "Manage identity, access, and role assignments for the ecosystem"
- Statistiques en haut a droite :
  - Total : nombre total d'utilisateurs
  - Active : nombre d'utilisateurs actifs (vert)
  - Pending : nombre d'utilisateurs en attente (orange)

#### Barre d'Outils
- Champ de recherche "Search identities by name or role..."
- Bouton "Filters"
- Bouton "Provision User"

#### Tableau des Utilisateurs
Colonnes :
- **Identity** : Avatar avec initiale + nom d'utilisateur + email genere
- **Authorization Role** : Badge colore (admin=violet, steward=bleu, autre=gris)
- **Onboarding Status** : Indicateur anime
  - "active" : Point vert
  - "pending" : Point orange avec animation pulse
  - "rejected" : Point rouge
- **Administrative Actions** (apparaissent au survol de la ligne) :
  - Pour les utilisateurs "pending" :
    - Bouton vert (coche) : Approuver l'utilisateur --> statut passe a "active"
    - Bouton rouge (X) : Rejeter l'utilisateur --> statut passe a "rejected"
  - Bouton trois points : Menu supplementaire

**Workflow d'approbation :**
1. Un nouvel utilisateur s'inscrit via /signup --> statut "pending"
2. L'admin voit le nouvel utilisateur dans le tableau avec statut orange "pending"
3. L'admin survole la ligne pour voir les boutons d'action
4. Cliquer sur la coche verte approuve l'utilisateur
5. Cliquer sur le X rouge rejette l'utilisateur
6. La table se rafraichit automatiquement

### 5.3 Journaux d'Audit (Audit Logs)

**Acces** : Menu lateral --> "Audit Logs" ou `/audit`
**Restriction** : Admin et Steward

**Ce que vous voyez :**

#### En-tete
- Titre "System Ledger"
- Description "Forensic audit trail for all cluster interactions and data mutations"
- Boutons d'action :
  - "Retrain Pattern" : Relance l'entrainement du modele EthiMask base sur les logs d'audit
  - "Refresh" : Rafraichit les donnees
  - "Export forensic PDF" : Exporte les logs en document PDF formate

#### Onglets
- **General Ledger** : Logs generaux de toutes les operations du systeme
- **Masking Forensics** : Logs specifiques aux operations de masquage EthiMask

#### Filtres (pour l'onglet Masking Forensics)
- Filtre par role : All Roles, Admin, Steward, Annotator, Labeler
- Filtre par type d'entite : All Entities, CIN, PHONE, EMAIL, IBAN
- Filtre par date : Date de debut + Date de fin
- Champ de recherche par mot-cle, utilisateur ou IP

#### Tableau des Logs
Colonnes :
- **Time Vector** : Horodatage de l'evenement
- **Node ID** : Service source (ex: AUTH:NODE_01, ETHIMASK:NODE_01)
- **Action Payload** : Code de l'action executee (ex: MASK_CIN, USER_LOGIN)
- **Initiator** : Avatar + nom de l'utilisateur qui a declenche l'action
- **Severity** : Badge de severite
  - INFO (bleu) : Operation normale
  - WARNING (orange) : Avertissement
  - CRITICAL (rouge avec icone triangle) : Evenement critique

**Cliquer sur une ligne** ouvre un modal "Forensic Detail Record" avec :
- Service Entity (nom du service)
- Initiator (nom de l'utilisateur)
- Details techniques au format JSON
- Bouton "Close Case File"

**Export PDF :**
1. Cliquez sur "Export forensic PDF"
2. Un fichier PDF est genere avec :
   - En-tete bleu fonce "System Forensic Ledger"
   - Date de generation et nombre de records
   - Tableau avec toutes les colonnes
3. Le fichier se telecharge automatiquement

### 5.4 Parametres Systeme (Settings)

**Acces** : Menu lateral --> "Settings" ou `/settings`
**Restriction** : Admin uniquement

**Ce que vous voyez :**

#### Grille de Configuration (8 cartes disponibles pour Admin)

1. **Governance Policy** (Admin + Steward)
   - Cliquer ouvre le modal EthiMask Config
   - 6 curseurs de configuration du perceptron :
     - Sensitivity Weight (ws) : Plus la valeur est elevee, plus le masquage est agressif
     - Role Trust Weight (wr) : Valeur negative = acces restreint pour les roles bas
     - Context Weight (wc) : Poids donne a l'environnement (API vs Analyse)
     - Purpose Weight (wp) : Poids donne a l'intention d'acces
     - Decision Bias (b) : Seuil de base pour toutes les decisions
     - Alpha Balance : Balance entre Privacy et Utility dans la fonction de perte
   - Equation affichee : Score T' = sigma(somme w_i * x_i + b)
   - Indicateur de somme des poids (doit etre = 1.0)
   - Bouton "Normalize" pour normaliser automatiquement les poids
   - Bouton "Commit Weight Configuration" pour sauvegarder
   - Section Homomorphic Encryption (HE) :
     - Statut du contexte TenSEAL (actif/inactif)
     - Bouton "Initialize Context" pour initialiser le chiffrement homomorphe

2. **Alert Configurations** (Admin + Steward)
   - Configuration des protocoles de notification systeme

3. **Node Network** (Admin uniquement)
   - Configuration des endpoints du cluster et tampons de latence

4. **Access Control** (Admin uniquement)
   - Permissions granulaires par role et regles MFA

5. **Engine Scaling** (Admin uniquement)
   - Modification de la concurrence des services Presidio et Cleaning

6. **Storage Schema** (Admin uniquement)
   - Mise a jour des pools de connexion MongoDB et Atlas

7. **Neural Roadmap V1** (Admin + Steward)
   - Cliquer ouvre un modal avec le plan de migration V1 :
     - Fonction de perte avancee : L = alpha * L_privacy + (1-alpha) * L_utility
     - Architecture Transformer (code Python)
     - Jalons d'implementation (Phase 1: RoBERTa, Phase 2: DP-SGD, Phase 3: Training distribue)

8. **Interface Theme** (Tous les roles)
   - Personnalisation de l'esthetique et du branding

#### Section Synchronisation Atlas
- En bas de la page, section "Governance Sync Required"
- Bouton "Sync Glossary to Atlas" : Synchronise les taxonomies PII/SPI avec Apache Atlas
- Bouton "Open Atlas UI" : Ouvre l'interface Apache Atlas dans un nouvel onglet
- Description : "Synchronize local taxonomy definitions with the Apache Atlas governance cluster"

### 5.5 Menu Lateral Admin

L'administrateur voit les elements suivants dans le menu lateral :
1. **Dashboard** (icone tableau de bord)
2. **User Control** (icone utilisateurs)
3. **Audit Logs** (icone historique)
4. **Settings** (icone engrenage)
5. **Logout** (icone deconnexion, en rouge)

---

## 6. Guide Role : Data Steward

### 6.1 Dashboard Steward

**Acces** : Automatique apres connexion

**Ce que vous voyez :**

#### Section Hero de Bienvenue
- Badge "Data Steward" en vert emeraude
- Description : "Primary Focus: Quality standards, compliance auditing, and metadata cataloging"
- 3 boutons d'action rapide :
  - "Sync Taxonomy" --> Synchronise les tags PII/SPI vers Apache Atlas
  - "Quality Audit" --> redirige vers /quality
  - "Forensic Review" --> redirige vers /audit

#### Panneau "Compliance Trend (ISO 25012)" (exclusif Steward)
- Graphique a barres animees montrant la tendance de conformite
- Indicateur "+12% This Week"
- Derive d'assurance qualite : LOW

#### Section "Governance Operations" (Admin + Steward)
- Bouton "Sync Taxonomy to Atlas"
- Bouton "View Audit Logs"
- Bouton "Data Discovery"

*(Les autres sections sont identiques au Dashboard Admin : statistiques, cluster, hierarchie des roles)*

### 6.2 Data Discovery

**Acces** : Menu lateral --> "Data Discovery" ou `/discovery`
**Restriction** : Steward uniquement dans le menu (Admin et Annotator y ont aussi acces via la route)

**Ce que vous voyez :**

#### En-tete
- Titre "Data Discovery" avec icone loupe
- Description "Advanced Catalog Search (Apache Atlas / Solr)"
- Bouton "Refresh Catalog" : Recharge les donnees depuis le backend
- Bouton "Open Atlas UI" : Ouvre l'interface Apache Atlas

#### Panneau Lateral de Facettes (colonne gauche, 3 filtres)

1. **Data Domain** (icone base de donnees, bleu)
   - Filtres cliquables : Health, Finance, HR, Legal, Gov, General
   - Cliquer sur un domaine l'active (fond bleu) / le desactive

2. **PII Entities** (icone bouclier, rouge)
   - Tags cliquables : CIN, PHONE, EMAIL, IBAN, PASSPORT + types detectes dynamiquement
   - Cliquer sur un type l'active (bordure rouge) / le desactive

3. **Classification** (icone bouclier, violet)
   - Niveaux : CONFIDENTIAL, INTERNAL, PUBLIC
   - Cliquer sur un niveau l'active (fond violet) / le desactive

Les filtres sont combinables : vous pouvez activer plusieurs filtres de differentes categories simultanement.

#### Zone de Resultats (colonne droite)

- **Barre de recherche** : "Search for datasets, columns, or business terms..."
  - Tapez un terme et appuyez Entree ou cliquez "Search"
- **Compteur** : "X Assets Found"
- **Liste des datasets** : Pour chaque dataset :
  - Icone base de donnees + nom du dataset
  - Badge de classification (CONFIDENTIAL en rouge, INTERNAL en orange, PUBLIC en vert)
  - Badge de domaine (en bleu)
  - Tags PII avec prefix # (ex: #CIN, #PHONE)
  - Proprietaire (Owner) et date de mise a jour
  - GUID Atlas (si disponible) avec icone lien externe
- Si aucun resultat : Message "No assets match your search criteria" avec bouton "Clear All Filters"

### 6.3 Quality Hub

**Acces** : Menu lateral --> "Quality Hub" ou `/quality`
**Restriction** : Admin et Steward

**Ce que vous voyez :**

#### En-tete
- Titre "Quality Hub"
- Description "ISO 25012 Data Quality Model Analysis (Sub-Second Evaluation)"
- Liste deroulante pour selectionner un dataset
- Bouton d'export PDF (apparait apres evaluation)
- Bouton "Trigger Audit" pour lancer l'evaluation

#### Avant Evaluation
- Zone vide avec icone et message "Ready for ISO 25012 Evaluation"
- Instruction : "Select a dataset from the repository above to generate a high-precision quality report"

#### Apres Evaluation (cliquer sur "Trigger Audit")

**Section Metriques Principales (2 panneaux) :**

1. **CORE COMPLIANCE** (panneau gauche)
   - Grade global (A, B, C, D, F) avec badge colore
   - Graphique radial (RadialBarChart) avec les dimensions de qualite
   - Legende des couleurs : Vert = >80%, Orange = 50-80%, Rouge = <50%
   - Dimensions ISO 25012 : Completeness, Accuracy, Consistency, etc.

2. **Global Score Index** (panneau droit)
   - Score global en grand (ex: 78%)
   - Barres de progression pour chaque dimension :
     - Nom de la dimension en majuscules
     - Pourcentage
     - Barre coloree (vert >80%, orange 50-80%, rouge <50%)

**Section Recommandations :**
- Grille de cartes de recommandations
- Chaque carte contient :
  - Icone bouclier
  - Numero de recommandation
  - Texte de recommandation detaille

**Export PDF :**
1. Cliquez sur le bouton fleche vers le bas (a cote de "Trigger Audit")
2. Un document PDF est genere avec :
   - En-tete "ISO 25012 Quality Report"
   - Grade et score global
   - Tableau des dimensions avec scores et statuts
   - Liste des recommandations
3. Le fichier se telecharge automatiquement

### 6.4 Journaux d'Audit (Audit Logs)

Identique a la section 5.3 (voir le guide Admin). Le Steward a acces a toutes les memes fonctionnalites d'audit que l'Admin.

### 6.5 Menu Lateral Steward

Le Data Steward voit les elements suivants dans le menu lateral :
1. **Dashboard** (icone tableau de bord)
2. **Data Discovery** (icone recherche fichier)
3. **Quality Hub** (icone coche)
4. **Audit Logs** (icone historique)
5. **Logout** (icone deconnexion, en rouge)

---

## 7. Guide Role : Annotateur (Annotator)

### 7.1 Dashboard Annotateur

**Acces** : Automatique apres connexion

**Ce que vous voyez :**

#### Section Hero de Bienvenue
- Badge "Data Annotator" en violet-rose
- Description : "Primary Focus: Data ingestion, profiling, and AI-assisted correction"
- 2 boutons d'action rapide :
  - "Upload Dataset" --> redirige vers /datasets
  - "Validate Detections" --> redirige vers /tasks

#### Panneau "Inter-Annotator Agreement" (exclusif Annotator)
- Valeur kappa affichee en grand : kappa = 0.88
- Label "Inter-Annotator Agreement"
- Badge "High Consistency Match"

*(Les autres sections sont identiques : statistiques, cluster, hierarchie des roles)*

### 7.2 Pipeline de Donnees (Data Pipeline / Ingestion Engine)

**Acces** : Menu lateral --> "Data Pipeline" ou `/datasets`
**Restriction** : Annotator uniquement pour l'upload (les autres roles voient un message "Restricted Access")

**Ce que vous voyez :**

#### En-tete
- Titre "Ingestion Engine"
- Description "Securely upload and register datasets into the DataGov ecosystem"

#### Zone d'Upload (Annotator uniquement)
- Zone de glisser-deposer (Drag & Drop) avec :
  - Icone upload
  - Texte "Drag & Drop or Click to Ingest"
  - Formats supportes : CSV, JSON, Excel (Max 500MB)
  - Bouton "Browse Secondary Storage"

**Comment uploader un dataset :**
1. **Methode 1 - Glisser-Deposer** : Glissez un fichier CSV, JSON ou Excel sur la zone
2. **Methode 2 - Clic** : Cliquez sur la zone pour ouvrir le selecteur de fichiers
3. Un apercu du fichier s'affiche avec son nom et sa taille
4. Cliquez sur "Begin High-Speed Ingestion"
5. Une barre de progression s'affiche :
   - "Streaming to Cluster" pendant l'upload
   - "Indexing Taxonomy" pendant le traitement
6. Succes : Message "Ingestion Complete" avec :
   - Notification "Dataset registered in Apache Atlas"
   - Notification "Airflow DAG Started: cleaning_pipeline_v1"
   - Bouton "Upload Another" pour continuer
   - Bouton "Scan for PII" pour aller a la detection PII

Si un autre role que Annotator accede a cette page, il voit un panneau rouge "Restricted Access" avec le message "Only the Data Annotator role is authorized to ingest raw datasets."

#### Repository Log (Tableau des Datasets)
- Accessible a tous les roles qui arrivent sur cette page
- Barre de recherche "Search repository..."
- Bouton rafraichir

**Tableau avec colonnes :**
- **Dataset Name** : Icone + nom du dataset
- **System ID** : Identifiant court (8 premiers caracteres)
- **Accession Date** : Date d'upload
- **Status** : Badge vert "Ready"
- **Actions** :
  - Icone oeil : Cliquer sur la ligne pour voir les details
  - Icone poubelle rouge (Admin et Steward uniquement) : Supprimer le dataset

**Cliquer sur un dataset** ouvre un modal avec :
- Nom du dataset et ID complet (avec bouton copier)
- 3 cartes d'info : Status, Type, Date
- **Onglets** :
  - "Data Preview" : Tableau des 5 premieres lignes (Admin et Steward uniquement, les autres voient "Access Restricted")
  - "Lineage Trace" : Visualisation du lignage des donnees
- **Boutons d'action** :
  - "Scan for PII" --> redirige vers la page PII Detection
  - "Quality Audit" (Admin/Steward) --> redirige vers Quality Hub
  - "Lineage Graph" (Admin/Steward) --> ouvre le graphe de lignage

#### Section Exports Hub
- Liste des fichiers exportes disponibles au telechargement
- Pour chaque export : nom, taille, date, type, bouton "Download"

### 7.3 Detection PII (PII Sentinel)

**Acces** : Menu lateral --> "PII Detection" ou `/pii`
**Restriction** : Admin, Steward et Annotator

**Ce que vous voyez :**

#### En-tete
- Badge "Security Layer"
- Titre "PII Sentinel"
- Description "Deep scanning for Moroccan sensitive personal information (CIN, Phone, RIB)"

#### Panneau de Statistiques (apres un scan)
4 cartes :
- **Total Detections** : Nombre total de PII detectees
- **Critical Risk** (rouge) : Nombre de PII a risque critique (CIN, IBAN, Passeport)
- **Entity Types** : Nombre de types d'entites distincts (survol affiche le detail)
- **Avg Confidence** : Confiance moyenne de l'IA (70%+ = fiable, 50-70% = revision necessaire)

#### Filtres par Type d'Entite
- Boutons cliquables en haut : ALL, CIN, PHONE_NUMBER, SENSITIVE_DATA, EMAIL, IBAN
- Cliquer sur un type filtre les resultats pour ce type uniquement

#### Zone d'Analyse (colonne gauche, 2/3 de la largeur)

**Onglet "Text Inspector" :**
1. Zone de texte libre "RAW DATA INPUT"
2. Collez du texte contenant potentiellement des donnees sensibles
3. Cliquez sur "Scan Buffer"

**Onglet "Volume Scan" :**
1. Liste deroulante "SELECT TARGET REPOSITORY" avec tous les datasets uploades
2. Selectionnez un dataset
3. Indicator vert "Ready for Compliance Scan"
4. Cliquez sur "Full Volume Audit"

#### Zone de Resultats (colonne droite, 1/3 de la largeur)

- Titre "Audit Results" avec compteur
- Bouton oeil (Admin et Steward uniquement) : Basculer l'affichage des valeurs PII / valeurs masquees
- Pour les Annotators : Mention "Values Restricted" (les valeurs reelles sont masquees)

**Chaque detection affichee :**
- Type d'entite (ex: "Moroccan National ID")
- Score de confiance (ex: 95%)
- Valeur detectee (visible pour Admin/Steward, "[REDACTED]" pour les autres)
- Code couleur selon le risque :
  - Rouge = Critique (CIN, IBAN, CNSS, Passeport)
  - Orange = Eleve (Telephone, Permis de conduire)
  - Jaune = Moyen (Email, Nom)
  - Bleu = Faible (Localisation, Date)

**Cliquer sur une detection** ouvre un modal detaille avec :
- Badge de risque (Critical/High/Medium/Low)
- Nom et type de l'entite
- Valeur detectee (Admin/Steward) ou "[RESTRICTED]" (autres)
- Barre de confiance
- Position dans le texte (Start-End)
- Description de l'entite (contexte marocain)

**Actions apres scan :**
- "Export Report (CSV)" : Telecharge un rapport CSV avec toutes les detections
- "Submit to Processing" (bouton vert) : Envoie les detections au pipeline de traitement, cree des taches d'annotation
- "PURGE AUDIT BUFFER" : Efface les resultats

### 7.4 File d'Attente des Taches (Task Queue)

**Acces** : Menu lateral --> "Task Queue" ou `/tasks`
**Restriction** : Annotator et Labeler

**Ce que vous voyez :**

#### En-tete Performance
- Panneau principal "Annotator Command" avec :
  - Icone trophee
  - Role systeme
  - Statistiques : X Resolved (vert) + X Active (orange)
- Carte "Avg Pulse Rate" : Temps moyen par enregistrement
- Carte "System Status" : Version et statut

#### 3 Onglets

**Onglet "Active Tasks" :**

Filtres :
- Filtre par statut : All Status, Pending, Assigned, Completed
- Filtre par priorite : All Priority, Critical, High, Medium, Low
- Bouton rafraichir

**Chaque tache affiche :**
- Bordure gauche coloree selon la priorite :
  - Rouge fonce = Critical
  - Rouge clair = High
  - Orange = Medium
  - Violet = Low
- Batch ID (premiers caracteres de l'ID)
- Type d'annotation (ex: "PII VALIDATION")
- Badge de statut (pending/assigned/completed)
- Dataset ID et horodatage
- Fragment de metadonnees (extrait JSON)

**Actions par tache :**
- Si statut "pending" :
  - Bouton "Claim" (bleu) : Revendiquer la tache et se l'assigner
  - Bouton oeil : Voir les details
- Si statut "assigned" :
  - Bouton X rouge : Rejeter la detection ("Not PII")
  - Bouton coche vert : Valider la detection ("Confirm Valid PII")
  - Bouton oeil : Voir les details

**Modal de Details de Tache :**
Cliquer sur le bouton oeil ouvre un modal avec :
- Titre "Task Analysis" avec ID de la tache
- Section "DETECTED ISSUES" (depliable) :
  - Liste des problemes detectes groupes par type
  - Score de confiance
  - Explication de l'analyse (si disponible)
- Section "Row Content" :
  - Affichage des donnees en format tableau (si array) ou cle-valeur (si objet)
  - Les valeurs qui correspondent a des detections sont surlignees en rouge
  - Bouton "Edit Data" (Admin, Steward, Annotator uniquement, PAS Labeler) :
    - Active le mode edition
    - Champs de texte editables pour corriger les donnees
  - Bouton copier JSON
- Actions :
  - "Reject (Not PII)" : Rejette la detection
  - "Confirm Valid PII" : Valide la detection
  - "Save & Validate" (en mode edition) : Sauvegarde les corrections et valide

**Onglet "Corrections (T5)" :**
- Liste des corrections suggerees par le modele T5
- Chaque correction affiche :
  - Type de probleme (ex: "SPELLING")
  - Valeur originale (en rouge)
  - Fleche de direction
  - Suggestion T5 (en vert)
  - Score de confiance
  - Boutons Accept (coche verte) / Reject (X rouge)

**Onglet "Export History" :**
- Liste des fichiers exportes (golden records)
- Chaque fichier affiche : nom, taille, date, type
- Bouton "Download" pour telecharger

### 7.5 Menu Lateral Annotateur

L'annotateur voit les elements suivants dans le menu lateral :
1. **Dashboard** (icone tableau de bord)
2. **Data Pipeline** (icone base de donnees)
3. **PII Detection** (icone bouclier alerte)
4. **Task Queue** (icone presse-papiers)
5. **Logout** (icone deconnexion, en rouge)

---

## 8. Guide Role : Labeler

### 8.1 Dashboard Labeler

**Acces** : Automatique apres connexion

**Ce que vous voyez :**

#### Section Hero de Bienvenue
- Badge "Data Labeler" en cyan-turquoise
- Description : "Primary Focus: Restricted, high-volume manual tagging of sensitive entities"
- 1 bouton d'action rapide :
  - "My Tasks" --> redirige vers /tasks

#### Panneau "Daily Quota Progress" (exclusif Labeler)
- Titre "Daily Quota Progress"
- Badge "8/10 Tasks"
- Barre de progression (ex: 80% Complete)
- Indicateur "2 Remaining"

*(Les autres sections sont identiques : statistiques, cluster, hierarchie des roles)*

### 8.2 File d'Attente des Taches (Task Queue)

**Acces** : Menu lateral --> "Task Queue" ou `/tasks`

Le Labeler a acces aux memes 3 onglets que l'Annotateur (Active Tasks, Export History, Corrections T5), avec les differences suivantes :

**Restrictions du Labeler :**
- **Pas d'edition des donnees** : Le bouton "Edit Data" n'apparait PAS dans le modal de details. Le Labeler ne peut que consulter les donnees en lecture seule
- **Actions limitees** : Il peut uniquement Claim, Valider ou Rejeter des taches

**Workflow du Labeler :**
1. Ouvrir la page "Task Queue"
2. Voir les taches en attente (statut "pending")
3. Cliquer "Claim" pour revendiquer une tache
4. Cliquer sur l'icone oeil pour voir les details
5. Examiner les donnees (lecture seule)
6. Valider (coche verte) ou Rejeter (X rouge) la detection
7. La tache disparait de la file et les statistiques se mettent a jour

### 8.3 Menu Lateral Labeler

Le Labeler voit les elements suivants dans le menu lateral :
1. **Dashboard** (icone tableau de bord)
2. **Task Queue** (icone presse-papiers)
3. **Logout** (icone deconnexion, en rouge)

---

## 9. Matrice d'Acces Detaillee

### 9.1 Acces aux Pages

| Page | Route | Admin | Steward | Annotator | Labeler |
|------|-------|-------|---------|-----------|---------|
| Landing Page | `/` | Oui (public) | Oui (public) | Oui (public) | Oui (public) |
| Login | `/login` | Oui | Oui | Oui | Oui |
| Signup | `/signup` | Oui | Oui | Oui | Oui |
| Dashboard | `/dashboard` | Oui | Oui | Oui | Oui |
| Data Pipeline | `/datasets` | Oui (route) | Oui (route) | Oui (menu) | Non |
| PII Detection | `/pii` | Oui (route) | Oui (route) | Oui (menu) | Non |
| Data Discovery | `/discovery` | Oui (route) | Oui (menu) | Oui (route) | Non |
| Quality Hub | `/quality` | Oui (route) | Oui (menu) | Non | Non |
| Task Queue | `/tasks` | Oui (route) | Oui (route) | Oui (menu) | Oui (menu) |
| User Control | `/users` | Oui (menu) | Non | Non | Non |
| Audit Logs | `/audit` | Oui (menu) | Oui (menu) | Non | Non |
| Settings | `/settings` | Oui (menu) | Non | Non | Non |

**Legende :**
- "Oui (menu)" = Visible dans le menu lateral ET accessible
- "Oui (route)" = Accessible via URL mais PAS dans le menu lateral
- "Non" = Redirige vers /dashboard si tente

### 9.2 Acces aux Fonctionnalites

| Fonctionnalite | Admin | Steward | Annotator | Labeler |
|----------------|-------|---------|-----------|---------|
| Upload de datasets | Non | Non | Oui | Non |
| Suppression de datasets | Oui | Oui | Non | Non |
| Voir apercu donnees brutes | Oui | Oui | Non | Non |
| Voir valeurs PII detectees | Oui | Oui | Non | Non |
| Editer donnees dans taches | Oui | Oui | Oui | Non |
| Valider/Rejeter taches | Oui | Oui | Oui | Oui |
| Revendiquer taches | Oui | Oui | Oui | Oui |
| Evaluer qualite ISO 25012 | Oui | Oui | Non | Non |
| Exporter rapport PDF qualite | Oui | Oui | Non | Non |
| Exporter rapport CSV PII | Oui | Oui | Oui | Non |
| Gerer utilisateurs | Oui | Non | Non | Non |
| Approuver/rejeter comptes | Oui | Non | Non | Non |
| Configurer poids EthiMask | Oui | Oui | Non | Non |
| Synchroniser Atlas | Oui | Oui | Non | Non |
| Voir journaux d'audit | Oui | Oui | Non | Non |
| Exporter PDF audit | Oui | Oui | Non | Non |
| Relancer entrainement EthiMask | Oui | Oui | Non | Non |
| Configurer parametres systeme | Oui | Non | Non | Non |
| Initialiser chiffrement HE | Oui | Non | Non | Non |
| Recherche Data Discovery | Oui | Oui | Oui | Non |

---

## 10. Workflows Complets

### 10.1 Workflow Principal : De l'Ingestion a la Gouvernance

Ce workflow illustre le parcours complet d'un dataset depuis l'upload jusqu'a la gouvernance :

```
1. ANNOTATEUR : Upload du Dataset
   /datasets --> Glisser-deposer un fichier CSV
   --> Le systeme declenche automatiquement le pipeline Airflow
   --> Le dataset est enregistre dans Apache Atlas

2. ANNOTATEUR : Detection PII
   /pii --> Selectionner le dataset dans "Volume Scan"
   --> Cliquer "Full Volume Audit"
   --> Examiner les detections (CIN, Phone, IBAN, etc.)
   --> Cliquer "Submit to Processing"
   --> Des taches sont creees pour validation humaine

3. ANNOTATEUR / LABELER : Validation des Taches
   /tasks --> Voir les taches creees
   --> Cliquer "Claim" pour revendiquer une tache
   --> Ouvrir les details (icone oeil)
   --> Examiner les detections et les donnees
   --> Valider (coche verte) ou Rejeter (X rouge)
   --> L'annotateur peut aussi editer les donnees si necessaire

4. ANNOTATEUR : Corrections T5
   /tasks --> Onglet "Corrections (T5)"
   --> Examiner les suggestions du modele T5
   --> Accepter ou rejeter chaque correction

5. STEWARD : Evaluation Qualite
   /quality --> Selectionner le dataset
   --> Cliquer "Trigger Audit"
   --> Examiner le rapport ISO 25012
   --> Exporter en PDF si necessaire

6. STEWARD : Data Discovery & Catalogage
   /discovery --> Rechercher le dataset dans le catalogue
   --> Verifier la classification, les tags PII, le domaine
   --> Verifier le GUID Atlas

7. ADMIN / STEWARD : Synchronisation Atlas
   Dashboard ou /settings --> Cliquer "Sync Taxonomy to Atlas"
   --> Les definitions PII/SPI sont synchronisees avec Apache Atlas

8. ADMIN / STEWARD : Audit
   /audit --> Consulter les journaux d'audit
   --> Verifier les operations effectuees
   --> Exporter le rapport forensique en PDF
```

### 10.2 Workflow d'Approbation des Utilisateurs

```
1. NOUVEL UTILISATEUR : Inscription
   /signup --> Remplir le formulaire
   --> Choisir un role
   --> Cliquer "Create Account"
   --> Statut : "pending"

2. ADMINISTRATEUR : Approbation
   /users --> Voir le nouvel utilisateur avec statut "pending" (orange)
   --> Survoler la ligne
   --> Cliquer la coche verte pour approuver
   OU
   --> Cliquer le X rouge pour rejeter

3. UTILISATEUR APPROUVE : Connexion
   /login --> Se connecter avec les identifiants
   --> Acces au Dashboard selon le role assigne
```

### 10.3 Workflow de Masquage Ethique (EthiMask)

```
1. ADMIN : Configurer les Poids du Perceptron
   /settings --> Cliquer "Governance Policy"
   --> Ajuster les 6 curseurs (ws, wr, wc, wp, b, alpha)
   --> Verifier que la somme des poids = 1.0
   --> Cliquer "Commit Weight Configuration"

2. ADMIN (optionnel) : Initialiser le Chiffrement Homomorphe
   /settings --> Governance Policy
   --> Section HE --> "Initialize Context"

3. STEWARD : Consulter les Logs de Masquage
   /audit --> Onglet "Masking Forensics"
   --> Filtrer par role, type d'entite, ou date
   --> Examiner les decisions de masquage

4. ADMIN / STEWARD : Relancer l'Entrainement
   /audit --> Cliquer "Retrain Pattern"
   --> Le modele EthiMask est relance avec les nouveaux logs
```

---

## 11. Navigation et Interface Commune

### 11.1 Barre Laterale (Sidebar)

La barre laterale est presente sur toutes les pages apres connexion. Elle contient :

- **Logo DataGov** en haut avec le role affiche en sous-titre
- **Menu de navigation** : Adapte au role (voir sections 5.5, 6.5, 7.5, 8.3)
- **Bouton Collapse** : Reduit la barre laterale en mode icones uniquement
- **Bouton Logout** : Deconnexion (rouge)

### 11.2 En-tete Principal (Shell)

L'en-tete de l'application affiche :
- "System Workspace" en sous-titre
- "Main Command Deck" en titre principal
- Indicateur de statut systeme (point colore) :
  - Vert pulsant = Operational
  - Orange pulsant = Degraded
  - Rouge rebondissant = Critical
- **Access Indicator** (Ranger) : Affiche le niveau d'acces securite de l'utilisateur base sur Apache Ranger
- Statut des noeuds : "X / Y Nodes Active"

### 11.3 Notifications (Toast)

Le systeme affiche des notifications temporaires en bas a droite :
- **Succes** (vert) : Operation reussie
- **Erreur** (rouge) : Operation echouee
- **Info** (bleu) : Information
- Les notifications disparaissent automatiquement apres quelques secondes

### 11.4 Modales

Plusieurs pages utilisent des modales (fenetres superposees) :
- Cliquer a l'exterieur de la modale la ferme
- Bouton X en haut a droite pour fermer
- Animation d'ouverture et de fermeture

---

## 12. FAQ et Depannage

### Q1 : Je ne peux pas me connecter
- Verifiez que vos identifiants sont corrects
- Si vous venez de creer un compte, votre statut est "pending" - contactez l'administrateur pour approbation
- Verifiez que les services Docker sont en cours d'execution (`docker-compose ps`)

### Q2 : Les services affichent "Offline" dans le dashboard
- Certains services (Classification, Correction) prennent plus de temps a demarrer car ils chargent des modeles ML (BERT, T5)
- Attendez 2-3 minutes apres le demarrage de Docker
- Cliquez sur le bouton rafraichir dans la section Node Cluster

### Q3 : L'upload de dataset echoue
- Verifiez que le format est CSV, JSON ou Excel
- Verifiez que la taille ne depasse pas 500MB
- Verifiez que le service cleaning-service est en cours d'execution

### Q4 : La detection PII ne retourne aucun resultat
- Verifiez que le service presidio-service est en cours d'execution
- Essayez avec un texte contenant des donnees marocaines connues (ex: "Mon CIN est AB123456")
- Baissez le seuil de confiance si necessaire

### Q5 : La synchronisation Atlas echoue
- Verifiez que la VM VMware HDP est demarree
- Verifiez que l'IP dans le fichier .env correspond a l'IP de la VM
- Verifiez que Apache Atlas est accessible a `http://IP_VM:21000`
- Les identifiants Atlas sont : admin / ensias2025

### Q6 : Le Quality Hub ne genere pas de rapport
- Assurez-vous d'avoir selectionne un dataset dans la liste deroulante
- Verifiez que le service quality-service est en cours d'execution
- Le dataset doit avoir ete prealablement uploade et traite

### Q7 : Les taches n'apparaissent pas dans Task Queue
- Les taches sont creees lorsqu'un scan PII est soumis via "Submit to Processing"
- Verifiez que le service annotation-service est en cours d'execution
- Rafraichissez la page

### Q8 : Comment changer le role d'un utilisateur ?
- Seul l'administrateur peut modifier les roles
- Actuellement, le changement de role se fait via l'API directement :
  ```
  PUT http://localhost:8000/api/auth/users/{username}/role?role=steward
  ```

### Q9 : Comment acceder a Apache Atlas / Ranger / Ambari ?
- Apache Ambari : `http://192.168.110.134:8080` (raj_ops / raj_ops)
- Apache Atlas : `http://192.168.110.134:21000` (admin / ensias2025)
- Apache Ranger : `http://192.168.110.134:6080` (admin / hortonworks1)
- Ces services fonctionnent sur la VM VMware HDP qui doit etre demarree

### Q10 : L'interface a une couleur differente de celle attendue
- Le theme de couleur change automatiquement selon votre role
- Admin = Rouge/Orange, Steward = Vert, Annotator = Violet, Labeler = Cyan
- Si la couleur est incorrecte, deconnectez-vous et reconnectez-vous

---

## Annexe A : Architecture des Services

| Service | Port | Description |
|---------|------|-------------|
| auth-service | 8001 | Authentification, JWT, gestion des roles |
| taxonomie-service | 8002 | Taxonomie PII/SPI marocaine (47+ patterns) |
| presidio-service | 8003 | Detection PII avec Microsoft Presidio |
| cleaning-service | 8004 | Upload, profilage, nettoyage, transformation |
| classification-service | 8005 | Classification ML par ensemble (BERT + RF + Rules) |
| correction-service | 8006 | Correction automatique via T5 |
| annotation-service | 8007 | Workflow d'annotation Human-in-the-Loop |
| quality-service | 8008 | Evaluation qualite ISO 25012 |
| ethimask-service | 8009 | Masquage ethique contextuel |
| nginx-gateway | 8000 | Passerelle API reverse proxy |
| datagov-modern | 3000 | Frontend React |
| airflow | 8081 | Orchestration Apache Airflow |
| mongo | 27017 | Base de donnees MongoDB |

## Annexe B : Raccourcis et Astuces

- **Dashboard** : Les statistiques se rafraichissent automatiquement toutes les 30 secondes
- **Node Cluster** : Cliquer sur un service ouvre la documentation API (FastAPI Swagger UI)
- **Data Discovery** : Les filtres sont combinables - activez plusieurs filtres simultanement
- **Task Queue** : Utilisez les filtres de statut et de priorite pour trier efficacement les taches
- **Quality Hub** : Le rapport PDF contient toutes les dimensions ISO 25012 avec recommandations
- **Audit Logs** : Utilisez l'onglet "Masking Forensics" pour tracer les operations de masquage par role
- **Settings** : Le bouton "Normalize" ajuste automatiquement les poids pour respecter la contrainte mathematique

## Annexe C : Glossaire

| Terme | Definition |
|-------|-----------|
| PII | Personally Identifiable Information - Donnees permettant d'identifier une personne |
| SPI | Sensitive Personal Information - Sous-ensemble de PII a risque eleve |
| CIN | Carte d'Identite Nationale marocaine |
| CNSS | Caisse Nationale de Securite Sociale |
| IBAN | International Bank Account Number |
| ISO 25012 | Norme internationale de qualite des donnees |
| EthiMask | Module de masquage ethique base sur un perceptron |
| T5 | Modele de langage Text-to-Text Transfer Transformer |
| BERT | Bidirectional Encoder Representations from Transformers |
| HDP | Hortonworks Data Platform |
| RBAC | Role-Based Access Control |
| JWT | JSON Web Token |
| Golden Record | Enregistrement valide et corrige, pret pour exploitation |
| Kappa (kappa) | Coefficient d'accord inter-annotateurs |
| Atlas GUID | Identifiant unique global d'une entite dans Apache Atlas |

---

*Document genere pour le projet DataGov - ENSIAS 2025/2026*
*Ce guide couvre l'integralite des interfaces et fonctionnalites de la plateforme pour chaque role utilisateur.*
