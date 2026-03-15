# MongoDB and Atlas Vector Search Setup

## Overview

The app can use **MongoDB** for document storage (replacing PostgreSQL) and **MongoDB Atlas Vector Search** for vector similarity (replacing ChromaDB).

## Environment

- `USE_MONGODB=true` – use MongoDB for document storage (campaigns, experiments, dataset registry, etc.).
- `MONGODB_URI` – connection string (e.g. `mongodb://localhost:27017` or Atlas SRV `mongodb+srv://...`).
- `MONGODB_DATABASE=marketing_agent` – database name.

For vector search:

- `USE_ATLAS_VECTOR_SEARCH=true` – use Atlas Vector Search instead of ChromaDB.
- `MONGODB_VECTOR_INDEX_NAME=vector_index` – name of the Atlas vector search index (create in Atlas UI).

## Atlas Vector Search index

1. In Atlas, open your cluster → **Search** → **Create Search Index**.
2. Choose **JSON Editor** and define an index on the collection that stores embeddings (e.g. `campaign_analyses` or `UCO_Gear_Campaigns`). Each document must have an `embedding` field (array of numbers).

Example index definition (dimensions depend on your embedding model, e.g. 768 for nomic-embed-text, 1536 for OpenAI):

```json
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 768,
      "similarity": "cosine"
    }
  ]
}
```

3. Set `MONGODB_VECTOR_INDEX_NAME` to the index name you gave in Atlas.

## Local MongoDB

For local development without Atlas:

```bash
# macOS
brew install mongodb-community
brew services start mongodb-community

# .env
MONGODB_URI=mongodb://localhost:27017
USE_MONGODB=false
USE_ATLAS_VECTOR_SEARCH=false
```

Use ChromaDB for vectors when not using Atlas. For production vectors, use Atlas with a vector index as above.
