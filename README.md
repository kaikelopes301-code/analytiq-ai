# AI Spreadsheet Chat

MVP de terminal que le um `csv` ou `xlsx`, identifica abas, colunas, formulas e estrutura basica em runtime, e responde perguntas sobre o arquivo com Gemini.

## Setup

```bash
pip install -r requirements.txt
```

Crie um `.env` com a sua chave:

```bash
GEMINI_API_KEY=sua_chave_aqui
```

## Uso

```bash
python main.py data/saas_b2b_brasil_
python main.py caminho/para/arquivo.xlsx
python main.py caminho/para/arquivo.xlsx --model gemini-2.5-flash
```

## O que este MVP faz

- le `csv` e `xlsx`
- lista abas em arquivos Excel
- detecta formulas em `xlsx`
- encontra colunas numericas, textuais, datas e colunas vazias
- monta um contexto automatico por aba
- responde perguntas sem schema hardcoded

## Comandos

- `/insights`: mostra o overview estrutural da planilha
- `/modelos`: lista os modelos Gemini disponiveis
- `/modelo <id>`: troca o modelo atual
- `/modelo auto`: escolhe o melhor fallback
- `/limpar`: limpa a tela
- `/sair`: encerra a sessao

## Perguntas de exemplo

- "Quais abas existem neste arquivo?"
- "Ha formulas? Em quais abas?"
- "Qual parece ser a aba principal?"
- "Quais colunas estao quase vazias?"
- "Quais IDs e colunas de data voce detectou?"
- "Resuma a estrutura da planilha"

## Testes

```bash
python -m pytest tests -q
```
