#!/usr/bin/env bash
# ==============================================================================
# Helper Script: Convert Backend & Frontend into Git Submodules
# Usage: ./scripts/setup-submodules.sh <GITHUB_USERNAME>
# ==============================================================================

set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <YOUR_GITHUB_USERNAME>"
    echo "Example: $0 kunalarya"
    exit 1
fi

GITHUB_USER="$1"
BACKEND_REPO="https://github.com/${GITHUB_USER}/student-resource-backend.git"
FRONTEND_REPO="https://github.com/${GITHUB_USER}/student-resource-frontend.git"

echo "=============================================================================="
echo "🔀 Submodule Setup for GitHub User: ${GITHUB_USER}"
echo "Backend Target:  ${BACKEND_REPO}"
echo "Frontend Target: ${FRONTEND_REPO}"
echo "=============================================================================="

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

# Step 1: Backup local environment files if present
echo "===> [1/4] Backing up local .env files..."
BACKUP_DIR=$(mktemp -d)
[ -f backend/.env ] && cp backend/.env "${BACKUP_DIR}/backend.env" || true
[ -f frontend/.env ] && cp frontend/.env "${BACKUP_DIR}/frontend.env" || true

# Step 2: Remove cached folders from git index and disk
echo "===> [2/4] Removing folders from current git index and filesystem..."
git rm -r --cached backend 2>/dev/null || true
git rm -r --cached frontend 2>/dev/null || true
rm -rf backend frontend

# Step 3: Add submodules
echo "===> [3/4] Adding submodules..."
git submodule add "${BACKEND_REPO}" backend
git submodule add "${FRONTEND_REPO}" frontend

# Step 4: Initialize, update and restore .env files
echo "===> [4/4] Initializing submodules and restoring local environment files..."
git submodule update --init --recursive
[ -f "${BACKUP_DIR}/backend.env" ] && cp "${BACKUP_DIR}/backend.env" backend/.env || true
[ -f "${BACKUP_DIR}/frontend.env" ] && cp "${BACKUP_DIR}/frontend.env" frontend/.env || true
rm -rf "${BACKUP_DIR}"

echo "=============================================================================="
echo "✅ Submodules successfully linked!"
echo "Now run:"
echo "  git commit -m 'chore: configure backend and frontend as git submodules'"
echo "  git push origin main"
echo "=============================================================================="
