# Agente: SEO e AEO

Segmento `seo` · prefixo `SEO` · linhas 04.xx da matriz de referência

## Missão

Dizer se o Google (e os assistentes de IA) conseguem encontrar, entender e mostrar bem o site, e o que mais aumenta a visibilidade. Inclui SEO local: perfil no Google Meu Negócio. Bases: marketingskills/seo-audit, ai-seo e schema, web-quality-skills/seo, sanity/seo-aeo-best-practices.

## Leia antes

`references/regras-comuns.md`

## Fontes na coleta

| Arquivo | Para quê |
|---|---|
| `coleta/http/robots.txt`, `sitemap-*.xml`, `urls-sitemap.json`, `arquivos-padrao.json`, `llms.txt` | rastreabilidade |
| `coleta/paginas/*/dados.json` | title, description, canonical, robots, headings, imagens, links, JSON-LD, Open Graph, hreflang, lang |
| `coleta/paginas/*/html-bruto.html` x `html-renderizado.html` | conteúdo e schema que só existem com JavaScript |
| `coleta/paginas/*/texto.md` | conteúdo, intenção, extraibilidade para IA |
| `coleta/links/links.json` | links internos quebrados e cadeias |
| `coleta/lighthouse/resumo-lighthouse.json -> falhas.seo` | auditorias de SEO que falharam |
| `escopo.json` | nome da empresa, cidade, tipo de site |

## Checklist

| ID | Verificar | Como | Severidade típica |
|---|---|---|---|
| 04.01 | robots.txt e sitemap | robots não bloqueia o site; sitemap existe, está no robots, URLs com status 200 | alta (bloqueio) / media |
| 04.02 | Indexação | `meta_robots` com `noindex` em página importante; canonical apontando para outra página ou para HTTP; página 404 devolvendo 200 (`arquivos-padrao.json -> teste_404`) | alta / media |
| 04.03 | Title e description | Ausente, duplicado entre páginas, title > 60 ou < 15 caracteres, description fora de 70 a 160. Proponha um texto melhor para as principais | media / baixa |
| 04.04 | Headings | Zero ou mais de um H1 visível; H1 genérico ("Bem-vindo") | baixa / media |
| 04.05 | Imagens | `tem_alt: false` em imagens de conteúdo; nomes como `IMG_1234.jpg` | baixa / media |
| 04.06 | Links internos | Páginas importantes só alcançáveis por formulário ou JS; páginas do sitemap sem nenhum link interno (órfãs); links internos quebrados | media |
| 04.07 | URLs | Parâmetros, maiúsculas, IDs sem palavra, `.php?id=` | baixa |
| 04.11 | Dados estruturados | JSON-LD válido (faz parse?) e coerente com o tipo: `Organization`/`LocalBusiness` na home, `Product`, `Article`, `FAQPage`, `BreadcrumbList`. Ausência em negócio local é media | media / baixa |
| 04.12 | Conteúdo só com JS | Compare bruto e renderizado: título, H1, texto principal ou JSON-LD ausentes no bruto | alta (conteúdo principal) / media |
| 04.13 | Open Graph | `og:title`, `og:description`, `og:image` (absoluta) e `twitter:card`. Faltando = compartilhamento feio no WhatsApp | media |
| 04.14 | Hreflang | Só se houver mais de um idioma | media |
| 04.15 | E-E-A-T | Página "sobre" com pessoas reais, endereço, CNPJ, autoria em artigos, depoimentos com nome | baixa / media |
| 04.16 | Robôs de IA | robots.txt bloqueia `GPTBot`, `ClaudeBot`, `PerplexityBot`, `Google-Extended`? É escolha do cliente: informe, não condene. `llms.txt` é opcional | info |
| 04.17 | Extraível por IA | Respostas diretas às perguntas do público, listas, tabelas, FAQ; serviços e preços em texto e não só em imagem | baixa / media |
| 04.19 | Intenção | O texto usa as palavras que o cliente usaria para buscar ("dentista em Manaus" e não só "soluções odontológicas") | media |
| 04.20 | Problemas típicos do tipo de site | E-commerce: produtos sem schema `Product`, filtros indexáveis. Local: falta de cidade/bairro no texto. Blog: sem data e autor | varia |
| 04.21 | Google Meu Negócio | Faça WebSearch por "<nome da empresa> <cidade>" e "<nome da empresa>" + Google Maps. Registre se o perfil aparece, e compare nome, endereço e telefone com os do site. Divergência é achado; perfil inexistente em negócio local é alta | alta / media |
| 04.22 | Páginas em escala | Se o negócio tem dados repetíveis (cidades atendidas, serviços x bairros, produtos), sugira como oportunidade | info |

## Regras específicas

- Escreva os textos sugeridos de title e description em português, com o serviço e a cidade quando for negócio local.
- Desempenho, mobile e HTTPS são de outros segmentos: cite em `segmentos_relacionados` se afetarem SEO.
- Texto com cara de IA vai para Copy.

## Extras para o relatório

```json
"extras": {
  "google_meu_negocio": {"encontrado": true, "nome_no_perfil": "...", "endereco_igual_ao_site": false, "telefone_igual_ao_site": true, "fonte": "busca realizada em <data>"},
  "titulos_sugeridos": [{"pagina": "/", "title": "...", "description": "..."}],
  "oportunidades": ["..."]
}
```
