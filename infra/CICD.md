# CI/CD — push to `main` → Cloud Run (keyless)

[`.github/workflows/ci.yml`](../.github/workflows/ci.yml) runs tests on every push
and PR. On **push to `main`**, after tests pass, the `deploy` job builds and deploys
both services to Cloud Run using **Workload Identity Federation** — no service-account
key is ever stored in GitHub.

Flow per push to main: tests → build+deploy backend → read its URL → build frontend
with that URL baked in → deploy frontend → point backend CORS at the frontend.

---

## One-time setup

### 0. Put the repo on GitHub
```bash
# from the repo root
gh repo create <owner>/terrashield --private --source=. --remote=origin --push
# or manually:
#   git remote add origin git@github.com:<owner>/terrashield.git
#   git push -u origin main
```

### 1. Prerequisites that the workflow assumes already exist
These are the one-time, manual pieces from [`DEPLOY.md`](DEPLOY.md) (the CI does *not*
create them, by design — they hold secrets / cost money):

- Artifact Registry repo **`terrashield`** (DEPLOY.md §2)
- Secret **`terrashield-ee-key`** holding your EE service-account key (DEPLOY.md §1a + §2a)
- The Cloud Run **runtime** SA can read that secret:
  ```bash
  PN=$(gcloud projects describe $RUN_PROJECT --format='value(projectNumber)')
  gcloud secrets add-iam-policy-binding terrashield-ee-key \
    --member="serviceAccount:${PN}-compute@developer.gserviceaccount.com" \
    --role=roles/secretmanager.secretAccessor
  ```

### 2. Deployer service account (in the billing project B)
```bash
export RUN_PROJECT=<billing-project>
gcloud config set project $RUN_PROJECT
gcloud iam service-accounts create gh-deployer --display-name="GitHub Actions deployer"
SA=gh-deployer@$RUN_PROJECT.iam.gserviceaccount.com
for r in roles/run.admin \
         roles/cloudbuild.builds.editor \
         roles/artifactregistry.writer \
         roles/storage.admin \
         roles/iam.serviceAccountUser; do
  gcloud projects add-iam-policy-binding $RUN_PROJECT \
    --member="serviceAccount:$SA" --role="$r"
done
```
Why each: `run.admin` deploy; `cloudbuild.builds.editor` submit builds;
`artifactregistry.writer` push images; `storage.admin` Cloud Build's staging bucket;
`iam.serviceAccountUser` act as the Cloud Run runtime SA.

### 3. Workload Identity Federation (keyless trust GitHub → GCP)
```bash
PN=$(gcloud projects describe $RUN_PROJECT --format='value(projectNumber)')

gcloud iam workload-identity-pools create github \
  --location=global --display-name="GitHub"

gcloud iam workload-identity-pools providers create-oidc github \
  --location=global --workload-identity-pool=github --display-name="GitHub OIDC" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository=='<owner>/terrashield'"

# Let only this repo impersonate the deployer SA
gcloud iam service-accounts add-iam-policy-binding $SA \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/$PN/locations/global/workloadIdentityPools/github/attribute.repository/<owner>/terrashield"

# This is the value for the WIF_PROVIDER variable below:
echo "projects/$PN/locations/global/workloadIdentityPools/github/providers/github"
```

### 4. GitHub repo **Variables** (Settings → Secrets and variables → Actions → Variables)
No secrets needed — it's keyless.

| Variable | Value |
|----------|-------|
| `GCP_PROJECT` | your billing/hosting project id (B) |
| `GCP_REGION` | e.g. `asia-south1` |
| `GEE_PROJECT` | your Earth Engine project id (account A) |
| `WIF_PROVIDER` | the `projects/.../providers/github` string printed in step 3 |
| `DEPLOY_SA` | `gh-deployer@<billing-project>.iam.gserviceaccount.com` |

---

## Use it
```bash
git push origin main
```
Watch **Actions** → the `Deploy to Cloud Run` job. When green, the last log line prints
the frontend URL — that's the live app. Subsequent pushes to `main` redeploy automatically;
PRs only run tests.

## Notes
- GeoCopilot LLM is off by default in CI deploys (`provider=none`). To enable it, store a
  `terrashield-llm-key` secret (DEPLOY.md §2a) and add
  `--update-secrets=TERRASHIELD_LLM_API_KEY=terrashield-llm-key:latest` plus
  `TERRASHIELD_LLM_PROVIDER=groq` to the backend deploy step.
- First run must be on `main`. To test the pipeline from a branch, temporarily change the
  `if:` guard in the `deploy` job, then revert.
- The EE key lives only in Secret Manager (account B) and is mounted at runtime; CI never
  touches Earth Engine.
