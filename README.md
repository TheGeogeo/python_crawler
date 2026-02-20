# WEB_CRAWLER — Installation & Lancement (Linux puis Windows)

Ce projet contient :
- Un **crawler** (1 seul thread) qui récupère les liens `<a href>` d’une page HTML et les stocke en **SQLite** **sans doublons**
- Un **serveur web** (**FastAPI**) qui affiche les URLs collectées (**cliquables**)
- L’interface web **s’ouvre automatiquement** au démarrage (via le module Python `webbrowser`)


## 1) Linux (Ubuntu/Debian/Fedora…)

### 1.1 Prérequis
- Python **3.10+** (idéalement 3.11/3.12)
- `pip`
- (recommandé) `venv`
- Pour l’ouverture automatique du navigateur :
  - un environnement graphique + `xdg-open` (souvent déjà présent)
  - sinon l’app fonctionne quand même, mais il faudra ouvrir l’URL manuellement

Vérifier :
```bash
python3 --version
python3 -m pip --version
```

### 1.2 Mettre les fichiers du projet
Place ces fichiers dans un dossier (ex. `web_crawler/`) :
- `requirements.txt`
- `db.py`
- `crawler.py`
- `webapp.py`
- `run.py`

### 1.3 Créer et activer un environnement virtuel
Dans le dossier du projet :
```bash
python3 -m venv .venv
source .venv/bin/activate
```

(Optionnel) Mettre `pip` à jour :
```bash
python -m pip install --upgrade pip
```

### 1.4 Installer les dépendances
```bash
pip install -r requirements.txt
```

### 1.5 Lancer l’application
Exemple minimal :
```bash
python run.py --seed "https://example.com"
```

Comportement par défaut :
- **pas de limite** de pages (illimité)
- crawl **tous domaines** (`same-domain` OFF)

Options utiles :
- Limiter au domaine de départ :
```bash
python run.py --seed "https://example.com" --same-domain-only
```

- Limiter le nombre de pages (ex. 300) :
```bash
python run.py --seed "https://example.com" --max-pages 300
```

- Ajouter un délai entre requêtes (ex. 0.4s) :
```bash
python run.py --seed "https://example.com" --delay 0.4
```

### 1.6 Accéder à l’interface web
Au lancement, le navigateur doit s’ouvrir automatiquement sur :
- `http://127.0.0.1:8000/`

Sinon ouvrir manuellement :
- Accueil / stats : `http://127.0.0.1:8000/`
- URLs cliquables : `http://127.0.0.1:8000/urls`
- API JSON : `http://127.0.0.1:8000/api/urls`

### 1.7 Arrêter
Dans le terminal :
- `Ctrl + C`


## 2) Windows (PowerShell puis CMD)

### 2.1 Prérequis
- Python **3.10+** installé (idéalement 3.11/3.12)
- `pip`

Vérifier :
```bat
python --version
pip --version
```

### 2.2 Mettre les fichiers du projet
Place ces fichiers dans un dossier (ex. `web_crawler\`) :
- `requirements.txt`
- `db.py`
- `crawler.py`
- `webapp.py`
- `run.py`

### 2.3 Créer et activer un environnement virtuel

**PowerShell**
```bat
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Si PowerShell refuse (ExecutionPolicy) :
```bat
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
.venv\Scripts\Activate.ps1
```

**CMD (alternative)**
```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

(Optionnel) Mettre `pip` à jour :
```bat
python -m pip install --upgrade pip
```

### 2.4 Installer les dépendances
```bat
pip install -r requirements.txt
```

### 2.5 Lancer l’application
Exemple minimal :
```bat
python run.py --seed "https://example.com"
```

Options utiles :
- Limiter au domaine de départ :
```bat
python run.py --seed "https://example.com" --same-domain-only
```

- Limiter le nombre de pages :
```bat
python run.py --seed "https://example.com" --max-pages 300
```

- Délai entre requêtes :
```bat
python run.py --seed "https://example.com" --delay 0.4
```

### 2.6 Accéder à l’interface web
Le navigateur s’ouvre automatiquement sur :
- `http://127.0.0.1:8000/`

Sinon ouvrir manuellement :
- Accueil / stats : `http://127.0.0.1:8000/`
- URLs cliquables : `http://127.0.0.1:8000/urls`
- API JSON : `http://127.0.0.1:8000/api/urls`

### 2.7 Arrêter
Dans le terminal :
- `Ctrl + C`


## 3) Notes / Dépannage rapide

- Le stockage se fait dans `crawler.sqlite` (par défaut). Changer avec :
```bash
python run.py --seed "https://example.com" --db "mon_fichier.sqlite"
```

- Si le port 8000 est déjà utilisé :
```bash
python run.py --seed "https://example.com" --port 8010
```

- Sur Linux **sans interface graphique**, l’ouverture auto du navigateur peut échouer :
  l’application tourne quand même, ouvre l’URL manuellement.

- Pour un usage “propre” en production : ajouter le respect `robots.txt` + limitation de débit.
# python_crawler
