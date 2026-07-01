# grist-openai-plugin

Serveur [GPT Action](https://platform.openai.com/docs/actions) (FastAPI + OpenAPI) exposant l'API REST de [Grist](https://www.getgrist.com/) à un Custom GPT dans ChatGPT.

Contrairement aux anciens "plugins ChatGPT" (dépréciés par OpenAI), un GPT Action est simplement un serveur HTTP décrit par un schéma OpenAPI, importé dans l'éditeur d'un Custom GPT.

## Endpoints exposés

39 endpoints couvrant l'intégralité de l'API REST Grist : organisations, espaces de travail, documents (y compris renommage, suppression, déplacement, export XLSX/CSV/SQLite, historique, accès), tables, colonnes, enregistrements (CRUD + upsert), pièces jointes, webhooks, et SQL en lecture seule.

Voir la [référence complète des endpoints](docs/API_REFERENCE.md) pour la liste détaillée avec routes, méthodes et `operationId`.

Le schéma OpenAPI complet est généré automatiquement par FastAPI sur `/openapi.json`.

## Installation

```bash
cd src/grist-openai-plugin
pip install -e .
```

## Configuration

Copiez `.env.example` en `.env` :

- `GRIST_API_KEY` : clé API Grist (le serveur l'utilise côté serveur — elle n'est jamais exposée à ChatGPT)
- `GRIST_API_URL` : URL de base de l'API Grist (`https://docs.getgrist.com/api` par défaut)
- `ACTION_API_KEY` : jeton secret que le Custom GPT devra envoyer en `Authorization: Bearer <token>`. **Indispensable dès que le serveur est exposé publiquement**, sinon n'importe qui peut lire/écrire vos documents Grist.

## Lancer le serveur

```bash
uvicorn grist_openai_plugin.main:app --reload
```

Le serveur écoute par défaut sur `http://localhost:8000`. Documentation interactive sur `http://localhost:8000/docs`.

## Exposer le serveur publiquement

ChatGPT doit pouvoir atteindre le serveur en HTTPS. En développement, un tunnel (ex. `ngrok http 8000`) suffit ; en production, déployez-le derrière un reverse proxy HTTPS.

## Configurer le Custom GPT

1. Sur [chatgpt.com/gpts/editor](https://chatgpt.com/gpts/editor), créez ou éditez un GPT.
2. Dans **Actions**, cliquez sur **Create new action**.
3. Collez l'URL `https://<votre-domaine>/openapi.json` (ou importez le schéma manuellement).
4. **Authentication** : choisissez **API Key**, type **Bearer**, et renseignez la valeur de `ACTION_API_KEY`.
5. Testez un endpoint (ex. `listOrgs`) depuis l'éditeur pour vérifier la connexion.

## Attention

Certains endpoints suppriment définitivement des données côté Grist (`deleteOrg`, `deleteWorkspace`, `deleteDoc`, `deleteDocHistory`, `deleteRecords`, `deleteColumn`, `deleteWebhook`). Ces opérations sont **irréversibles** : le Custom GPT ne devrait les invoquer qu'après confirmation explicite de l'utilisateur.

## Test en local

```bash
curl http://localhost:8000/orgs \
  -H "Authorization: Bearer $ACTION_API_KEY"
```
