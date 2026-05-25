# TerraShield — one-command manual deploy to Cloud Run.
#
# Run from the repo root in PowerShell:
#     .\infra\deploy.ps1
# From CMD:
#     powershell -ExecutionPolicy Bypass -File infra\deploy.ps1
# Add -Groq to also enable the GeoCopilot LLM (requires the terrashield-llm-key secret):
#     .\infra\deploy.ps1 -Groq
#
# Assumes the one-time setup in DEPLOY.md is done (EE key secret, Artifact Registry
# repo, runtime-SA secret access) and that gcloud is on the `deploy` config
# (account B / terralens-496005).

param(
  [string]$RunProject = "terralens-496005",
  [string]$Region     = "asia-south1",
  [string]$EeProject  = "xward-481405",
  [switch]$Groq
)

$ErrorActionPreference = "Stop"
$AR = "$Region-docker.pkg.dev/$RunProject/terrashield"

function Assert-Ok($what) {
  if ($LASTEXITCODE -ne 0) { throw "$what failed (exit $LASTEXITCODE)" }
}

Write-Host "==> Building backend image..." -ForegroundColor Cyan
gcloud builds submit --config infra/cloudbuild.backend.yaml --substitutions="_IMAGE=$AR/backend" .
Assert-Ok "backend build"

# Set CORS here too (not only at the end) so a mid-run failure can't leave the
# backend with a blank allowed-origin -> "Backend offline".
$FrontendUrl0 = "https://terrashield-frontend-352605264721.asia-south1.run.app"
$envVars = "TERRASHIELD_ENV=production,TERRASHIELD_GEE_PROJECT=$EeProject,TERRASHIELD_GEE_SA_KEY=/secrets/ee-key.json,TERRASHIELD_CORS_ORIGINS=$FrontendUrl0"
$secrets = "/secrets/ee-key.json=terrashield-ee-key:latest"
if ($Groq) {
  $envVars += ",TERRASHIELD_LLM_PROVIDER=groq,TERRASHIELD_LLM_MODEL=llama-3.3-70b-versatile"
  $secrets += ",TERRASHIELD_LLM_API_KEY=terrashield-llm-key:latest"
}

Write-Host "==> Deploying backend..." -ForegroundColor Cyan
gcloud run deploy terrashield-backend --image "$AR/backend" --region $Region --allow-unauthenticated --port 8000 --min-instances 1 --memory 4Gi --cpu 2 --timeout 300 --update-secrets="$secrets" --set-env-vars="$envVars"
Assert-Ok "backend deploy"

$BackendUrl = (gcloud run services describe terrashield-backend --region $Region --format="value(status.url)")
Assert-Ok "read backend url"
Write-Host "Backend: $BackendUrl" -ForegroundColor Green

Write-Host "==> Building frontend image (baking backend URL)..." -ForegroundColor Cyan
gcloud builds submit --config infra/cloudbuild.frontend.yaml --substitutions="_IMAGE=$AR/frontend,_API_BASE=$BackendUrl/api/v1" .
Assert-Ok "frontend build"

Write-Host "==> Deploying frontend..." -ForegroundColor Cyan
gcloud run deploy terrashield-frontend --image "$AR/frontend" --region $Region --allow-unauthenticated --port 3000
Assert-Ok "frontend deploy"

$FrontendUrl = (gcloud run services describe terrashield-frontend --region $Region --format="value(status.url)")
Assert-Ok "read frontend url"

Write-Host "==> Wiring CORS (backend allows the frontend origin)..." -ForegroundColor Cyan
gcloud run services update terrashield-backend --region $Region --update-env-vars="TERRASHIELD_CORS_ORIGINS=$FrontendUrl"
Assert-Ok "cors update"

Write-Host ""
Write-Host "Deployed." -ForegroundColor Green
Write-Host "  App : $FrontendUrl" -ForegroundColor Green
Write-Host "  API : $BackendUrl" -ForegroundColor Green
Write-Host "  EE  : $BackendUrl/api/v1/earthdata/status  (expect mode=live)" -ForegroundColor Green
