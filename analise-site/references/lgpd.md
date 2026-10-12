# LGPD para análise de sites (referência rápida)

Apoio para o agente de Privacidade. Estrutura de achados inspirada em mastepanoski/gdpr-audit, com os artigos da Lei 13.709/2018 (LGPD).

**Aviso que vai no relatório:** a análise aponta indícios técnicos de não conformidade. Ela não substitui avaliação jurídica.

## Artigos mais citados em site

| Tema | Artigo | O que verificar no site |
|---|---|---|
| Princípios: finalidade, necessidade, transparência | art. 6º | Formulário pede só o necessário e diz para quê |
| Bases legais | art. 7º | Cada coleta tem uma base: consentimento, execução de contrato, legítimo interesse etc. |
| Consentimento livre, informado e destacado | art. 8º | Caixa não vem pré-marcada; aceite separado para marketing |
| Informação ao titular | art. 9º | Política de privacidade acessível, clara, com finalidade, compartilhamento e contato |
| Dados sensíveis | art. 11 | Saúde, religião, biometria, origem racial etc. exigem cuidado extra |
| Crianças e adolescentes | art. 14 | Consentimento de um dos pais quando o público é infantil |
| Direitos do titular | art. 18 | Canal para acesso, correção, exclusão, portabilidade |
| Transferência internacional | art. 33 | Ferramentas com servidor fora do Brasil (analytics, chat, CRM) mencionadas na política |
| Encarregado (DPO) | art. 41 | Nome e contato do encarregado divulgados, em geral na política |
| Segurança | art. 46 | HTTPS, proteção dos dados coletados (cruzar com Segurança) |
| Incidentes | art. 48 | Fora do escopo da análise de site |

## Cookies e rastreamento

A LGPD não tem regra específica de cookies, mas o Guia Orientativo de Cookies da ANPD (2022) entende que cookies não necessários (analytics, publicidade) dependem de consentimento ou de outra base legal bem justificada, e que o banner precisa:

- permitir recusar com a mesma facilidade de aceitar;
- não carregar cookies não necessários antes da escolha;
- separar categorias (necessários, analytics, marketing);
- dar acesso à política de cookies.

Na prática da análise: compare `coleta/privacidade/antes-consentimento.json` com `depois-consentimento.json`. Pixel de anúncio ou Google Analytics disparando antes do aceite é achado `alta`.

## Severidade sugerida

| Situação | Severidade |
|---|---|
| Formulário coleta dado sensível sem aviso, ou dados de crianças sem salvaguarda | critica |
| Rastreamento de marketing antes do consentimento | alta |
| Sem política de privacidade com formulário que coleta dados | alta |
| Política existe, mas sem encarregado, sem finalidade ou sem canal de direitos | media |
| Banner sem opção de recusar | media |
| Política genérica copiada de modelo, sem citar as ferramentas reais do site | baixa |
