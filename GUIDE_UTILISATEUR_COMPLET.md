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
10. [Parcours Complet Clic-par-Clic pour Chaque Role](#10-parcours-complet-clic-par-clic-pour-chaque-role)
11. [Navigation et Interface Commune](#11-navigation-et-interface-commune)
12. [FAQ et Depannage](#12-faq-et-depannage)
13. [Integration Apache Atlas, Apache Ranger et Apache Airflow](#13-integration-apache-atlas-apache-ranger-et-apache-airflow)

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
| steward_user | Steward123 | Data Steward |
| annotator_user | Annotator123 | Annotateur |
| labeler_user | Labeler123 | Labeler |

*(Note : ces comptes sont crees automatiquement au demarrage via le script `restore_all_users.py`)*

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
- Graphique a barres animees montrant l'etat de sante de chaque service (9 barres)
- Barre verte = service Healthy, barre rouge = service Offline
- Indicateur en haut a droite : "X/9 Nodes Online"
- Latence moyenne affichee en bas (calculee en temps reel a partir des health checks)

#### Panneau "Global PII Distribution"
- Tags des types PII detectes : CIN, PHONE, IBAN, EMAIL
- Nombre de noeuds collaboratifs actifs

#### Statistiques Globales (4 cartes, donnees temps reel)
- **Total Records** : Nombre total d'enregistrements (depuis l'API `/cleaning/stats`)
- **Total Datasets** : Nombre de jeux de donnees uploades (depuis l'API `/cleaning/stats`)
- **Quality Score** : Score moyen de qualite ISO 25012 (depuis l'API `/quality/stats`)
- **System Nodes** : Nombre de services Healthy / 9 total (depuis les health checks)

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

#### Section Synchronisation Atlas (en bas de la page)
- Grande carte avec icone Settings animee et titre "Governance Sync Required"
- Description : "Synchronize local taxonomy definitions with the Apache Atlas governance cluster. Required when updating PI/SPI patterns."
- **Bouton "Sync Glossary to Atlas"** : Cliquer pour synchroniser les 47 classifications + 47 termes de glossaire PII/SPI vers **Apache Atlas**. Une notification toast confirme : "Synced 47 classifications & 47 glossary terms to Atlas!"
- **Bouton "Open Atlas UI"** : Ouvre l'interface web **Apache Atlas** (http://IP_VM:21000) dans un nouvel onglet du navigateur. Vous pouvez y voir les entites cataloguees, le glossaire, et les lignages de donnees

### 5.5 Menu Lateral Admin

L'administrateur voit **tous** les elements suivants dans le menu lateral :
1. **Dashboard** (icone tableau de bord)
2. **Data Pipeline** (icone base de donnees)
3. **PII Detection** (icone bouclier alerte)
4. **Data Discovery** (icone recherche fichier)
5. **Quality Hub** (icone coche cercle)
6. **Task Queue** (icone presse-papiers)
7. **User Control** (icone utilisateurs)
8. **Audit Logs** (icone historique)
9. **Settings** (icone engrenage)
10. **Logout** (icone deconnexion, en rouge)

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
- Graphique a barres animees montrant l'etat de sante de chaque service (9 barres vertes/rouges)
- Badge en haut a droite affichant le Quality Score reel (depuis l'API `/quality/stats`)
- Indicateur en bas : "X of 9 Services Compliant"

#### Section "Governance Operations" (Admin + Steward)
- Bouton "Sync Taxonomy to Atlas"
- Bouton "View Audit Logs"
- Bouton "Data Discovery"

*(Les autres sections sont identiques au Dashboard Admin : statistiques, cluster, hierarchie des roles)*

### 6.2 Data Discovery

**Acces** : Menu lateral --> "Data Discovery" ou `/discovery`
**Restriction** : Admin, Steward et Annotator (visible dans le menu pour les trois roles)

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
2. **Data Pipeline** (icone base de donnees)
3. **PII Detection** (icone bouclier alerte)
4. **Data Discovery** (icone recherche fichier)
5. **Quality Hub** (icone coche cercle)
6. **Task Queue** (icone presse-papiers)
7. **Audit Logs** (icone historique)
8. **Logout** (icone deconnexion, en rouge)

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
- Valeur kappa affichee en grand (donnee temps reel depuis l'API `/annotation/users/{username}/stats`)
- Label "Inter-Annotator Agreement"
- Badge dynamique selon la valeur kappa :
  - kappa >= 0.75 : "High Consistency" (violet)
  - kappa >= 0.40 : "Moderate Agreement" (orange)
  - kappa < 0.40 : "Low Agreement" (gris)
  - Pas de donnees : "No Data Yet" (gris)

*(Les autres sections sont identiques : statistiques, cluster, hierarchie des roles)*

### 7.2 Pipeline de Donnees (Data Pipeline / Ingestion Engine)

**Acces** : Menu lateral --> "Data Pipeline" ou `/datasets`
**Restriction** : Admin, Steward et Annotator voient cette page dans le menu. Seul l'Annotator peut uploader des fichiers (les autres roles voient un message "Restricted Access" sur la zone d'upload)

**Ce que vous voyez :**

#### En-tete
- Titre "Ingestion Engine"
- Description "Securely upload and register datasets into the DataGov ecosystem"

#### Zone d'Upload (Admin, Steward, Annotator)
- Visible pour les roles Admin, Steward et Annotator
- Zone de glisser-deposer (Drag & Drop) avec :
  - Icone upload animee (rebondit lors du survol)
  - Texte "Drag & Drop or Click to Ingest"
  - Formats supportes : CSV, JSON, Excel (Max 500MB)
  - Bouton "Browse Secondary Storage"

**Comment uploader un dataset :**
1. **Methode 1 - Glisser-Deposer** : Glissez un fichier CSV, JSON ou Excel sur la zone (la bordure devient bleue)
2. **Methode 2 - Clic** : Cliquez n'importe ou dans la zone pour ouvrir le selecteur de fichiers
3. Un apercu du fichier s'affiche avec son nom et sa taille en MB
4. Cliquez sur "Begin High-Speed Ingestion"
5. Une barre de progression s'affiche avec pourcentage :
   - "Streaming to Cluster" pendant l'upload reseau
   - "Indexing Taxonomy" pendant le traitement serveur
6. Succes : Message "Ingestion Complete" avec :
   - **Notification toast** (en bas a droite) : "Dataset registered in Apache Atlas (ID: xxxxxxxx...)" -- Cela confirme que le dataset a ete catalogue dans **Apache Atlas**
   - **Notification toast** : "Airflow DAG Started: cleaning_pipeline_v1" -- Cela confirme que le pipeline **Apache Airflow** a ete declenche automatiquement
   - Bouton "Upload Another" pour continuer avec un autre fichier
   - Bouton "Scan for PII" pour aller directement a la page PII Detection

**Important** : Apres l'upload, le systeme declenche automatiquement :
- L'enregistrement du dataset dans **Apache Atlas** (catalogage metadata)
- Le pipeline **Apache Airflow** (16 taches : nettoyage → profilage → classification → detection PII → corrections → qualite → masquage)

Si le role **Labeler** accede a cette page, il voit un panneau rouge "Restricted Access" avec le message "Only the Data Annotator role is authorized to ingest raw datasets."

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
**Restriction** : Admin, Steward, Annotator et Labeler (tous les roles)

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
4. **Data Discovery** (icone recherche fichier)
5. **Task Queue** (icone presse-papiers)
6. **Logout** (icone deconnexion, en rouge)

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

#### Panneau "Task Progress" (exclusif Labeler)
- Titre "Task Progress"
- Badge affichant le ratio taches completees/total (donnees temps reel depuis l'API `/annotation/users/{username}/stats`)
- Barre de progression animee (pourcentage calcule automatiquement)
- Indicateur "X Remaining" en bas a droite
- Les valeurs `completed` et `pending` proviennent de l'API en temps reel

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
| Dashboard | `/dashboard` | Oui (menu) | Oui (menu) | Oui (menu) | Oui (menu) |
| Data Pipeline | `/datasets` | Oui (menu) | Oui (menu) | Oui (menu) | Non |
| PII Detection | `/pii` | Oui (menu) | Oui (menu) | Oui (menu) | Non |
| Data Discovery | `/discovery` | Oui (menu) | Oui (menu) | Oui (menu) | Non |
| Quality Hub | `/quality` | Oui (menu) | Oui (menu) | Non | Non |
| Task Queue | `/tasks` | Oui (menu) | Oui (menu) | Oui (menu) | Oui (menu) |
| User Control | `/users` | Oui (menu) | Non | Non | Non |
| Audit Logs | `/audit` | Oui (menu) | Oui (menu) | Non | Non |
| Settings | `/settings` | Oui (menu) | Non | Non | Non |

**Legende :**
- "Oui (menu)" = Visible dans le menu lateral ET accessible
- "Non" = Non visible dans le menu et redirige vers /dashboard si tente via URL

### 9.2 Acces aux Fonctionnalites

| Fonctionnalite | Admin | Steward | Annotator | Labeler |
|----------------|-------|---------|-----------|---------|
| Upload de datasets | Oui | Oui | Oui | Non |
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

## 10. Parcours Complet Clic-par-Clic pour Chaque Role

### 10.1 Parcours ADMIN : Du Login a la Gouvernance

```
ETAPE 1 : Connexion
   → Ouvrir http://localhost:3000
   → Vous voyez la Landing Page "DataSentinel" avec carousel de technologies
   → Cliquer "Login" en haut a droite
   → Entrer : admin / admin123
   → Cliquer "Sign In"
   → Vous etes redirige vers le Dashboard

ETAPE 2 : Dashboard Admin
   → Vous voyez le Hero "Welcome back, admin" avec badge rouge "Administrator"
   → 3 boutons d'action rapide : "User Management", "System Settings", "Operational Status"
   → En dessous : section "DataGov - Data Governance Platform" avec description
   → PANNEAU EXCLUSIF ADMIN : "System Benchmarks" avec 9 barres (1 par service)
      - Barres vertes = services Healthy
      - Barres rouges = services Offline
      - Badge "X/9 Nodes Online" en haut a droite
      - "Avg Latency: XXms" en bas
   → PANNEAU "Global PII Distribution" : tags CIN, PHONE, IBAN, EMAIL
   → 4 cartes statistiques : Total Records, Total Datasets, Quality Score, System Nodes
   → SECTION "Governance Operations" (visible ADMIN + STEWARD seulement) :
      - Bouton vert "Sync Taxonomy to Atlas" → CLIQUER ICI pour synchroniser avec ATLAS
      - Bouton "View Audit Logs" → va a /audit
      - Bouton "Data Discovery" → va a /discovery
   → Grille "Node Cluster" : 9 services cliquables
      - CLIQUER sur un service → Modal avec nom, port, description, bouton "API Docs"
      - Le bouton "API Docs" ouvre la documentation Swagger FastAPI du service
   → Section "Role Hierarchy" : liste des 4 roles, badge "YOU" sur Admin

ETAPE 3 : Menu lateral Admin (9 pages accessibles)
   → Dashboard | Data Pipeline | PII Detection | Data Discovery
   → Quality Hub | Task Queue | User Control | Audit Logs | Settings

ETAPE 4 : User Control (/users) - Gestion des utilisateurs
   → Cliquer "User Control" dans le menu lateral
   → Vous voyez le tableau de tous les utilisateurs
   → Compteurs en haut : Total, Active (vert), Pending (orange)
   → Pour un utilisateur "pending" : survoler la ligne → boutons apparaissent
      - Coche verte → approuver (statut passe a "active")
      - X rouge → rejeter (statut passe a "rejected")

ETAPE 5 : Data Pipeline (/datasets) - Upload et catalogue
   → Cliquer "Data Pipeline" dans le menu lateral
   → Zone d'upload Drag & Drop visible (Admin PEUT uploader)
   → Glisser un fichier CSV → apercu avec nom + taille
   → Cliquer "Begin High-Speed Ingestion"
   → Barre de progression → "Streaming to Cluster" → "Indexing Taxonomy"
   → SUCCES → 2 notifications toast :
      - "Dataset registered in Apache Atlas (ID: xxx...)" ← ATLAS
      - "Airflow DAG Started: cleaning_pipeline_v1" ← AIRFLOW
   → Tableau "Repository Log" : liste des datasets avec nom, ID, date, statut
   → CLIQUER sur un dataset → Modal avec :
      - 3 cartes info (Status, Type, Date)
      - Onglet "Data Preview" : tableau des 5 premieres lignes (Admin PEUT voir)
      - Onglet "Lineage Trace" : graphe du lignage depuis ATLAS
      - Boutons : "Scan for PII", "Quality Audit", "Lineage Graph"
   → Icone poubelle rouge pour supprimer un dataset (Admin PEUT supprimer)
   → Section "Exports Hub" en bas : fichiers CSV exportes telechargeables

ETAPE 6 : PII Detection (/pii)
   → Cliquer "PII Detection" dans le menu lateral
   → 2 onglets : "Text Inspector" (texte libre) ou "Volume Scan" (dataset)
   → Pour "Volume Scan" : selectionner un dataset dans la liste deroulante
   → Cliquer "Full Volume Audit"
   → RESULTATS (colonne droite) :
      - Chaque detection affiche : type, confiance (%), valeur
      - Admin VOIT les valeurs reelles (CIN, phone, etc.)
      - Bouton oeil pour basculer affichage des valeurs
   → 4 cartes stats : Total Detections, Critical Risk, Entity Types, Avg Confidence
   → Boutons : "Export Report (CSV)", "Submit to Processing", "PURGE AUDIT BUFFER"
   → CLIQUER sur une detection → Modal "Forensic Detail" avec :
      - Badge de risque (Critical/High/Medium/Low)
      - Valeur detectee (visible pour Admin)
      - Barre de confiance + position dans le texte
      - Description de l'entite (contexte marocain)

ETAPE 7 : Quality Hub (/quality)
   → Cliquer "Quality Hub" dans le menu lateral
   → Selectionner un dataset dans la liste deroulante
   → Cliquer "Trigger Audit"
   → Rapport ISO 25012 avec : grade (A-F), graphique radial, 6 dimensions
   → Bouton export PDF

ETAPE 8 : Settings (/settings) - Configuration et ATLAS
   → Cliquer "Settings" dans le menu lateral
   → 8 cartes de configuration (toutes visibles pour Admin)
   → CLIQUER "Governance Policy" → Modal EthiMask :
      - 6 curseurs de poids du perceptron (ws, wr, wc, wp, b, alpha)
      - Equation : Score T' = sigma(somme w_i * x_i + b)
      - Bouton "Normalize" pour normaliser les poids
      - Bouton "Commit Weight Configuration" pour sauvegarder
      - Section Homomorphic Encryption avec "Initialize Context"
   → CLIQUER "Neural Roadmap V1" → Modal avec plan migration Transformer
   → EN BAS DE PAGE : "Governance Sync Required"
      - Bouton "Sync Glossary to Atlas" → SYNCHRONISE AVEC ATLAS
      - Bouton "Open Atlas UI" → OUVRE L'INTERFACE ATLAS dans un nouvel onglet
```

### 10.2 Parcours STEWARD : Qualite et Conformite

```
ETAPE 1 : Connexion
   → Ouvrir http://localhost:3000/login
   → Entrer : steward_user / Steward123
   → Cliquer "Sign In" → Dashboard

ETAPE 2 : Dashboard Steward
   → Hero "Welcome back, steward_user" avec badge vert "Data Steward"
   → 3 boutons d'action rapide :
      - "Sync Taxonomy" → synchronise avec ATLAS (cliquer = appel API)
      - "Quality Audit" → va a /quality
      - "Forensic Review" → va a /audit
   → PANNEAU EXCLUSIF STEWARD : "Compliance Trend (ISO 25012)"
      - 9 barres vertes/rouges (etat des services)
      - Badge Quality Score reel (ex: "78%") depuis l'API
      - "X of 9 Services Compliant" en bas
   → SECTION "Governance Operations" :
      - Bouton "Sync Taxonomy to Atlas" → CLIQUER = synchronisation ATLAS
      - Bouton "View Audit Logs" → /audit
      - Bouton "Data Discovery" → /discovery

ETAPE 3 : Menu lateral Steward (7 pages)
   → Dashboard | Data Pipeline | PII Detection | Data Discovery
   → Quality Hub | Task Queue | Audit Logs

ETAPE 4 : Quality Hub (/quality) - Evaluation ISO 25012
   → Selectionner un dataset
   → Cliquer "Trigger Audit" → rapport genere en 2-3 secondes
   → PANNEAU GAUCHE "Core Compliance" : grade (A-F) + graphique radial
   → PANNEAU DROIT "Global Score Index" : barres par dimension
      - Completeness, Accuracy, Consistency, Validity, Uniqueness, Timeliness
   → Section recommandations avec actions specifiques
   → Bouton export PDF (icone fleche vers le bas)

ETAPE 5 : Data Discovery (/discovery) - Catalogue ATLAS
   → Filtres a gauche : Data Domain, PII Entities, Classification
   → Barre de recherche "Search for datasets..."
   → Liste des datasets avec : nom, classification, domaine, tags PII
   → GUID Atlas affiche pour chaque dataset (lien externe)
   → Bouton "Open Atlas UI" en haut → OUVRE ATLAS

ETAPE 6 : Audit Logs (/audit) - Journaux forensiques
   → Onglet "General Ledger" : tous les logs systeme
   → Onglet "Masking Forensics" : logs de masquage EthiMask
   → Filtres : par role, type d'entite, date, mot-cle
   → CLIQUER sur un log → Modal "Forensic Detail Record"
   → Bouton "Export forensic PDF" → telecharge un PDF formate
   → Bouton "Retrain Pattern" → relance l'entrainement EthiMask
```

### 10.3 Parcours ANNOTATEUR : Ingestion et Validation

```
ETAPE 1 : Connexion
   → Ouvrir http://localhost:3000/login
   → Entrer : annotator_user / Annotator123
   → Cliquer "Sign In" → Dashboard

ETAPE 2 : Dashboard Annotateur
   → Hero avec badge violet "Data Annotator"
   → 2 boutons : "Upload Dataset" (→ /datasets), "Validate Detections" (→ /tasks)
   → PANNEAU EXCLUSIF : "Inter-Annotator Agreement"
      - Valeur kappa en grand (ex: "kappa = 0.85") depuis l'API en temps reel
      - Badge dynamique : "High Consistency" (violet), "Moderate Agreement" (orange),
        "Low Agreement" (gris), ou "No Data Yet"

ETAPE 3 : Menu lateral Annotateur (5 pages)
   → Dashboard | Data Pipeline | PII Detection | Data Discovery | Task Queue

ETAPE 4 : Data Pipeline (/datasets) - Upload de fichiers
   → Zone d'upload Drag & Drop visible (Annotator PEUT uploader)
   → Glisser un CSV → "Begin High-Speed Ingestion"
   → Notifications toast ATLAS + AIRFLOW apres succes
   → Tableau des datasets : cliquer pour voir details
      - Onglet "Data Preview" : CADENAS ROUGE "Access Restricted" (Annotator ne peut PAS voir les donnees brutes)
      - Onglet "Lineage Trace" : accessible
   → PAS d'icone poubelle (Annotator ne peut PAS supprimer)

ETAPE 5 : PII Detection (/pii) - Scanner les donnees
   → Meme interface que Admin/Steward MAIS :
      - Valeurs PII affichees comme "[REDACTED_1]", "[REDACTED_2]", etc.
      - Mention "Values Restricted" a cote du titre "Audit Results"
      - PAS de bouton oeil pour basculer l'affichage
   → CLIQUER sur une detection → Modal sans la valeur reelle :
      "[RESTRICTED - Admin/Steward access required]"
   → Peut exporter CSV (valeurs redactees) et "Submit to Processing"

ETAPE 6 : Task Queue (/tasks) - Valider les detections
   → En-tete : stats "X Resolved" + "X Active" depuis l'API
   → Onglet "Active Tasks" : liste des taches avec priorite (couleur bordure)
   → CLIQUER "Claim" sur une tache pending → elle vous est assignee
   → CLIQUER icone oeil → Modal "Task Analysis" avec :
      - Section "DETECTED ISSUES" (depliable)
      - Section "Row Content" avec les donnees
      - Bouton "Edit Data" → VISIBLE pour Annotator (peut corriger les donnees)
      - Bouton "Save & Validate" apres edition
   → CLIQUER coche verte → "Confirm Valid PII"
   → CLIQUER X rouge → "Reject (Not PII)"
   → Onglet "Corrections (T5)" : suggestions du modele T5 avec Accept/Reject
   → Onglet "Export History" : fichiers exportes telechargeables
```

### 10.4 Parcours LABELER : Etiquetage a Volume Eleve

```
ETAPE 1 : Connexion
   → Ouvrir http://localhost:3000/login
   → Entrer : labeler_user / Labeler123
   → Cliquer "Sign In" → Dashboard

ETAPE 2 : Dashboard Labeler
   → Hero avec badge cyan "Data Labeler"
   → 1 bouton d'action : "My Tasks" (→ /tasks)
   → PANNEAU EXCLUSIF : "Task Progress"
      - Badge "X/Y Tasks" (donnees temps reel depuis l'API)
      - Barre de progression animee (pourcentage)
      - "X% Complete" a gauche, "Y Remaining" a droite

ETAPE 3 : Menu lateral Labeler (2 pages seulement)
   → Dashboard | Task Queue

ETAPE 4 : Task Queue (/tasks) - Seule page de travail
   → Meme interface que Annotator MAIS :
      - PAS de bouton "Edit Data" dans le modal (lecture seule)
      - Peut uniquement : Claim, Valider (coche verte), Rejeter (X rouge)
      - Peut consulter les donnees mais PAS les modifier
   → Workflow :
      1. Voir les taches "pending"
      2. Cliquer "Claim" pour revendiquer
      3. Cliquer icone oeil pour examiner
      4. Lire les donnees (PAS d'edition)
      5. Valider ou Rejeter
      6. La tache disparait et les stats se mettent a jour

PAGES NON ACCESSIBLES AU LABELER :
   → /datasets → redirige vers /dashboard
   → /pii → redirige vers /dashboard
   → /quality → redirige vers /dashboard
   → /discovery → redirige vers /dashboard
   → /users → redirige vers /dashboard
   → /audit → redirige vers /dashboard
   → /settings → redirige vers /dashboard
```

### 10.5 Workflow d'Approbation des Utilisateurs

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

### 10.6 Workflow de Masquage Ethique (EthiMask)

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

## 13. Integration Apache Atlas, Apache Ranger et Apache Airflow

Cette section explique en detail **ou** et **comment** vous interagissez avec Atlas, Ranger et Airflow dans l'interface.

### 13.1 Apache Atlas (Catalogage et Gouvernance des Metadonnees)

**Qu'est-ce qu'Atlas dans DataGov ?**
Apache Atlas est le catalogue de metadonnees. Il stocke les definitions de taxonomie PII/SPI (47 classifications + 47 termes de glossaire) et enregistre chaque dataset uploade avec son lignage.

**Ou vous voyez Atlas dans l'interface :**

| Endroit | Page | Roles | Ce qui se passe quand vous cliquez |
|---------|------|-------|-------------------------------------|
| **Bouton "Sync Taxonomy to Atlas"** | Dashboard (section Governance Operations) | Admin, Steward | Envoie les 47 classifications PII/SPI marocaines vers Atlas. Notification toast verte "Taxonomy successfully synced to Atlas!" |
| **Bouton "Sync Glossary to Atlas"** | Settings (en bas de page) | Admin | Meme action que ci-dessus. Notification avec le nombre exact : "Synced 47 classifications & 47 glossary terms to Atlas!" |
| **Bouton "Open Atlas UI"** | Settings (en bas de page) | Admin | Ouvre l'interface web Apache Atlas dans un nouvel onglet (http://IP_VM:21000) |
| **Bouton "Open Atlas UI"** | Data Discovery (en-tete) | Admin, Steward, Annotator | Ouvre Atlas UI dans un nouvel onglet |
| **Notification "Dataset registered in Apache Atlas"** | Data Pipeline (apres upload) | Admin, Steward, Annotator | Toast automatique confirmant que le dataset a ete catalogue dans Atlas |
| **GUID Atlas** | Data Discovery (liste des datasets) | Admin, Steward, Annotator | Chaque dataset affiche son identifiant unique Atlas (GUID) avec icone lien externe |
| **Onglet "Lineage Trace"** | Data Pipeline (modal dataset) | Admin, Steward | Visualisation du lignage des donnees provenant d'Atlas (graphe de noeuds et aretes) |

**Processus detaille de synchronisation Atlas :**
1. Allez au Dashboard ou a la page Settings
2. Cliquez "Sync Taxonomy to Atlas" ou "Sync Glossary to Atlas"
3. Une notification bleue "Syncing Taxonomy with Apache Atlas..." apparait
4. Attendez 5-15 secondes (la synchronisation contacte le serveur Atlas)
5. Notification verte : "Taxonomy successfully synced to Atlas!" avec le nombre de termes synchronises
6. Si Atlas n'est pas accessible : notification rouge "Failed to sync with Atlas. Check logs."

### 13.2 Apache Ranger (Controle d'Acces et Politiques de Securite)

**Qu'est-ce que Ranger dans DataGov ?**
Apache Ranger gere les politiques d'acces granulaires. Il determine quelles donnees chaque role peut voir et modifier, avec evaluation en temps reel (ALLOWED / DENIED / MASKED).

**Ou vous voyez Ranger dans l'interface :**

| Endroit | Page | Roles | Ce que vous voyez |
|---------|------|-------|-------------------|
| **"Access Indicator" dans l'en-tete** | Toutes les pages (Shell) | Tous | Un badge colore a cote du statut systeme qui affiche votre niveau d'acces Ranger. Exemple : "FULL ACCESS" pour admin, "READ-ONLY" pour labeler |
| **RangerProvider (contexte global)** | Toutes les pages | Tous | Au chargement de l'application, le systeme interroge Ranger pour determiner vos droits. Cela influence ce que vous pouvez voir et faire |
| **Valeurs PII masquees** | PII Detection (resultats) | Annotator, Labeler | Si Ranger determine que votre role ne peut pas voir les valeurs PII, elles s'affichent comme "[REDACTED]" au lieu de la valeur reelle |
| **"Access Restricted" dans Data Preview** | Data Pipeline (modal dataset) | Annotator | L'onglet Data Preview affiche un cadenas rouge "Access Restricted - Only Admin and Steward can view raw data" |

**Comment fonctionne Ranger en pratique :**
- **Admin** : Voit TOUT (valeurs PII, donnees brutes, logs complets)
- **Steward** : Voit TOUT (meme niveau que admin pour les donnees)
- **Annotator** : Valeurs PII masquees ("[REDACTED]"), pas d'acces a l'apercu des donnees brutes
- **Labeler** : Acces le plus restreint, pas d'edition, valeurs masquees

### 13.3 Apache Airflow (Orchestration du Pipeline de Donnees)

**Qu'est-ce qu'Airflow dans DataGov ?**
Apache Airflow orchestre le pipeline complet de traitement des donnees. Quand un dataset est uploade, Airflow declenche automatiquement 16 taches sequentielles.

**Ou vous voyez Airflow dans l'interface :**

| Endroit | Page | Roles | Ce que vous voyez |
|---------|------|-------|-------------------|
| **Notification "Airflow DAG Started"** | Data Pipeline (apres upload) | Admin, Steward, Annotator | Toast vert "Airflow DAG Started: cleaning_pipeline_v1" - confirme que le pipeline Airflow a demarre |
| **Interface Airflow (externe)** | `http://localhost:8081` | Admin (acces direct) | Interface web Airflow avec le DAG `data_processing_pipeline` et ses 16 taches |

**Les 16 taches Airflow (dans l'ordre d'execution) :**
```
1. start                    → Point d'entree
2. check_services_health    → Verification de sante de tous les services
3. upload_dataset           → Enregistrement du dataset
4. profile_data             → Profilage statistique (YData Profiling)
5. clean_data               → Nettoyage (doublons, valeurs manquantes, outliers)
6. detect_pii_taxonomie     → Detection PII via Taxonomie marocaine (47 patterns)
7. detect_pii_presidio      → Detection PII via Microsoft Presidio
8. classify_sensitivity     → Classification de sensibilite (BERT + RF + Rules)
9. detect_inconsistencies   → Detection d'incoherences par ligne
10. apply_corrections       → Corrections automatiques par T5
11. evaluate_quality        → Evaluation ISO 25012 (6 dimensions)
12. create_annotation_tasks → Creation des taches de validation humaine
13. apply_masking           → Masquage ethique EthiMask
14. store_results           → Stockage des resultats dans MongoDB
15. export_certified        → Export du "Golden Record" (fichier CSV certifie)
16. end                     → Fin du pipeline
```

**Pour acceder a l'interface Airflow :**
1. Ouvrez `http://localhost:8081` dans votre navigateur
2. Identifiants : `admin` / mot de passe configure dans Docker
3. Vous verrez le DAG `data_processing_pipeline`
4. Cliquez sur le DAG pour voir le graphe des taches
5. Cliquez sur une tache pour voir ses logs d'execution

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
