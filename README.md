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
- "Quais clientes puxaram o crescimento em 2024-12?"
- "O crescimento veio mais de expansão ou de novos logos?"
- "Que sinais de risco aparecem antes das quedas de MRR?"
- "Qual segmento e canal mais ajudaram nos melhores meses?"

## Base de exemplo

O arquivo [data/sample.csv](C:/analytiq-ai/data/sample.csv) agora vem mais estruturado, com:

- métricas SaaS mensais
- drivers de retenção e expansão
- mix de enterprise, mid-market e SMB
- nomes de clientes legíveis
- contexto qualitativo por mês para o agente interpretar melhor

Veja também [data/README.md](C:/analytiq-ai/data/README.md).

## Rodar os testes

```bash
pytest tests/ -v
```
