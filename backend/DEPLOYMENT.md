# GCP Cloud Run Deployment Guide

This guide explains how to deploy the Marketing Agent Backend to Google Cloud Platform (GCP) Cloud Run with secure API authentication.

## Prerequisites

1. Google Cloud SDK (`gcloud`) installed and configured
2. Docker installed locally (for building images)
3. GCP project with billing enabled
4. Cloud Run API enabled in your GCP project

## Security Configuration

### ⚠️ CRITICAL: Never Commit API Keys to Git

**API keys and secrets must NEVER be committed to version control.** Always use:
- Environment variables (for local development)
- GCP Secret Manager (for production)
- CI/CD secret management tools

The `.gitignore` file excludes `.env` files, but always verify before committing.

### API Key Authentication

The backend uses API key authentication. Set the `API_KEYS` environment variable as a comma-separated list of valid API keys.

**For local development:**
1. Copy `.env.example` to `.env` in the backend directory
2. Fill in your API keys and other configuration
3. The `.env` file is gitignored and will not be committed

**For production:**
Use GCP Secret Manager (see section below) or environment variables set directly in Cloud Run (not in code).

### Example (local .env file):
```bash
API_KEYS=key1,key2,key3
```

**Note**: If `API_KEYS` is not set or empty, authentication is disabled (development mode). Always set API keys in production.

## Running Docker Locally

Before deploying to Cloud Run, you can build and run the Docker container locally for testing.

### Prerequisites

1. Docker installed and running
2. `.env` file configured (optional, for environment variables)

### Build the Docker Image

From the project root:
```bash
cd backend
docker build -t marketing-agent-backend:latest .
```

Or from the project root in one command:
```bash
docker build -t marketing-agent-backend:latest ./backend
```

### Run the Container

**Basic run (port 8080):**
```bash
docker run -p 8080:8080 marketing-agent-backend:latest
```

**With volume mounts (for persistent storage):**
To persist your database and vector storage between container restarts:
```bash
docker run -p 8080:8080 \
  -v $(pwd)/storage:/app/storage \
  marketing-agent-backend:latest
```

**With environment variables from .env file:**
```bash
cd backend
docker run -p 8080:8080 \
  -v $(pwd)/storage:/app/storage \
  --env-file .env \
  marketing-agent-backend:latest
```

**With individual environment variables:**
```bash
docker run -p 8080:8080 \
  -v $(pwd)/storage:/app/storage \
  -e API_KEYS=your-api-key \
  -e OPENAI_API_KEY=your-openai-key \
  -e ALLOWED_ORIGINS=http://localhost:3000 \
  marketing-agent-backend:latest
```

**Run in detached mode (background):**
```bash
docker run -d \
  --name marketing-agent-backend \
  -p 8080:8080 \
  -v $(pwd)/storage:/app/storage \
  --env-file .env \
  marketing-agent-backend:latest
```

### Access the API

Once running, access:
- **Health Check:** `http://localhost:8080/api/v1/health`
- **API Documentation:** `http://localhost:8080/docs`
- **ReDoc:** `http://localhost:8080/redoc`

### Useful Docker Commands

**View logs:**
```bash
docker logs marketing-agent-backend
# Or follow logs in real-time
docker logs -f marketing-agent-backend
```

**Stop the container:**
```bash
docker stop marketing-agent-backend
```

**Remove the container:**
```bash
docker rm marketing-agent-backend
```

**Run a one-off command in the container:**
```bash
docker exec -it marketing-agent-backend /bin/bash
```

## Deployment Steps

### 1. Build and Push Docker Image

```bash
# Set your GCP project ID
export PROJECT_ID=your-project-id
export REGION=us-central1  # or your preferred region
export SERVICE_NAME=marketing-agent-backend

# Build the Docker image
docker build -t gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest ./backend

# Configure Docker to use gcloud as a credential helper
gcloud auth configure-docker

# Push the image to Google Container Registry
docker push gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest
```

### 2. Deploy to Cloud Run

