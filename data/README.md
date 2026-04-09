# Sample Data Guide

`sample.csv` foi estruturado para o agente conseguir responder perguntas numericas e tambem interpretar contexto de negocio.

## O que existe na base

- Serie mensal de `2020-01` ate `2024-12`
- Metricas principais: `mrr`, `active_customers`, `churn_rate`, `nps`, `cac`, `ltv`, `ltv_cac_ratio`
- Metricas operacionais: `expansion_mrr`, `contraction_mrr`, `reactivation_mrr`, `gross_revenue_retention_pct`, `net_revenue_retention_pct`, `pipeline_coverage`, `win_rate_pct`, `support_sla_pct`, `onboarding_days`
- Mix de clientes: `enterprise_customers`, `mid_market_customers`, `smb_customers`
- Contexto qualitativo: `focus_segment`, `primary_channel`, `product_launch`, `top_new_logos`, `top_expansion_accounts`, `churned_accounts`, `customer_story`, `risk_signal`

## Como ler

- As colunas numericas sustentam comparacoes e tendencias.
- As colunas textuais explicam o que aconteceu em cada mes, quais clientes puxaram crescimento e onde esta o risco.
- Os nomes de clientes sao realistas e consistentes para perguntas sobre logos, expansao e churn.

## Perguntas sugeridas

- Quais clientes mais puxaram o crescimento no ultimo trimestre?
- O crescimento recente veio mais de novos logos ou expansao da base?
- Existe concentracao de receita em contas enterprise nos ultimos 12 meses?
- Quais sinais de risco apareceram antes das quedas de MRR?
- Em quais meses o time vendeu melhor e qual canal apareceu junto?
- O churn caiu junto com melhora de onboarding e SLA?
- Quais contas aparecem com mais recorrencia em expansao?
- O que mudou entre 2023-12 e 2024-12 em receita, retencao e perfil da carteira?
