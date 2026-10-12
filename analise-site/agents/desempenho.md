# Agente: Desempenho

Segmento `desempenho` · prefixo `DES` · linhas 03.xx da matriz de referência

## Missão

Dizer se o site carrega rápido e estável, principalmente no celular, e quais mudanças trazem o maior ganho medido. Bases: cloudflare/web-perf, addyosmani/core-web-vitals e performance.

## Leia antes

`references/regras-comuns.md`

## Fontes na coleta (em ordem de confiança)

| Fonte | O que é |
|---|---|
| `coleta/psi/resumo-psi.json` | **PageSpeed medido pelo Google** (Lighthouse oficial, rodado nos servidores dele, sem influência de antivírus ou do computador de quem coletou). Traz notas, métricas de laboratório com rede 4G lenta, recomendações e, quando o site tem tráfego, **dados de campo** (usuários reais, 28 dias) no campo `campo`. `campo: null` significa que o site não tem tráfego suficiente, o que é normal. Os arquivos `web-<pagina>-<mobile|desktop>.txt` têm o relatório completo. **É a fonte principal** |
| `coleta/paginas/*/dados.json -> metricas_lab` | **Laboratório sem limitação de rede**, medido no navegador da coleta (LCP, CLS, TTFB). Sempre existe, mas é mais otimista que o PageSpeed. Use só como apoio ou se o PageSpeed falhar |
| `coleta/lighthouse/resumo-lighthouse.json` | **Lighthouse local** com limitação de rede/CPU. Só vale se `contaminado_por_antivirus` for nulo; se não for, ignore as notas e use o PageSpeed |
| `coleta/paginas/*/rede.json` e `resumo.json -> paginas[].por_tipo, recursos_pesados, terceiros` | Peso, tipos, cache, compressão |
| `coleta/paginas/*/dados.json` | imagens (dimensões, `loading`, `fetchpriority`, `srcset`), scripts no head, preloads, fontes |
| `resumo.json -> paginas[].metricas_lab` | Medição sem limitação, só referência |

Nunca misture campo e laboratório no mesmo número. Diga sempre de onde vem.

## Faixas

| Métrica | Bom | Precisa melhorar | Ruim |
|---|---|---|---|
| LCP | ≤ 2,5 s | 2,5 a 4 s | > 4 s |
| INP | ≤ 200 ms | 200 a 500 ms | > 500 ms |
| CLS | ≤ 0,1 | 0,1 a 0,25 | > 0,25 |
| TTFB | ≤ 0,8 s | 0,8 a 1,8 s | > 1,8 s |

## Checklist

| ID | Verificar | Como | Severidade típica |
|---|---|---|---|
| 03.01 | LCP, INP, CLS | Campo, se houver; senão PageSpeed (laboratório do Google); senão Lighthouse local não contaminado; senão `metricas_lab`. Ruim = alta; precisa melhorar = media | alta / media |
| 03.02 | Campo x laboratório | Registre em `extras.core_web_vitals` os dois, com a fonte | — |
| 03.03 | Lighthouse mobile e desktop | Nota de performance das páginas medidas | — (vira contexto) |
| 03.04 | TTFB e CDN | `server-response-time`; headers de CDN em `stack.json` | media |
| 03.05 | Bloqueio de renderização | Scripts no `<head>` sem `async`/`defer`, CSS grande; oportunidade `render-blocking-resources` | media |
| 03.06 | Imagens | Arquivos > 200 KB, formato JPG/PNG onde caberia WebP/AVIF, imagem exibida muito menor que a natural, imagem LCP com `loading="lazy"` ou sem prioridade | alta (hero > 1 MB) / media |
| 03.07 | Fontes | Mais de 4 arquivos de fonte, sem `font-display: swap`, fontes do Google sem preconnect | baixa / media |
| 03.08 | Peso total | Página > 3 MB no celular é media; > 6 MB é alta | media / alta |
| 03.09 | Terceiros | Quantos domínios e quanto pesam; chat, pixels e vídeos carregados antes da interação | media |
| 03.10 | Cache e compressão | Arquivos estáticos sem `cache-control` longo; HTML/JS/CSS sem `gzip`/`br` | media |
| 03.11 | CLS | Imagens sem `width`/`height`, banners que empurram conteúdo, troca de fonte | media |
| 03.12 | Interatividade | TBT alto e tarefas longas no Lighthouse (só isso, sem diagnóstico por fase) | media |
| 03.13 | Bundler (código) | Build de produção, minificação, polyfills, bibliotecas inteiras importadas (`lodash`, `moment`) | baixa / media |
| 03.14 | Dicas por framework | Se a stack for Next/Nuxt/Astro/WordPress, cite o recurso nativo (ex.: `next/image`, plugin de cache) | — |
| 03.17 | Quantificar | Toda recomendação traz ganho estimado em ms ou KB. Oportunidade com 0 ms não vira achado | — |

## Regras específicas

- Site já bom deve ouvir isso: "LCP de 1,2 s e CLS 0 no celular: excelente" vira ponto forte.
- Seja específico: "comprimir `hero.png` (1,4 MB) para WebP de ~180 KB: −1,1 MB por visita".
- Se não houve Lighthouse confiável nem `metricas_lab`, diga em `nao_verificado` e limite a nota a 70.
- **Ausência de dado de campo é esperada e não tira ponto.** Muitos sites não têm tráfego suficiente para o Google reunir dados de usuários reais. Não desconte nota, não limite a 70 e não gere achado. Diga uma vez no `resumo`, em linguagem simples, e registre em `cobertura.nao_verificado` só o INP, que não se mede em laboratório.
- **Se o PageSpeed do Google falhou** (`ferramentas.psi: false`), diga isso uma vez no `resumo` e use as demais fontes, sem descontar nota por isso.

## Extras para o relatório

```json
"extras": { "core_web_vitals": [{"metrica": "LCP", "campo_mobile": "2,9 s", "lab_mobile": "3,4 s", "faixa": "precisa melhorar"}],
            "lighthouse": {"home mobile": 62, "home desktop": 91} }
```
