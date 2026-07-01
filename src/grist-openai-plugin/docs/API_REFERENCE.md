# Référence des endpoints GPT Action

Ce document liste l'ensemble des 39 endpoints exposés par `grist-openai-plugin`, couvrant l'intégralité de l'API REST Grist (https://support.getgrist.com/api/). Pour l'installation et la configuration du Custom GPT, voir le [README](../README.md).

Le schéma OpenAPI complet (généré automatiquement par FastAPI) est disponible sur `/openapi.json` ; la documentation interactive sur `/docs`.

## Organisations (`/orgs`)

| Méthode | Route | operationId | Description |
|---|---|---|---|
| GET | `/orgs` | `listOrgs` | Liste les organisations accessibles. |
| PATCH | `/orgs/{org_id}` | `updateOrg` | Renomme une organisation. |
| DELETE | `/orgs/{org_id}` | `deleteOrg` | Supprime une organisation. **Irréversible.** |
| GET | `/orgs/{org_id}/access` | `listOrgAccess` | Liste les utilisateurs et leurs accès. |
| PATCH | `/orgs/{org_id}/access` | `updateOrgAccess` | Modifie les accès. |

## Espaces de travail (`/workspaces`)

| Méthode | Route | operationId | Description |
|---|---|---|---|
| GET | `/orgs/{org_id}/workspaces` | `listWorkspaces` | Liste les espaces de travail d'une organisation. |
| POST | `/orgs/{org_id}/workspaces` | `createWorkspace` | Crée un espace de travail. |
| GET | `/workspaces/{workspace_id}` | `getWorkspace` | Détails d'un espace de travail. |
| PATCH | `/workspaces/{workspace_id}` | `updateWorkspace` | Renomme un espace de travail. |
| DELETE | `/workspaces/{workspace_id}` | `deleteWorkspace` | Supprime un espace de travail. **Irréversible.** |
| GET | `/workspaces/{workspace_id}/access` | `listWorkspaceAccess` | Liste les utilisateurs et leurs accès. |
| PATCH | `/workspaces/{workspace_id}/access` | `updateWorkspaceAccess` | Modifie les accès. |

## Documents (`/docs`)

| Méthode | Route | operationId | Description |
|---|---|---|---|
| POST | `/workspaces/{workspace_id}/docs` | `createDoc` | Crée un document vide. |
| GET | `/docs/{doc_id}` | `getDoc` | Métadonnées d'un document. |
| PATCH | `/docs/{doc_id}` | `updateDoc` | Renomme un document. |
| DELETE | `/docs/{doc_id}` | `deleteDoc` | Supprime un document. **Irréversible.** |
| POST | `/docs/{doc_id}/move` | `moveDoc` | Déplace un document vers un autre espace de travail. |
| GET | `/docs/{doc_id}/download` | `downloadDoc` | Télécharge le document complet (fichier SQLite). |
| GET | `/docs/{doc_id}/download/xlsx` | `downloadDocXlsx` | Télécharge le document au format XLSX. |
| GET | `/docs/{doc_id}/download/csv` | `downloadTableCsv` | Télécharge une table au format CSV. |
| POST | `/docs/{doc_id}/force-reload` | `forceReloadDoc` | Force le rechargement du document. |
| PATCH | `/docs/{doc_id}/states/remove` | `deleteDocHistory` | Purge l'historique, en conservant les `keep` derniers états. |
| GET | `/docs/{doc_id}/access` | `listDocAccess` | Liste les utilisateurs et leurs accès. |
| PATCH | `/docs/{doc_id}/access` | `updateDocAccess` | Modifie les accès. |
| GET | `/docs/{doc_id}/usersForViewAs` | `listDocUsersForViewAs` | Liste les utilisateurs pour prévisualiser les droits ("view as"). |

## Tables

| Méthode | Route | operationId | Description |
|---|---|---|---|
| GET | `/docs/{doc_id}/tables` | `listTables` | Liste les tables du document. |
| POST | `/docs/{doc_id}/tables` | `addTables` | Crée une ou plusieurs tables. |
| PATCH | `/docs/{doc_id}/tables` | `updateTables` | Modifie des tables existantes (ex. renommage). |

## Colonnes

| Méthode | Route | operationId | Description |
|---|---|---|---|
| GET | `/docs/{doc_id}/tables/{table_id}/columns` | `listColumns` | Liste les colonnes d'une table. |
| POST | `/docs/{doc_id}/tables/{table_id}/columns` | `addColumns` | Ajoute des colonnes. |
| PATCH | `/docs/{doc_id}/tables/{table_id}/columns` | `updateColumns` | Modifie des colonnes existantes. |
| DELETE | `/docs/{doc_id}/tables/{table_id}/columns/{column_id}` | `deleteColumn` | Supprime une colonne. |

## Enregistrements (records)

| Méthode | Route | operationId | Description |
|---|---|---|---|
| GET | `/docs/{doc_id}/tables/{table_id}/records` | `listRecords` | Liste les lignes, avec filtrage/tri/limite. |
| POST | `/docs/{doc_id}/tables/{table_id}/records` | `addRecords` | Ajoute des lignes. |
| PATCH | `/docs/{doc_id}/tables/{table_id}/records` | `updateRecords` | Met à jour des lignes par ID. |
| POST | `/docs/{doc_id}/tables/{table_id}/records/delete` | `deleteRecords` | Supprime des lignes par ID. |
| PUT | `/docs/{doc_id}/tables/{table_id}/records` | `upsertRecords` | Ajoute ou met à jour des lignes, identifiées par des champs `require`. |

## Pièces jointes (`/attachments`)

| Méthode | Route | operationId | Description |
|---|---|---|---|
| GET | `/docs/{doc_id}/attachments` | `listAttachments` | Liste les métadonnées des pièces jointes. |
| POST | `/docs/{doc_id}/attachments` | `uploadAttachments` | Envoie un ou plusieurs fichiers (multipart) comme pièces jointes. |
| GET | `/docs/{doc_id}/attachments/{attachment_id}` | `getAttachmentMetadata` | Métadonnées d'une pièce jointe. |
| GET | `/docs/{doc_id}/attachments/{attachment_id}/download` | `downloadAttachment` | Télécharge le contenu d'une pièce jointe. |

## Webhooks

| Méthode | Route | operationId | Description |
|---|---|---|---|
| GET | `/docs/{doc_id}/webhooks` | `listWebhooks` | Liste les webhooks du document. |
| POST | `/docs/{doc_id}/webhooks` | `createWebhook` | Crée un webhook. |
| PATCH | `/docs/{doc_id}/webhooks/{webhook_id}` | `updateWebhook` | Modifie un webhook existant. |
| DELETE | `/docs/{doc_id}/webhooks/{webhook_id}` | `deleteWebhook` | Supprime un webhook. |

## SQL

| Méthode | Route | operationId | Description |
|---|---|---|---|
| POST | `/docs/{doc_id}/sql` | `runSql` | Exécute une requête `SELECT` en lecture seule. |

## Notes

- Les endpoints marqués **Irréversible** suppriment définitivement des données côté Grist.
- `uploadAttachments` nécessite une requête `multipart/form-data` (dépendance `python-multipart`, déjà incluse) ; ce type de requête n'est pas toujours bien géré par l'éditeur de Custom GPT — préférez un test via `curl` (voir le README) si besoin.
- Toutes les routes (sauf `/openapi.json`, `/docs`, `/redoc`) exigent l'en-tête `Authorization: Bearer <ACTION_API_KEY>` dès que celle-ci est configurée.
