#!/usr/bin/env bash
# =============================================================================
# Azure 인프라 초기 설정 스크립트
#
# 실행 전 필요:
#   az login
#   az account set --subscription <YOUR_SUBSCRIPTION_ID>
#
# 사용법:
#   bash deploy/azure-setup.sh
# =============================================================================
set -e

# ── 설정값 (필요에 따라 수정) ─────────────────────────────────────────────
RESOURCE_GROUP="humanness-evaluator-rg"
LOCATION="koreacentral"
REGISTRY_NAME="humannessevaluatoracr"   # 전역 고유 이름 (소문자, 숫자만)
CONTAINER_APP_ENV="humanness-env"
CONTAINER_APP_NAME="humanness-evaluator"
# ──────────────────────────────────────────────────────────────────────────

echo "================================================"
echo "  Humanness Evaluator — Azure 인프라 설정"
echo "================================================"

# 1. Resource Group
echo "[1/5] Resource Group 생성..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output none

# 2. Azure Container Registry
echo "[2/5] Container Registry 생성..."
az acr create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$REGISTRY_NAME" \
  --sku Basic \
  --admin-enabled true \
  --output none

# 3. Container Apps Environment
echo "[3/5] Container Apps Environment 생성..."
az containerapp env create \
  --name "$CONTAINER_APP_ENV" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --output none

# 4. Container App (placeholder — 실제 이미지는 CI/CD에서 배포)
echo "[4/5] Container App 초기 생성..."
az containerapp create \
  --name "$CONTAINER_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --environment "$CONTAINER_APP_ENV" \
  --image "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest" \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 1.0 \
  --memory 2.0Gi \
  --output none

# 5. GitHub Actions용 Service Principal 생성
echo "[5/5] GitHub Actions Service Principal 생성..."
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
SP_JSON=$(az ad sp create-for-rbac \
  --name "humanness-evaluator-deploy" \
  --role contributor \
  --scopes "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}" \
  --sdk-auth)

# 결과 출력
FQDN=$(az containerapp show \
  --name "$CONTAINER_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query properties.configuration.ingress.fqdn \
  --output tsv 2>/dev/null || echo "배포 후 확인")

echo ""
echo "================================================"
echo "  설정 완료!"
echo "================================================"
echo ""
echo "MCP Server URL (배포 후):"
echo "  https://${FQDN}/sse"
echo ""
echo "GitHub Secrets에 추가할 값들:"
echo "  AZURE_CREDENTIALS      = 아래 JSON 전체"
echo "  AZURE_REGISTRY_NAME    = ${REGISTRY_NAME}"
echo "  AZURE_RESOURCE_GROUP   = ${RESOURCE_GROUP}"
echo ""
echo "AZURE_CREDENTIALS 값:"
echo "$SP_JSON"
echo ""
echo "Claude Desktop 연결 설정 (~/Library/Application Support/Claude/claude_desktop_config.json):"
echo '{'
echo '  "mcpServers": {'
echo '    "humanness-evaluator": {'
echo "      \"url\": \"https://${FQDN}/sse\""
echo '    }'
echo '  }'
echo '}'
