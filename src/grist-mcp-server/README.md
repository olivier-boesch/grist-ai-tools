# grist-mcp-server

Serveur MCP (Model Context Protocol) exposant l'API REST de [Grist](https://www.getgrist.com/) à Claude Desktop / Claude Code.

## Outils exposés

46 outils couvrant l'intégralité de l'API REST Grist : organisations, espaces de travail, documents (y compris renommage, suppression, déplacement, export XLSX/CSV/SQLite, historique, accès), tables, colonnes, enregistrements (CRUD + upsert), pièces jointes, webhooks, et SQL en lecture seule.

Voir la [référence complète des outils](docs/API_REFERENCE.md) pour la liste détaillée avec signatures et descriptions.

## Installation

```bash
cd src/grist-mcp-server
pip install -e .
```

## Configuration

Copiez `.env.example` en `.env` et renseignez :

- `GRIST_API_KEY` : clé API Grist (Profil > Paramètres du compte > clé API)
- `GRIST_API_URL` : URL de base de l'API (`https://docs.getgrist.com/api` par défaut ; à adapter pour une instance self-hosted, ex. `https://grist.example.com/api`)

## Utilisation avec Claude Desktop

Ajoutez dans `claude_desktop_config.json` :

```json
{
  "mcpServers": {
    "grist": {
      "command": "grist-mcp-server",
      "env": {
        "GRIST_API_KEY": "votre_cle_api",
        "GRIST_API_URL": "https://docs.getgrist.com/api"
      }
    }
  }
}
```

Ou, sans installation globale, en pointant directement sur le venv du projet :

```json
{
  "mcpServers": {
    "grist": {
      "command": "/chemin/vers/venv/bin/grist-mcp-server",
      "env": {
        "GRIST_API_KEY": "votre_cle_api"
      }
    }
  }
}
```

## Attention

Certains outils suppriment définitivement des données côté Grist (`delete_org`, `delete_workspace`, `delete_doc`, `delete_doc_history`, `delete_records`, `delete_column`, `delete_webhook`). Ces opérations sont **irréversibles** : vérifiez toujours les identifiants avant de les exécuter, surtout lorsqu'ils sont invoqués par un assistant conversationnel.

## Test en local

```bash
mcp dev grist_mcp_server/server.py
```

Lance l'inspecteur MCP pour tester les outils interactivement.
