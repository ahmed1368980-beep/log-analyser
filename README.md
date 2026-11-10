# Analyse des logs d'authentification Linux

## C'est quoi ce projet ?
Mon projet lit les fichiers auth.log d'un serveur Linux. Il garde les connexions
réussies et échouées, les met dans une base de données et affiche 3 graphiques.
Je l'ai fait pour analyser la sécurité d'un serveur.

## Ce que j'ai utilisé
- Python : le langage de tout le projet, lecture des fichiers, regex, orchestration
- PostgreSQL (psycopg2) : base de données relationnelle pour stocker les événements, requêtes rapides avec index
- API IPinfo (requests) : pour trouver le pays d'une adresse IP
- Matplotlib : dessiner les 3 graphiques dans une fenêtre

## Les dossiers
```
log-analyser/
├── Data/         # les fichiers auth.log
├── Ingestion/    # lire les fichiers, dont les .gz
├── Process/      # parser les lignes (regex) et trouver le pays des IP
├── Storage/      # base PostgreSQL
├── Serving/      # afficher les graphiques
├── config/       # réglages (settings.py) et fichier de logs (logger.py)
├── main.py       # lance tout dans l'ordre
└── README.md
```

## Comment ça marche
1. **Lecture** : le programme lit les fichiers texte et les archives .gz, ligne par ligne. Les caractères bizarres ne font pas planter.
2. **Parsing** : il trouve la date, l'heure, l'utilisateur et l'IP avec des regex.
3. **Géolocalisation** : il trouve le pays de chaque IP avec l'API IPinfo. J'ai mis un cache JSON parce que c'est plus rapide et on économise le quota gratuit.
4. **Base de données** : il stocke tout dans la table auth_events avec des index pour que les GROUP BY soient rapides.
5. **Dashboard** : il affiche 3 graphiques en barres dans une fenêtre Matplotlib.

## Comment le lancer
1. Installer les bibliothèques :
   ```bash
   pip install requests matplotlib psycopg2-binary
   ```
2. Créer la base (une seule fois, dans psql) :
   ```sql
   CREATE DATABASE auth_logs;
   ```
3. Mettre le token IPinfo et le mot de passe PostgreSQL.

   Avec PowerShell :
   ```powershell
   $env:IPINFO_TOKEN="mon_token"
   $env:DB_PASSWORD="mon_mot_de_passe"
   ```
   Avec cmd :
   ```bash
   set IPINFO_TOKEN=mon_token
   set DB_PASSWORD=mon_mot_de_passe
   ```
4. Lancer depuis le dossier du projet :
   ```bash
   python main.py
   ```

## Les 3 graphiques
1. Tentatives échouées par pays : quels pays attaquent le plus
2. Tentatives réussies par utilisateur : qui se connecte vraiment
3. Tentatives échouées avec utilisateur invalide : les noms inventés (admin, test, ...) que les robots essaient