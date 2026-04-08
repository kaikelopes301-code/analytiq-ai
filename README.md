# AI Data Analysis Agent

Agente de análise de dados em terminal com interface de chat, painel visual sob demanda e seleção dinâmica de modelos Gemini.

## Setup

```bash
pip install -r requirements.txt
```

Crie um `.env` com a sua chave:

```bash
GEMINI_API_KEY=sua_chave_aqui
```

Obtenha sua chave em [Google AI Studio](https://aistudio.google.com/app/apikey).

## Uso

```bash
python main.py data/sample.csv
python main.py data/sample.csv --model gemini-2.5-flash
```

Ao iniciar, o app abre em uma tela clean e centralizada. O painel visual só aparece quando você pede por insights ou faz perguntas ligadas a métricas.

## Comandos no chat

- `/insights`: abre o painel visual com cards, tendências e highlights.
- `/modelos`: lista os modelos Gemini disponíveis para a sua chave.
- `/modelo <id>`: troca o modelo atual sem reiniciar.
- `/modelo auto`: escolhe o melhor fallback disponível.
- `/limpar`: limpa a tela e volta para a tela inicial.
- `/sair`: encerra a sessão.

## Perguntas de exemplo

- "Me dá um insight visual do negócio"
- "Como estão churn, MRR e clientes?"
- "Qual foi a tendência dos últimos 6 meses?"
- "Tem algum risco na retenção?"

## Rodar os testes

```bash
pytest tests/ -v
```
