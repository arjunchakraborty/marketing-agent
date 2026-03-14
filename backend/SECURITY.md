# Security Guidelines

## API Keys and Secrets Management

### ⚠️ CRITICAL: Never Commit Secrets to Version Control

This repository contains code that handles sensitive API keys and credentials. Follow these guidelines strictly:

### ✅ DO:

1. **Use `.env` files for local development**:
   - Copy `.env.example` to `.env`
   - Fill in your actual values
   - `.env` files are gitignored and will NOT be committed

2. **Use GCP Secret Manager for production**:
   - Store all API keys and secrets in Google Secret Manager
   - Reference secrets in Cloud Run using `--set-secrets`
   - See `DEPLOYMENT.md` for instructions

3. **Use environment variables in CI/CD**:
   - Configure secrets as environment variables in your CI/CD platform
   - Never hardcode secrets in build scripts or configuration files

4. **Review changes before committing**:
   - Always run `git diff` before committing
   - Verify no `.env` files or hardcoded secrets are included
   - Consider using `git-secrets` or similar tools

### ❌ DON'T:

1. **Never commit `.env` files** - They are gitignored, but always verify
2. **Never hardcode API keys in code** - Use environment variables or Secret Manager
3. **Never commit secrets in deployment scripts** - Use Secret Manager or interactive prompts
4. **Never share API keys in documentation** - Use placeholders like `your-api-key-here`
5. **Never log API keys** - Be careful with logging that might expose secrets

### Checking for Accidental Commits

If you accidentally commit a secret:

1. **Immediately rotate/revoke the exposed secret**
2. **Remove it from git history** (if repository is private):
   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch backend/.env" \
     --prune-empty --tag-name-filter cat -- --all
   ```
3. **Force push** (only if you're sure, and coordinate with team)
4. **If repository is public**: Consider the secret compromised and rotate immediately

### Pre-commit Checks

Consider installing `git-secrets` to prevent accidental commits:

```bash
# Install git-secrets (macOS)
brew install git-secrets

# Configure for this repository
cd /path/to/marketing-agent
git secrets --install
git secrets --register-aws  # If using AWS secrets
```

### Environment Variables Reference

Sensitive variables that should NEVER be committed:
- `API_KEYS` - Authentication keys for API access
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key
- `DATABASE_URL` - Database connection strings with passwords
- Any variable containing passwords, tokens, or keys

Non-sensitive variables (can be in example files):
- `LOG_LEVEL` - Logging configuration
- `DEFAULT_LLM_PROVIDER` - Feature flags
- `VECTOR_DB_PATH` - Local paths (not containing secrets)

