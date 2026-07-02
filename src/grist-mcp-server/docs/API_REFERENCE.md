# Référence des outils MCP

Ce document liste l'ensemble des 46 outils exposés par `grist-mcp-server`, couvrant l'intégralité de l'API REST Grist (https://support.getgrist.com/api/). Pour l'installation et la configuration, voir le [README](../README.md).

Chaque outil renvoie soit la réponse JSON de l'API Grist, soit `{"error": "...", "status_code": ...}` en cas d'échec.

## Organisations (orgs)

| Outil | Description |
|---|---|
| `list_orgs()` | Liste les organisations accessibles avec la clé API. |
| `update_org(org_id, name)` | Renomme une organisation. |
| `delete_org(org_id)` | Supprime une organisation. **Irréversible.** |
| `list_org_access(org_id)` | Liste les utilisateurs et leurs niveaux d'accès. |
| `update_org_access(org_id, users)` | Modifie les accès (`{"email": "owners"\|"editors"\|"viewers"\|null}`). |

## Espaces de travail (workspaces)

| Outil | Description |
|---|---|
| `list_workspaces(org_id)` | Liste les espaces de travail d'une organisation. |
| `get_workspace(workspace_id)` | Détails d'un espace de travail (dont les documents qu'il contient). |
| `create_workspace(org_id, name)` | Crée un nouvel espace de travail. |
| `update_workspace(workspace_id, name)` | Renomme un espace de travail. |
| `delete_workspace(workspace_id)` | Supprime un espace de travail et tous ses documents. **Irréversible.** |
| `list_workspace_access(workspace_id)` | Liste les utilisateurs et leurs niveaux d'accès. |
| `update_workspace_access(workspace_id, users)` | Modifie les accès. |

## Documents (docs)

| Outil | Description |
|---|---|
| `create_doc(workspace_id, name)` | Crée un document vide. |
| `get_doc(doc_id)` | Métadonnées d'un document. |
| `update_doc(doc_id, name)` | Renomme un document. |
| `delete_doc(doc_id)` | Supprime un document. **Irréversible.** |
| `move_doc(doc_id, workspace_id)` | Déplace un document vers un autre espace de travail. |
| `download_doc(doc_id, nohistory=False, template=False)` | Télécharge le document complet (fichier SQLite), encodé en base64. |
| `download_doc_xlsx(doc_id)` | Télécharge le document au format XLSX, encodé en base64. |
| `download_table_csv(doc_id, table_id)` | Télécharge une table au format CSV (texte). |
| `force_reload_doc(doc_id)` | Force le rechargement du document depuis le stockage. |
| `delete_doc_history(doc_id, keep)` | Purge l'historique, en conservant les `keep` derniers états. |
| `list_doc_access(doc_id)` | Liste les utilisateurs et leurs niveaux d'accès. |
| `update_doc_access(doc_id, users)` | Modifie les accès. |
| `list_doc_users_for_view_as(doc_id)` | Liste les utilisateurs disponibles pour prévisualiser les droits ("view as"). |

## Tables

| Outil | Description |
|---|---|
| `list_tables(doc_id)` | Liste les tables du document. |
| `add_tables(doc_id, tables)` | Crée une ou plusieurs tables. |
| `update_tables(doc_id, tables)` | Modifie les propriétés de tables existantes (ex. renommage). |

## Colonnes

| Outil | Description |
|---|---|
| `list_columns(doc_id, table_id)` | Liste les colonnes d'une table. |
| `add_columns(doc_id, table_id, columns)` | Ajoute des colonnes. |
| `update_columns(doc_id, table_id, columns)` | Modifie des colonnes existantes (type, label, formule...). |
| `delete_column(doc_id, table_id, column_id)` | Supprime une colonne. |

## Enregistrements (records)

| Outil | Description |
|---|---|
| `list_records(doc_id, table_id, filter=None, sort=None, limit=None)` | Liste les lignes d'une table, avec filtrage/tri/limite. |
| `add_records(doc_id, table_id, records)` | Ajoute des lignes. |
| `update_records(doc_id, table_id, records)` | Met à jour des lignes par ID. |
| `delete_records(doc_id, table_id, record_ids)` | Supprime des lignes par ID. |
| `upsert_records(doc_id, table_id, records, add=True, update=True, on_many="first")` | Ajoute ou met à jour des lignes, identifiées par des champs `require`. |

## Pièces jointes (attachments)

| Outil | Description |
|---|---|
| `list_attachments(doc_id, filter=None, sort=None, limit=None)` | Liste les métadonnées des pièces jointes du document. |
| `upload_attachments(doc_id, files)` | Envoie des fichiers comme pièces jointes ; `files: [{"filename", "content_base64"}]` (contenu inline, encodé en base64 — le serveur MCP n'a pas accès au système de fichiers de l'appelant). Renvoie leurs nouveaux IDs. |
| `get_attachment_metadata(doc_id, attachment_id)` | Métadonnées d'une pièce jointe (nom, taille, dates). |
| `download_attachment(doc_id, attachment_id)` | Télécharge le contenu d'une pièce jointe, encodé en base64. |

## Webhooks

| Outil | Description |
|---|---|
| `list_webhooks(doc_id)` | Liste les webhooks configurés sur le document. |
| `create_webhook(doc_id, fields)` | Crée un webhook (`{"url", "eventTypes", "tableId", "enabled"}`). |
| `update_webhook(doc_id, webhook_id, fields)` | Modifie un webhook existant. |
| `delete_webhook(doc_id, webhook_id)` | Supprime un webhook. |

## SQL

| Outil | Description |
|---|---|
| `run_sql(doc_id, sql, args=None)` | Exécute une requête `SELECT` en lecture seule (paramètres via `?`). |

## Notes

- Les outils marqués **Irréversible** suppriment définitivement des données côté Grist : utilisez-les avec prudence, surtout depuis un assistant conversationnel.
- Les téléchargements et téléversements binaires (`download_doc`, `download_doc_xlsx`, `download_attachment`, `upload_attachments`) transportent leur contenu encodé en base64, car le protocole MCP transporte du JSON et un client MCP distant n'a pas d'accès au système de fichiers du serveur.
- `run_sql` n'autorise que les requêtes `SELECT` ; toute écriture doit passer par les outils `records`.
- `create_webhook`/`update_webhook` peuvent échouer avec une erreur 403 explicite si le domaine de l'URL n'est pas dans la liste blanche `ALLOWED_WEBHOOK_DOMAINS` configurée côté instance Grist — ce n'est pas une erreur de syntaxe de l'appel, mais une politique de sécurité serveur (voir le README).
- `add_columns` force `isFormula: false` par défaut sur les colonnes sans champ `formula` ni `isFormula` explicite, pour éviter que les colonnes de données classiques soient créées par erreur comme colonnes formule (comportement par défaut de l'API Grist).
