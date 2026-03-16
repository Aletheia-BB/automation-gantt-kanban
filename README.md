# automation-gantt-kanban

Automação completa para exportar issues do **GitHub Projects (kanban)** da organização [Aletheia-BB](https://github.com/orgs/Aletheia-BB/projects) e gerar visualizações de **Gantt Chart** e **Kanban Board** em PNG.

---

## Estrutura do projeto

```
automation-gantt-kanban/
├── .env.example            # Template de variáveis
├── .gitignore
├── generate_csv.sh         # Exporta CSV via GitHub API (macOS/Linux)
├── generate_csv.bat        # Exporta CSV via GitHub API (Windows)
├── automation_script.py    # Gera Gantt e Kanban a partir do CSV
├── requirements.txt        # Dependências Python
├── gantt.csv               # CSV gerado (não versionar)
└── README.md
```

---

## Pré-requisitos

| Ferramenta | Instalação |
|---|---|
| [GitHub CLI](https://cli.github.com/) | `brew install gh` / `winget install GitHub.cli` |
| [jq](https://jqlang.github.io/jq/) | `brew install jq` / `winget install jqlang.jq` |
| Python 3.8+ | [python.org](https://www.python.org/) |

---

## Configuração

### 1. Copie o arquivo de variáveis

```bash
cp .env.example .env
```

### 2. Edite o `.env` com suas configurações

```env
GITHUB_ORG=Aletheia-BB
INPUT_CSV=gantt.csv
OUTPUT_CSV=gant.csv
GANTT_PNG=automation_gantt_chart.png
KANBAN_PNG=automation_kanban_board.png
```

### 3. Autentique no GitHub CLI com o escopo necessário

```bash
gh auth login
gh auth refresh -s read:project
```

### 4. Instale as dependências Python

```bash
pip install -r requirements.txt
```

---

## Como usar

### Passo 1 — Exportar o CSV do GitHub Projects

**macOS / Linux:**
```bash
chmod +x generate_csv.sh
./generate_csv.sh
```

**Windows:**
```bat
generate_csv.bat
```

O script:
- Verifica se `gh`, `jq` e autenticação estão disponíveis
- Carrega variáveis do `.env` automaticamente
- Busca **todos os projetos** da organização
- Exporta issues com `project`, `id`, `title`, `status`, `start` e `end`
- Salva em `gantt.csv` (ou o valor de `INPUT_CSV` no `.env`)

### Passo 2 — Gerar os gráficos

```bash
python automation_script.py
```

Saída gerada:
- `gant.csv` — CSV normalizado com status padronizados
- `automation_gantt_chart.png` — Gráfico de Gantt por data
- `automation_kanban_board.png` — Board Kanban por status

---

## Campos do GitHub Projects utilizados

| Campo no projeto | Nome exato na API |
|---|---|
| Data de início | `Start date` |
| Data de término | `Target date` |
| Status da issue | `Status` |

> Os campos `Start date` e `Target date` devem existir no seu projeto.  
> Para criá-los: **Project → + → Date field**.

---

## Cores do Gantt

| Status | Cor |
|---|---|
| Completed | 🟢 Verde `#4CAF50` |
| In Progress | 🟡 Âmbar `#FFC107` |
| To Do | 🔵 Azul `#03A9F4` |

---

## .gitignore recomendado

```
.env
gantt.csv
gant.csv
*.png
```
