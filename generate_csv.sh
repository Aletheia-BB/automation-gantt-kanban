#!/usr/bin/env bash
set -euo pipefail

# Carrega .env se existir
if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
fi

GITHUB_ORG="${GITHUB_ORG:-Aletheia-BB}"
OUTPUT="${INPUT_CSV:-gantt.csv}"

# ── Verificação do gh CLI ──────────────────────────────────────────────
if ! command -v gh &> /dev/null; then
  echo "❌ GitHub CLI (gh) não encontrado."
  echo ""
  echo "Instale em: https://cli.github.com/"
  echo "  macOS:   brew install gh"
  echo "  Ubuntu:  sudo apt install gh"
  echo "  Fedora:  sudo dnf install gh"
  exit 1
fi

# ── Verificação do jq ──────────────────────────────────────────────────
if ! command -v jq &> /dev/null; then
  echo "❌ jq não encontrado."
  echo "  macOS:   brew install jq"
  echo "  Ubuntu:  sudo apt install jq"
  echo "  Fedora:  sudo dnf install jq"
  exit 1
fi

# ── Verificação de autenticação ────────────────────────────────────────
if ! gh auth status &> /dev/null; then
  echo "❌ Você não está autenticado no gh CLI."
  echo "   Execute: gh auth login"
  exit 1
fi

echo "🔍 Buscando projetos da org: $GITHUB_ORG..."

PROJECTS=$(gh api graphql -f query="
  query {
    organization(login: \"$GITHUB_ORG\") {
      projectsV2(first: 20) {
        nodes { number title }
      }
    }
  }
" | jq -r '.data.organization.projectsV2.nodes[] | "\(.number)|\(.title)"')

if [ -z "$PROJECTS" ]; then
  echo "⚠️  Nenhum projeto encontrado. Verifique o escopo read:project"
  echo "   Execute: gh auth refresh -s read:project"
  exit 1
fi

echo '"project","id","title","status","start","end"' > "$OUTPUT"

while IFS='|' read -r NUMBER TITLE; do
  echo "  📋 Projeto $NUMBER: $TITLE"

  gh api graphql -f query="
    query {
      organization(login: \"$GITHUB_ORG\") {
        projectV2(number: $NUMBER) {
          items(first: 100) {
            nodes {
              content {
                ... on Issue { title number state }
              }
              startDate: fieldValueByName(name: \"Start date\") {
                ... on ProjectV2ItemFieldDateValue { date }
              }
              endDate: fieldValueByName(name: \"Target date\") {
                ... on ProjectV2ItemFieldDateValue { date }
              }
              status: fieldValueByName(name: \"Status\") {
                ... on ProjectV2ItemFieldSingleSelectValue { name }
              }
            }
          }
        }
      }
    }
  " | jq -r --arg proj "$TITLE" '
    .data.organization.projectV2.items.nodes[] |
    select(.content != null) |
    [
      $proj,
      (.content.number // "" | tostring),
      (.content.title // ""),
      (.status.name // ""),
      (.startDate.date // ""),
      (.endDate.date // "")
    ] | @csv
  ' >> "$OUTPUT"

done <<< "$PROJECTS"

echo ""
echo "✅ $OUTPUT gerado com sucesso!"
