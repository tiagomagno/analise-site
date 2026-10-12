# Agente: Arquitetura, Código e Infra

Segmento `arquitetura` · prefixo `ARQ` · linhas 10.xx da matriz de referência

## Missão

Avaliar a base técnica: domínio, certificado, e-mail do domínio, redirecionamentos, páginas de erro, links, organização das páginas e, havendo código, dependências e qualidade geral. Bases: samber/site-launch-checklist, resend/email-best-practices, trailofbits/supply-chain-risk-auditor, getsentry/code-review, marketingskills/site-architecture, wshobson/sql-optimization-patterns, web-quality-skills/best-practices.

## Leia antes

`references/regras-comuns.md`

## Fontes na coleta

| Arquivo | Para quê |
|---|---|
| `coleta/stack.json` | tecnologias, CMS, hospedagem |
| `coleta/http/redirects.json` | `http://`, `http://www.`, `https://`, `https://www.` e para onde cada um vai |
| `coleta/tls/tls.json` | certificado, validade, versão TLS. `valido: true` com `aviso` = a verificação local falhou mas o certificado está bom (não é achado). `valido: null` = inconclusivo (vai para `nao_verificado`, não é achado). Só `valido: false` indica problema real do certificado |
| `coleta/dns/dns.json` | A, MX, SPF, DMARC, DKIM, CAA, DNSSEC |
| `coleta/http/arquivos-padrao.json` | robots, favicon, manifest, teste de 404 |
| `coleta/links/links.json` | quebrados, cadeias de redirecionamento, sem resposta |
| `coleta/paginas/*/console.json` | erros de JavaScript |
| `coleta/paginas/*/dados.json -> links` (menu e rodapé) | estrutura de navegação |
| Código (se houver) | `package.json`/lockfile, `requirements.txt`, `go.mod`, estrutura de pastas, build |

## Checklist

| ID | Verificar | Como | Severidade típica |
|---|---|---|---|
| 10.01 | Stack e hospedagem | Registre em `extras.stack`. Versões antigas e sem suporte (ex.: PHP 7, WordPress muito desatualizado pela versão no `generator`) são achado | media / alta |
| 10.02 | Domínio canônico | As 4 variantes chegam à mesma URL final com **um** redirecionamento 301/308 | media |
| 10.03 | Certificado e HTTPS | Certificado inválido ou vencendo em menos de 15 dias; HTTP sem redirecionar; TLS < 1.2 | critica (inválido) / alta |
| 10.04 | E-mail do domínio | Se há MX: SPF presente e terminando em `~all`/`-all`; DMARC presente (`p=none` é fraco); DKIM em algum seletor comum. Sem SPF/DMARC, e-mails do cliente caem em spam e o domínio pode ser falsificado | alta / media |
| 10.05 | CAA e DNSSEC | Ausentes = baixa | baixa |
| 10.06 | Página 404 | `teste_404.status` deve ser 404 (soft 404 = 200 é media); página de erro própria com link para a home | media / baixa |
| 10.07 | Links e redirecionamentos | `quebrados` (internos = media; externos = baixa); cadeias com 2+ saltos. Itens em `sem_resposta` vão para `nao_verificado`, não são quebrados | media / baixa |
| 10.08 | Favicon e manifest | Favicon ausente; `apple-touch-icon` ausente | baixa |
| 10.09 | Erros no console | Erros de JS em `console.json`, principalmente se afetam formulário ou menu | media / baixa |
| 10.10 | Arquitetura de informação | Menu com rótulos claros; páginas importantes a até 3 cliques; URLs que refletem a hierarquia; rodapé com contato e políticas | media / baixa |
| 10.11 | Dependências (código) | Rode o auditor nativo se disponível (`npm audit --omit=dev`, `pip-audit`, `govulncheck`). Pacotes com vulnerabilidade alta/crítica, abandonados (sem release há 2+ anos), `postinstall` suspeito | alta / media |
| 10.12 | Código (visão geral) | Organização, tipagem, testes existentes, segredos fora do repositório, README de instalação. Só achados com impacto claro | baixa / media |
| 10.13 | Banco (código) | Consultas em laço (N+1), listagens sem paginação, falta de índice em campos de filtro. Só se houver acesso ao código e ao esquema | media |
| 10.14 | Build e ambiente | Modo de desenvolvimento em produção (`NODE_ENV`, `DEBUG`), source maps, variáveis de ambiente documentadas (`.env.example`) | media |

## Regras específicas

- Backups e restauração não são verificáveis de fora: pergunte no escopo e registre a resposta em `cobertura`.
- Links de redes sociais que bloqueiam robôs (Instagram, LinkedIn, Facebook) costumam aparecer em `sem_resposta` ou com 403/999: não reporte como quebrado.

## Extras para o relatório

```json
"extras": { "stack": {"tecnologias": [...], "hospedagem": "..."},
            "email_dominio": {"spf": "ok", "dmarc": "ausente", "dkim": "selector1 encontrado"},
            "certificado": {"emissor": "...", "dias_para_expirar": 63} }
```
