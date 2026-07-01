# grist-mcp-server

Serveur MCP (Model Context Protocol) exposant l'API REST de [Grist](https://www.getgrist.com/) à Claude Desktop / Claude Code.

## Outils exposés

- `list_orgs`, `list_workspaces`, `get_workspace`, `create_workspace`
- `create_doc`, `get_doc`
- `list_tables`, `add_tables`
- `list_columns`, `add_columns`, `update_columns`
- `list_records`, `add_records`, `update_records`, `delete_records`
- `run_sql` (SELECT en lecture seule)

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

## Test en local

```bash
mcp dev grist_mcp_server/server.py
```

Lance l'inspecteur MCP pour tester les outils interactivement.
