# Script PowerShell pour construire et pousser les images vers AWS ECR
# Charger les variables .env
if (Test-Path ".\.env") {
    Get-Content ".\.env" | ForEach-Object {
        if ($_ -match "^([^#=]+)=(.*)$") {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
}

# Configuration
$AWS_ACCOUNT_ID = $env:AWS_ACCOUNT_ID
$AWS_REGION = $env:AWS_REGION -eq "" ? "eu-west-1" : $env:AWS_REGION
$IMAGE_TAG = $env:IMAGE_TAG -eq "" ? "latest" : $env:IMAGE_TAG
$BACKEND_REPO = $env:BACKEND_REPO -eq "" ? "eduscore-backend" : $env:BACKEND_REPO
$FRONTEND_REPO = $env:FRONTEND_REPO -eq "" ? "eduscore-frontend" : $env:FRONTEND_REPO
$VITE_API_URL = $env:VITE_API_URL -eq "" ? "/api" : $env:VITE_API_URL
$VITE_GOOGLE_CLIENT_ID = $env:VITE_GOOGLE_CLIENT_ID

# Validation
if (-not $AWS_ACCOUNT_ID) {
    Write-Error "AWS_ACCOUNT_ID n'est pas défini. Vérifiez votre .env"
    exit 1
}

$REGISTRY = "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

Write-Host "ECR Registry: $REGISTRY" -ForegroundColor Green
Write-Host "Backend Repo: $BACKEND_REPO" -ForegroundColor Green
Write-Host "Frontend Repo: $FRONTEND_REPO" -ForegroundColor Green
Write-Host "Image Tag: $IMAGE_TAG" -ForegroundColor Green

# Construire les images
Write-Host "`nConstruction backend..." -ForegroundColor Cyan
docker build -t "$REGISTRY/$($BACKEND_REPO):$IMAGE_TAG" backend
if ($LASTEXITCODE -ne 0) {
    Write-Error "Erreur build backend"
    exit 1
}

Write-Host "`nConstruction frontend..." -ForegroundColor Cyan
docker build --build-arg "VITE_API_URL=$VITE_API_URL" `
             --build-arg "VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID" `
             -t "$REGISTRY/$($FRONTEND_REPO):$IMAGE_TAG" `
             frontend
if ($LASTEXITCODE -ne 0) {
    Write-Error "Erreur build frontend"
    exit 1
}

# Authentification ECR et push
Write-Host "`nAuthentification ECR..." -ForegroundColor Cyan
$loginCmd = aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $REGISTRY
if ($LASTEXITCODE -ne 0) {
    Write-Error "Erreur authentification ECR. Vérifiez vos credentials AWS."
    exit 1
}

Write-Host "`nPoussage backend..." -ForegroundColor Cyan
docker push "$REGISTRY/$($BACKEND_REPO):$IMAGE_TAG"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Erreur push backend"
    exit 1
}

Write-Host "`nPoussage frontend..." -ForegroundColor Cyan
docker push "$REGISTRY/$($FRONTEND_REPO):$IMAGE_TAG"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Erreur push frontend"
    exit 1
}

Write-Host "`n✅ Images ECR poussées avec succès :" -ForegroundColor Green
Write-Host "- $REGISTRY/$($BACKEND_REPO):$IMAGE_TAG" -ForegroundColor Green
Write-Host "- $REGISTRY/$($FRONTEND_REPO):$IMAGE_TAG" -ForegroundColor Green
