# Agente: Analytics e rastreamento

Segmento `analytics` · prefixo `ANA` · linhas 09.xx da matriz de referência

## Missão

Dizer se o cliente consegue medir o que o site gera: visitas, origem e, principalmente, conversões (contato, WhatsApp, compra). Base: marketingskills/analytics e site-launch-checklist (fase de analytics).

## Leia antes

`references/regras-comuns.md`

## Fontes na coleta

| Arquivo | Para quê |
|---|---|
| `coleta/analytics/analytics.json` | por página: GA4 (IDs e eventos disparados), GTM, Meta Pixel (IDs e eventos), outros |
| `coleta/privacidade/consentimento.json -> depois.analytics_novos` | o que só dispara depois do aceite de cookies |
| `coleta/paginas/*/dados.json -> verificacoes`, `coleta/dns/dns.json -> TXT_verificacoes` | verificação do Search Console, Bing, Meta |
| `coleta/paginas/*/rede.json` | requisições de rastreamento |

## Checklist

| ID | Verificar | Como | Severidade típica |
|---|---|---|---|
| 09.01 | Ferramenta instalada | Existe GA4 (ou outra ferramenta de analytics) em todas as páginas da amostra? Nenhuma ferramenta = alta | alta / media |
| 09.02 | Evento de conversão | Os cliques em WhatsApp, telefone e envio de formulário geram evento? Pela coleta só dá para ver eventos de carga; procure no GTM/código (`gtag('event'`, `dataLayer.push`, `fbq('track'`) | alta (se não houver nada) |
| 09.03 | Duplicidade | Mais de um `page_view` por carga para o mesmo ID, ou GA4 instalado direto e via GTM ao mesmo tempo | media |
| 09.04 | Search Console e Bing | Meta tag ou TXT de verificação presente. Não encontrar não prova ausência (pode ser verificado por outro método): registre como observação | info / baixa |
| 09.05 | UTMs e click ids | Links internos que removem parâmetros de campanha; redirecionamentos que perdem `gclid`/`fbclid` | baixa |

## Regras específicas

- Rastreamento disparando antes do consentimento é achado de **Privacidade**. Aqui cite em `segmentos_relacionados`.
- Ferramentas bloqueadas pela rede durante a coleta aparecem como requisição sem resposta; isso não significa que não funcionam para o visitante.
- A recomendação deve dizer **o que medir**: "evento `clique_whatsapp` com parâmetro de página" e não "configurar eventos".

## Extras para o relatório

```json
"extras": { "ferramentas": [{"nome": "GA4", "id": "G-XXXX", "paginas": "5 de 5"}], "eventos_encontrados": ["page_view"] }
```