**⚠️ IMPORTANT**: Never hardcode API keys in deployment commands or scripts that might be committed to Git. Use Secret Manager (recommended) or set environment variables interactively.

#### Option A: Using GCP Secret Manager (Recommended - See Security Best Practices section)

#### Option B: Setting environment variables directly (Not recommended for secrets)

```bash
# ⚠️ WARNING: This exposes secrets in your shell history
# Use Secret Manager instead for production
gcloud run deploy ${SERVICE_NAME} \
  --image gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --set-env-vars "API_KEYS=your-secret-api-key-1,your-secret-api-key-2" \
  --set-env-vars "DATABASE_URL=postgresql://user:password@host:5432/dbname" \
  --set-env-vars "OPENAI_API_KEY=your-openai-key" \
  --set-env-vars "ALLOWED_ORIGINS=https://your-frontend-domain.com" \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0
```

### 3. Environment Variables

Required and optional environment variables:

#### Required (for production):
- `API_KEYS`: Comma-separated list of API keys for authentication
- `DATABASE_URL`: PostgreSQL connection string (recommended for production)
- `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins

#### Optional (but recommended):
- `OPENAI_API_KEY`: OpenAI API key for LLM features
- `ANTHROPIC_API_KEY`: Anthropic API key (alternative to OpenAI)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `VECTOR_DB_PATH`: Path for vector database storage (default: `storage/vectors`)

### 4. Using Cloud Build (Alternative)

Create a `cloudbuild.yaml` file in the project root:

```yaml
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/marketing-agent-backend:$COMMIT_SHA', './backend']
  
  # Push the container image to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/marketing-agent-backend:$COMMIT_SHA']
  
  # Deploy container image to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'marketing-agent-backend'
      - '--image'
      - 'gcr.io/$PROJECT_ID/marketing-agent-backend:$COMMIT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'

images:
  - 'gcr.io/$PROJECT_ID/marketing-agent-backend:$COMMIT_SHA'
```

Then deploy:
```bash
gcloud builds submit --config cloudbuild.yaml
```

## API Authentication

Once deployed, all API endpoints (except `/api/v1/health`) require authentication via API key.

### Using X-API-Key Header:
```bash
curl -H "X-API-Key: your-api-key" \
  https://your-service-url.run.app/api/v1/analytics/kpis
```

### Using Authorization Bearer Token:
```bash
curl -H "Authorization: Bearer your-api-key" \
  https://your-service-url.run.app/api/v1/analytics/kpis
```

## Security Best Practices

1. **⚠️ NEVER Commit Secrets to Git**: 
   - All `.env` files are gitignored
   - Never commit API keys, passwords, or tokens
   - Review `git diff` before committing to ensure no secrets are included
   - Use `git-secrets` or similar tools to scan for accidental commits

2. **Use Secret Manager for API Keys**: Store sensitive credentials in Google Secret Manager instead of environment variables:
   ```bash
   # Create secret
   echo -n "your-api-key-1,your-api-key-2" | gcloud secrets create api-keys --data-file=-
   
   # Grant Cloud Run access
   gcloud secrets add-iam-policy-binding api-keys \
     --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"
   
   # Deploy with secret reference
   gcloud run deploy ${SERVICE_NAME} \
     --set-secrets="API_KEYS=api-keys:latest"
   ```

2. **Use Cloud SQL for Database**: For production, use Cloud SQL PostgreSQL instead of SQLite.

3. **Enable VPC Connector**: If accessing private resources, configure a VPC connector.

4. **Set Resource Limits**: Adjust memory and CPU based on your workload.

5. **Configure CORS Properly**: Set `ALLOWED_ORIGINS` to your actual frontend domain.

## Public Endpoints

The following endpoints are publicly accessible (no authentication required):
- `GET /api/v1/health` - Health check endpoint
- `GET /docs` - API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation
- `GET /openapi.json` - OpenAPI schema

All other endpoints require valid API key authentication.

## Monitoring and Logging

Cloud Run automatically provides:
- Request logs in Cloud Logging
- Metrics in Cloud Monitoring
- Error tracking and reporting

Access logs:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME}" --limit 50
```

