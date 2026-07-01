# grist-ai-tools

Outils permettant de connecter [Grist](https://www.getgrist.com/) (SaaS ou self-hosted) à des assistants IA :

| Projet | Ce que ça fait | Pour qui |
|---|---|---|
| [`src/grist-mcp-server`](src/grist-mcp-server) | Serveur MCP qui expose l'API Grist à **Claude Desktop** / **Claude Code** | Utilisateurs de Claude |
| [`src/grist-openai-plugin`](src/grist-openai-plugin) | Serveur GPT Action (FastAPI) qui expose l'API Grist à un **Custom GPT** dans ChatGPT | Utilisateurs de ChatGPT |

Les deux couvrent l'intégralité de l'[API REST Grist](https://support.getgrist.com/api/) : organisations, espaces de travail, documents (renommage, suppression, déplacement, export XLSX/CSV/SQLite, historique, accès), tables, colonnes, enregistrements (CRUD + upsert), pièces jointes, webhooks et SQL en lecture seule. Détail complet :

- [Référence des outils MCP](src/grist-mcp-server/docs/API_REFERENCE.md)
- [Référence des endpoints GPT Action](src/grist-openai-plugin/docs/API_REFERENCE.md)

Les deux projets sont indépendants : installez celui qui correspond à l'assistant que vous utilisez (ou les deux). Chacun a son propre README détaillé (liens ci-dessus) ; ce document est un guide d'installation général, pensé pour être suivi sur **Windows, macOS et Linux**.

## Prérequis

- **Python 3.10 ou supérieur**
  - Windows : téléchargez l'installeur sur [python.org/downloads](https://www.python.org/downloads/) et cochez **"Add python.exe to PATH"** pendant l'installation.
  - macOS : `brew install python@3.12` (avec [Homebrew](https://brew.sh/)), ou téléchargez sur [python.org](https://www.python.org/downloads/macos/).
  - Linux (Debian/Ubuntu) : `sudo apt install python3 python3-venv python3-pip`.
  - Vérifiez ensuite avec `python3 --version` (ou `python --version` sur Windows).
- **Une clé API Grist** : dans Grist, allez dans **Profil > Paramètres du compte > Clé API**, cliquez sur **Créer**, puis copiez-la. Elle vous servira pour les deux projets.
- **Git** (pour récupérer le dépôt) : [git-scm.com/downloads](https://git-scm.com/downloads).

## Récupérer le projet

```bash
git clone <url-du-dépôt> grist-ai-tools
cd grist-ai-tools
```

Sur Windows, ouvrez **PowerShell** ou l'**Invite de commandes** pour toutes les commandes ci-dessous ; sur macOS/Linux, utilisez un terminal.

## Créer un environnement virtuel Python

Un environnement virtuel isole les dépendances du projet du reste de votre système. Créez-en un à la racine, ou un par sous-projet selon vos besoins.

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Windows (Invite de commandes / cmd.exe)**

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

> Sur PowerShell, si l'activation échoue avec une erreur de politique d'exécution, lancez une fois : `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

Une fois activé, votre invite de commande affiche un préfixe `(.venv)`. Toutes les commandes `pip` suivantes doivent être lancées avec cet environnement actif. Pour le désactiver plus tard : `deactivate`.

## Installer un projet

Choisissez le projet correspondant à votre assistant IA, puis suivez son README pour la configuration complète (variables d'environnement, connexion à Claude Desktop ou à un Custom GPT, etc.).

### Option A — Claude (serveur MCP)

```bash
cd src/grist-mcp-server
pip install -e .
cp .env.example .env
```

Éditez `.env` et renseignez `GRIST_API_KEY` (et `GRIST_API_URL` si vous utilisez du self-hosted). Puis suivez la section **"Utilisation avec Claude Desktop"** du [README de grist-mcp-server](src/grist-mcp-server/README.md) pour déclarer le serveur dans `claude_desktop_config.json`.

Emplacement de `claude_desktop_config.json` selon l'OS :

- **macOS** : `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows** : `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux** : `~/.config/Claude/claude_desktop_config.json`

### Option B — ChatGPT (GPT Action)

```bash
cd src/grist-openai-plugin
pip install -e .
cp .env.example .env
```

Éditez `.env` et renseignez `GRIST_API_KEY`, `GRIST_API_URL` (optionnel) et `ACTION_API_KEY` (obligatoire dès que le serveur est exposé publiquement). Lancez ensuite le serveur :

```bash
uvicorn grist_openai_plugin.main:app --reload
```

Puis suivez la section **"Configurer le Custom GPT"** du [README de grist-openai-plugin](src/grist-openai-plugin/README.md) pour connecter votre serveur à un Custom GPT dans ChatGPT.

> Note Windows : la commande `cp` n'existe pas nativement dans cmd.exe/PowerShell. Utilisez `copy .env.example .env` (cmd) ou `Copy-Item .env.example .env` (PowerShell), ou copiez le fichier manuellement dans l'explorateur.

## Problèmes courants

- **`python: command not found` / `'python' n'est pas reconnu`** : Python n'est pas installé ou pas dans le PATH. Réinstallez en cochant l'option PATH (Windows), ou utilisez `python3` (macOS/Linux).
- **`pip: command not found`** : activez d'abord l'environnement virtuel (voir ci-dessus) ; `pip` y est disponible automatiquement.
- **Erreur d'authentification Grist (401/403)** : vérifiez que `GRIST_API_KEY` dans `.env` est correcte et que `GRIST_API_URL` correspond bien à votre instance (SaaS ou self-hosted).
- **Le Custom GPT n'arrive pas à joindre le serveur** : ChatGPT a besoin d'une URL **HTTPS** publique. En local, utilisez un tunnel comme [ngrok](https://ngrok.com/) (`ngrok http 8000`).

## Opérations sensibles

Plusieurs outils/endpoints suppriment définitivement des données Grist (organisation, espace de travail, document, historique, lignes, colonnes, webhooks). Ces opérations sont **irréversibles** — vérifiez toujours les identifiants concernés avant de les exécuter, en particulier lorsqu'ils sont déclenchés par un assistant conversationnel. Voir les sections "Attention" des références d'API liées ci-dessus.

## Structure du dépôt

```
grist-ai-tools/
├── src/
│   ├── grist-mcp-server/
│   │   ├── grist_mcp_server/    # Client API Grist + serveur MCP (outils)
│   │   ├── docs/API_REFERENCE.md  # Référence des 46 outils
│   │   └── README.md
│   └── grist-openai-plugin/
│       ├── grist_openai_plugin/   # Client API Grist + serveur FastAPI (endpoints)
│       ├── docs/API_REFERENCE.md  # Référence des 39 endpoints
│       └── README.md
└── README.md                      # Ce fichier
```
