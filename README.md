# AI Data Analysis Agent

Agente de IA que analisa dados CSV e responde perguntas em linguagem natural usando Gemini.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Adicione sua GEMINI_API_KEY no .env
```

Obtenha sua chave gratuita em: https://aistudio.google.com/app/apikey

## Uso

```bash
python main.py data/sample.csv
```

## Perguntas de exemplo

- "Teve queda de receita?"
- "Qual o maior valor de usuários?"
- "Tem algo estranho nos dados?"
- "Qual foi a tendência geral de conversões?"

## Rodar os testes

```bash
pytest tests/ -v
```

## Estrutura

```
analytiq-ai/
├── main.py           # Ponto de entrada — loop de perguntas
├── data_loader.py    # Carregamento e validação do CSV
├── analyzer.py       # Estatísticas, quedas, outliers, insights
├── ai_agent.py       # Integração com Gemini
├── utils.py          # Formatação no terminal
├── data/
│   └── sample.csv    # Dataset de exemplo
└── tests/
    ├── test_data_loader.py
    ├── test_analyzer.py
    ├── test_ai_agent.py
    └── test_utils.py
```
