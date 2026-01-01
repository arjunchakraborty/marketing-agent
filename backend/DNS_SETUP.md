# DNS URL Setup for Marketing Agent APIs

This guide explains how to get a DNS URL to connect to your Marketing Agent backend APIs deployed on Google Cloud Run.

## Option 1: Use Default Cloud Run URL (Easiest)

When you deploy to Cloud Run, Google automatically provides a URL in the format:
```
https://marketing-agent-backend-XXXXX-uc.a.run.app
```

### Get Your Service URL

1. **Check if already deployed:**
   ```bash
   gcloud run services list --region=us-central1
   ```

2. **Get the service URL:**
   ```bash
   gcloud run services describe marketing-agent-backend \
     --region=us-central1 \
     --format="value(status.url)"
   ```

3. **Test the API:**
   ```bash
   # Replace with your actual URL
   curl https://marketing-agent-backend-XXXXX-uc.a.run.app/api/v1/health
   ```

### API Endpoints

Once you have your URL, your API endpoints will be:
- **Health Check:** `https://YOUR-URL.run.app/api/v1/health`
- **Analytics:** `https://YOUR-URL.run.app/api/v1/analytics/*`
- **Ingestion:** `https://YOUR-URL.run.app/api/v1/ingestion/*`
- **Intelligence:** `https://YOUR-URL.run.app/api/v1/intelligence/*`
- **Products:** `https://YOUR-URL.run.app/api/v1/products/*`
- **Image Analysis:** `https://YOUR-URL.run.app/api/v1/image-analysis/*`
- **Experiments:** `https://YOUR-URL.run.app/api/v1/experiments/*`
- **Campaigns:** `https://YOUR-URL.run.app/api/v1/campaigns/*`
- **API Docs:** `https://YOUR-URL.run.app/docs`

## Option 2: Map a Custom Domain (Production)

If you want to use your own domain (e.g., `api.yourdomain.com`), follow these steps:

### Prerequisites

1. A domain registered with any DNS provider (Google Domains, Cloudflare, Route53, etc.)
2. Access to your domain's DNS settings

### Steps

1. **Verify domain ownership in Google Cloud:**
   ```bash
   # This will open a browser to verify domain ownership
   gcloud domains verify yourdomain.com
   ```

2. **Map your domain to Cloud Run:**
   ```bash
   gcloud run domain-mappings create \
     --service=marketing-agent-backend \
     --domain=api.yourdomain.com \
     --region=us-central1
   ```

3. **Get DNS records to add:**
   ```bash
   gcloud run domain-mappings describe api.yourdomain.com \
     --region=us-central1 \
     --format="value(status.resourceRecords)"
   ```

4. **Add DNS records to your domain provider:**
   - Go to your DNS provider's control panel
   - Add the CNAME or A records provided by the command above
   - Wait for DNS propagation (usually 5-60 minutes)

5. **Verify the mapping:**
   ```bash
   gcloud run domain-mappings describe api.yourdomain.com \
     --region=us-central1
   ```
   
   Look for `status.conditions` to show `Ready: True`

### Example DNS Records

You'll typically need to add a CNAME record:
```
Type: CNAME
Name: api
Value: ghs.googlehosted.com
```

Or A records if specified by Google Cloud.

## Option 3: Use Cloud Load Balancer (Advanced)

For production with SSL certificates and more control:

1. **Create a serverless NEG (Network Endpoint Group):**
   ```bash
   gcloud compute network-endpoint-groups create marketing-agent-neg \
     --region=us-central1 \
     --network-endpoint-type=serverless \
     --cloud-run-service=marketing-agent-backend
   ```

2. **Create a backend service:**
   ```bash
   gcloud compute backend-services create marketing-agent-backend-service \
     --global \
     --load-balancing-scheme=EXTERNAL
   ```

3. **Add the NEG to the backend service:**
   ```bash
   gcloud compute backend-services add-backend marketing-agent-backend-service \
     --global \
     --network-endpoint-group=marketing-agent-neg \
     --network-endpoint-group-region=us-central1
   ```

4. **Create URL map, target HTTPS proxy, and forwarding rule** (see [GCP Load Balancer docs](https://cloud.google.com/load-balancing/docs/https/setting-up-https-serverless))

## Quick Start: Deploy and Get URL

If you haven't deployed yet, here's the complete flow:

```bash
# 1. Set your project
export PROJECT_ID=your-project-id
export REGION=us-central1
export SERVICE_NAME=marketing-agent-backend

# 2. Build and deploy (using Cloud Build)
gcloud builds submit --config cloudbuild.yaml

# 3. Get your service URL
gcloud run services describe ${SERVICE_NAME} \
  --region=${REGION} \
  --format="value(status.url)"

# 4. Test it
curl $(gcloud run services describe ${SERVICE_NAME} \
  --region=${REGION} \
  --format="value(status.url)")/api/v1/health
```

## Environment Variables for Frontend

Once you have your API URL, update your frontend configuration:

**For Next.js (web/):**
```typescript
// In your API client or config
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 
  'https://marketing-agent-backend-XXXXX-uc.a.run.app';
```

**For local development:**
```bash
# In web/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Troubleshooting

### Service not found
- Make sure you've deployed the service first
- Check the service name matches: `marketing-agent-backend`
- Verify the region matches

### DNS not resolving
- Wait 5-60 minutes for DNS propagation
- Check DNS records are correct using `dig api.yourdomain.com`
- Verify domain ownership in Google Cloud Console

### CORS errors
- Update `ALLOWED_ORIGINS` environment variable in Cloud Run to include your frontend domain
- Make sure the frontend URL matches exactly (including protocol and port)

### Authentication errors
- Ensure `API_KEYS` environment variable is set in Cloud Run
- Use the `X-API-Key` header or `Authorization: Bearer` header in requests

## Security Notes

- The default `.run.app` URL uses HTTPS automatically
- Custom domains also get automatic SSL certificates from Google
- Always use HTTPS in production
- Never expose API keys in client-side code

