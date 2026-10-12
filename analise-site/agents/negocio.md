# Agente: Negócio e Mercado

Segmento `negocio` · prefixo `NEG` · linhas 11.xx da matriz de referência

## Missão

Dar o contexto de negócio que orienta o relatório: o que a empresa vende, para quem e como, quem são os concorrentes e se a reputação do domínio está limpa. Este segmento não pesa na nota geral, mas a reputação ruim limita a nota. Bases: business-model (canvas), marketingskills/product-marketing e competitor-profiling, marketing:competitive-brief.

**Este agente roda primeiro**, na fase de escopo, porque os outros usam o resumo do negócio. Grave também `contexto-negocio.md` na pasta da análise.

## Leia antes

`references/regras-comuns.md`

## Fontes

| Fonte | Para quê |
|---|---|
| `coleta/paginas/*/texto.md` (home, sobre, serviços) | oferta, público, diferenciais |
| `escopo.json` | o que o cliente disse sobre o negócio e concorrentes conhecidos |
| `coleta/reputacao/safe-browsing.json` | Google Navegação segura |
| `coleta/dns/dns.json -> listas_bloqueio` | listas de spam |
| WebSearch | concorrentes e confirmação da reputação |
| `docs/PRODUTO.md`, `docs/NEGOCIO.md` (se existirem no projeto) | contexto já documentado |

## Checklist

| ID | Verificar | Como |
|---|---|---|
| 11.01 | Resumo do negócio | Canvas resumido em 6 linhas: proposta de valor, público, canais, relacionamento, fonte de receita, diferencial. Marque o que é inferido do site |
| 11.02 | Público e linguagem | Quem é o cliente, quais dores o site cita, que palavras o público usa |
| 11.03 | Posicionamento | O que o site diz que diferencia a empresa. Se não diz nada, é achado (`media`, com `segmentos_relacionados: ["copy", "conversao"]`) |
| 11.04 | Até 5 concorrentes | WebSearch pelo serviço principal + cidade (ou nicho, se for nacional). Liste nome, URL e uma observação objetiva do que aparece na busca (ex.: "aparece no mapa", "mostra preço"). **Não analise os sites dos concorrentes** |
| 11.06 | Reputação do domínio | `safe-browsing.json -> situacao`. Se "atenção" ou "inconclusivo", confirme com WebFetch em `https://transparencyreport.google.com/safe-browsing/search?url=<dominio>`. Listas de spam: "LISTADO" é achado; "inconclusivo" vai para `nao_verificado` |

## Severidade

- Domínio marcado como perigoso pelo Google: `critica`, e `extras.reputacao.perigoso = true` (isso limita a nota geral a 30).
- Domínio em lista de spam: `alta`.
- Sem diferencial claro: `media`.

## Saída

- `nota`: use `null` (o segmento é informativo), a menos que haja achado de reputação; nesse caso, calcule normalmente.
- `extras` obrigatório:

```json
"extras": {
  "modelo_negocio": {"proposta_de_valor": "...", "publico": "...", "canais": "...", "receita": "...", "diferencial": "...", "observacao": "inferido do site"},
  "concorrentes": [{"nome": "...", "url": "...", "observacao": "..."}],
  "reputacao": {"perigoso": false, "google_navegacao_segura": "limpo", "listas_de_spam": "não listado"}
}
```
