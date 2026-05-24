# Deploying TerraShield AI

The platform is two containers — **backend** (FastAPI + geo-engine) and
**frontend** (Next.js). The only non-obvious part is Earth Engine auth when your
**GEE account ≠ your Google Cloud (billing) account**. Read §1 first.

---

## 1. The account split — how EE auth actually works

**Key idea: Earth Engine access lives in a *service-account key*, not in where you
host the container.** A service account (SA) is a robot identity with its own JSON
key. If that SA is authorized for Earth Engine, *any* server holding the key can
call EE — regardless of which Cloud/billing account runs the server.

So you bridge the two accounts like this:

```
  GEE side (account A)                 Billing side (account B)
  ───────────────────                  ────────────────────────
  Project registered for EE            Cloud Run / billing enabled
  (e.g. xward-481405)                  (e.g. your-gcloud-project)
        │                                       │
        │ create service account + key          │ run the container
        │ grant it EE access                     │ (hosting only)
        ▼                                       ▼
     key.json  ───────────────────────────►  backend reads key.json
                                              ee.Initialize(creds, project=A)
```

You do **not** need EE and Cloud Run in the same project. The container runs on
account B; it authenticates to EE in project A using the SA key.

### 1a. Create the EE service account (on the GEE/account-A project)

Using the Google account that owns the **EE-registered** project (e.g.
`xward-481405`):

```bash
export EE_PROJECT=xward-481405          # your EE-registered project
gcloud config set project $EE_PROJECT

gcloud iam service-accounts create terrashield-ee \
  --display-name="TerraShield Earth Engine"

# Roles needed to use Earth Engine from this project
gcloud projects add-iam-policy-binding $EE_PROJECT \
  --member="serviceAccount:terrashield-ee@${EE_PROJECT}.iam.gserviceaccount.com" \
  --role="roles/serviceusage.serviceUsageConsumer"
gcloud projects add-iam-policy-binding $EE_PROJECT \
  --member="serviceAccount:terrashield-ee@${EE_PROJECT}.iam.gserviceaccount.com" \
  --role="roles/earthengine.viewer"

# Download the key (keep it secret — never commit it)
gcloud iam service-accounts keys create ee-key.json \
  --iam-account="terrashield-ee@${EE_PROJECT}.iam.gserviceaccount.com"
```

Then **register the service account for Earth Engine** (one-time): make sure the
Earth Engine API is enabled on the project (`gcloud services enable
earthengine.googleapis.com`) and the project is registered at
<https://code.earthengine.google.com> (Cloud project registration). For legacy
setups you can also register the SA email at
<https://signup.earthengine.google.com/#!/service_accounts>.

> Sanity check the key locally before deploying:
> ```bash
> TERRASHIELD_GEE_PROJECT=$EE_PROJECT TERRASHIELD_GEE_SA_KEY=./ee-key.json \
>   python scripts/smoke_test.py     # should print source=live
> ```

---

## 2. Deploy to Cloud Run (on your billing account, account B)

```bash
export RUN_PROJECT=your-gcloud-project     # billing/hosting account
export REGION=asia-south1                  # Mumbai
gcloud config set project $RUN_PROJECT
gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
  secretmanager.googleapis.com cloudbuild.googleapis.com

# Create the Artifact Registry repo the images push to (one-time).
gcloud artifacts repositories create terrashield \
  --repository-format=docker --location=$REGION \
  --description="TerraShield container images"
```

### 2a. Store secrets (don't bake them into images)

```bash
# Earth Engine SA key (created in §1a)
gcloud secrets create terrashield-ee-key --data-file=ee-key.json
# Groq/Llama key (optional)
printf '%s' "gsk_your_groq_key" | gcloud secrets create terrashield-llm-key --data-file=-
```

### 2b. Backend

```bash
gcloud builds submit --config infra/cloudbuild.backend.yaml \
  --substitutions=_IMAGE=$REGION-docker.pkg.dev/$RUN_PROJECT/terrashield/backend .

gcloud run deploy terrashield-backend \
  --image $REGION-docker.pkg.dev/$RUN_PROJECT/terrashield/backend \
  --region $REGION --allow-unauthenticated --port 8000 \
  --min-instances 1 --memory 2Gi --cpu 1 --timeout 300 \
  --update-secrets=/secrets/ee-key.json=terrashield-ee-key:latest,TERRASHIELD_LLM_API_KEY=terrashield-llm-key:latest \
  --set-env-vars=TERRASHIELD_ENV=production,TERRASHIELD_GEE_PROJECT=xward-481405,TERRASHIELD_GEE_SA_KEY=/secrets/ee-key.json,TERRASHIELD_LLM_PROVIDER=groq,TERRASHIELD_LLM_MODEL=llama-3.3-70b-versatile
# note the printed backend URL → BACKEND_URL
```

> The image is built from `infra/backend.Dockerfile` via the Cloud Build config
> (`gcloud builds submit` has no `--file` flag). `--memory 2Gi` is sized for the ML
> extra (scikit-learn / shap / xgboost); drop to 1Gi if you build without `[ml]`.
> `--min-instances 1` avoids cold starts; `--timeout 300` gives heavy live EE + ML
> calls room. The SA key is mounted at `/secrets/ee-key.json` and read via
> `TERRASHIELD_GEE_SA_KEY`. Set `TERRASHIELD_GEE_PROJECT` to **your** EE project.

### 2c. Frontend

`NEXT_PUBLIC_API_BASE` is baked at **build time**, so pass the backend URL as a
build arg:

```bash
export BACKEND_URL=https://terrashield-backend-xxxx.a.run.app
gcloud builds submit --config infra/cloudbuild.frontend.yaml \
  --substitutions=_IMAGE=$REGION-docker.pkg.dev/$RUN_PROJECT/terrashield/frontend,_API_BASE=$BACKEND_URL/api/v1 .

gcloud run deploy terrashield-frontend \
  --image $REGION-docker.pkg.dev/$RUN_PROJECT/terrashield/frontend \
  --region $REGION --allow-unauthenticated --port 3000
# note the printed frontend URL → FRONTEND_URL
```

### 2d. Wire CORS (backend must allow the frontend origin)

```bash
gcloud run services update terrashield-backend --region $REGION \
  --update-env-vars=TERRASHIELD_CORS_ORIGINS=$FRONTEND_URL
```

Open `FRONTEND_URL` → the status badge should read **LIVE**.

---

## 3. Alternative: skip Cloud Run entirely

The SA-key bridge means you can host the container anywhere:

- **Railway / Render** — push the repo, set the same env vars, upload `ee-key.json`
  as a secret file (or paste its contents into `TERRASHIELD_GEE_SA_KEY_JSON` and
  write it to a file on boot). Easiest for a quick PM demo.
- **Frontend on Vercel** — deploy `frontend/` with `NEXT_PUBLIC_API_BASE` set to
  your backend URL; host only the backend on Cloud Run.

---

## 4. Checklist

- [ ] EE SA created on the EE-registered project + key downloaded
- [ ] Local `smoke_test.py` prints `source=live` with the key
- [ ] Secrets in Secret Manager (EE key, Groq key) — **never in git or images**
- [ ] Backend deployed (`min-instances 1`, key mounted, `TERRASHIELD_GEE_PROJECT` set)
- [ ] Frontend built with `NEXT_PUBLIC_API_BASE=$BACKEND_URL/api/v1`
- [ ] `TERRASHIELD_CORS_ORIGINS` = frontend URL
- [ ] Rotate any API key that was shared in plaintext
