@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul

echo.
echo =======================================
echo   GitHub Gantt CSV Exporter
echo =======================================
echo.

:: ── Carrega .env se existir ────────────────────────────────────────────
if exist ".env" (
  for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    set "line=%%A"
    if not "!line:~0,1!"=="#" (
      set "%%A=%%B"
    )
  )
)

if not defined GITHUB_ORG set GITHUB_ORG=Aletheia-BB
if not defined INPUT_CSV   set INPUT_CSV=gantt.csv

:: ── Verificação do gh CLI ──────────────────────────────────────────────
where gh >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] GitHub CLI ^(gh^) nao encontrado.
    echo Baixe em: https://cli.github.com/
    echo   winget install --id GitHub.cli
    pause & exit /b 1
)

:: ── Verificação do jq ──────────────────────────────────────────────────
where jq >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] jq nao encontrado.
    echo   winget install jqlang.jq
    pause & exit /b 1
)

:: ── Verificação de autenticação ────────────────────────────────────────
gh auth status >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Nao autenticado. Execute: gh auth login
    pause & exit /b 1
)

echo Buscando projetos da org: %GITHUB_ORG%...
echo.

gh api graphql -f query="query { organization(login: \"%GITHUB_ORG%\") { projectsV2(first: 20) { nodes { number title } } } }" ^
  | jq -r ".data.organization.projectsV2.nodes[] | \"\(.number)|\(.title)\"" > "%TEMP%\gh_projects.txt"

if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Falha ao buscar projetos. Verifique o escopo read:project:
    echo   gh auth refresh -s read:project
    pause & exit /b 1
)

echo "project","id","title","status","start","end" > "%INPUT_CSV%"

for /f "tokens=1,* delims=|" %%A in (%TEMP%\gh_projects.txt) do (
    echo   Projeto %%A: %%B
    gh api graphql -f query="query { organization(login: \"%GITHUB_ORG%\") { projectV2(number: %%A) { items(first: 100) { nodes { content { ... on Issue { title number state } } startDate: fieldValueByName(name: \"Start date\") { ... on ProjectV2ItemFieldDateValue { date } } endDate: fieldValueByName(name: \"Target date\") { ... on ProjectV2ItemFieldDateValue { date } } status: fieldValueByName(name: \"Status\") { ... on ProjectV2ItemFieldSingleSelectValue { name } } } } } } }" ^
      | jq -r --arg proj "%%B" ".data.organization.projectV2.items.nodes[] | select(.content != null) | [$proj, (.content.number // \"\" | tostring), (.content.title // \"\"), (.status.name // \"\"), (.startDate.date // \"\"), (.endDate.date // \"\")] | @csv" >> "%INPUT_CSV%"
)

del "%TEMP%\gh_projects.txt" >nul 2>&1
echo.
echo [OK] %INPUT_CSV% gerado com sucesso!
echo.
pause
