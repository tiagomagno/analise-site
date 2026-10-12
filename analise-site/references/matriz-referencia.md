# Matriz de referência da skill `analise-site`

Data: 10/10/2026 (atualizada com SEO local, botões de contato, ortografia, reputação do domínio e concorrentes)

Para que serve: mostrar, segmento por segmento, **o que cada skill de referência verifica** e **o que a nossa skill vai verificar**. É a base de consulta para escrever os agentes agora e para comparar resultados depois. Quando um achado da nossa parecer raso, procure a linha aqui, veja qual referência cobre aquele ponto e abra o arquivo dela.

## Como ler

| Símbolo | Significado |
|---|---|
| ● | A referência cobre esse ponto |
| ✓ | A nossa inclui |
| ◐ | A nossa inclui de forma resumida ou só em certas condições (anotado ao lado) |
| ✗ | A nossa deixa de fora, de propósito (motivo ao lado) |
| → | A nossa cobre, mas em outro segmento |

Modo: **URL** = funciona só com o site no ar. **Código** = precisa do código-fonte. **Ambos** = usa os dois quando houver.

A pasta de cada referência está em `candidatas/`, `candidatas2/` ou nos zips originais. Os Prompts 1 e 2 são os de segurança que você enviou.

---

## 1. Segurança

Referências: **P1** Prompt 1 · **P2** Prompt 2 · **SEN** sentry-security-review · **ADY** addy-security-and-hardening · **TOB** tob-insecure-defaults · **LLM** owasp-llm-top10 · **WQB** wq-best-practices

| Ponto | P1 | P2 | SEN | ADY | TOB | LLM | WQB | Nossa | Modo |
|---|---|---|---|---|---|---|---|---|---|
| Detectar a stack e adaptar as checagens a ela | | ● | ● | | | | | ✓ | Ambos |
| Headers de segurança (CSP, HSTS, X-Frame, X-Content-Type, Referrer, Permissions) | ● | | | ● | | | ● | ✓ | URL |
| HTTPS obrigatório, cookies com HttpOnly/Secure/SameSite | ● | | | ● | | | ● | ✓ | URL |
| Arquivos expostos (.env, .git, backups, listagem de diretório) | ● | | | | | | | ✓ | URL |
| Source maps públicos em produção | | | | | | | ● | ✓ | URL |
| Chaves e segredos no bundle JS do navegador | ● | ● | ● | ● | | | | ✓ | URL |
| Segredos no código, configs, CI e histórico git | ● | ● | ● | ● | | | | ✓ | Código |
| Defaults inseguros: segredo com valor padrão, admin/admin, fail-open, debug ligado | | ◐ | | | ● | | | ✓ | Código |
| CORS com curinga / acesso permissivo | ● | | | ● | ● | | | ✓ | Ambos |
| Isolamento por dono/tenant (RLS, filtro por usuário) | ● | ● | ● | | | | | ✓ | Código |
| Permissão checada só no front | ● | ● | ● | | | | | ✓ | Código |
| IDOR (objeto acessado por ID sem checar dono) | ● | ● | ● | ● | | | | ✓ | Código |
| XSS (innerHTML, v-html, markdown sem sanitizar, `javascript:` em href) | ● | ● | ● | ● | | | ● | ✓ | Ambos |
| Injeção SQL/NoSQL/comando | ● | | ● | ● | | | | ✓ | Código |
| CSRF | ● | | ● | | | | | ◐ só SameSite e presença de token | Ambos |
| Uploads, path traversal, SSRF | ● | | ● | ● | | | | ◐ só se houver upload ou fetch no servidor | Código |
| Autenticação e sessão (expiração, onde guarda token, reset de senha, MFA) | ● | | ● | ● | | | | ◐ pontos principais: token em localStorage, expiração, rate limit no login | Ambos |
| Rate limiting e proteção contra abuso | ● | | | ● | | | | ✓ | Ambos |
| Webhooks sem verificação de assinatura | ● | | | | | | | ✓ | Código |
| Funcionalidades com IA: chave no front, prompt injection, teto de custo | ● | | | ● | | ● | | ✓ resumo | Ambos |
| OWASP LLM Top 10 completo | | | | | | ● | | ✗ profundo demais para o macro | |
| Senhas com hash forte (bcrypt/argon2) / criptografia fraca | ● | | ● | | ● | | | ◐ só hash de senha | Código |
| Logs sem dados sensíveis, monitoramento | ● | | ● | | | | | ◐ | Código |
| Dependências vulneráveis | | | ● | ● | | | ● | → Arquitetura | Código |
| Docker e infraestrutura como código | | | ● | | | | | ✗ fora do escopo macro | |
| Modelagem de ameaças (STRIDE) | | | | ● | | | | ✗ fora do escopo macro | |
| Só reportar o que é explorável; separar "precisa verificação" | ● | ● | ● | | ● | | | ✓ verificado / suspeita | |
| Registrar pontos fortes com evidência | | ● | | | | | | ✓ | |
| Gerar issues do GitHub e PDF | | ● | | | | | | ✓ no relatório comum | |

## 2. Privacidade e LGPD

Referências: **GDA** gdpr-audit · **WSG** wshobson-gdpr · **LCH** site-launch-checklist (fase legal) · **MKA** mk-analytics (seção privacidade) · **ADY** addy-security (dados pessoais) · **P1**

| Ponto | GDA | WSG | LCH | MKA | ADY | P1 | Nossa | Modo |
|---|---|---|---|---|---|---|---|---|
| Banner de consentimento que **bloqueia** scripts antes do aceite | ● | | ● | ● | | | ✓ comparar requisições antes e depois do aceite | URL |
| Inventário de cookies e serviços de terceiros | ● | | | | | | ✓ | URL |
| Política de privacidade e termos de uso publicados | ● | | ● | | | | ✓ | URL |
| Encarregado (DPO) identificado com contato | | | | | | | ✓ exigência própria da LGPD (art. 41) | URL |
| Formulários: coleta mínima e finalidade informada | ● | ● | | | ● | | ✓ | URL |
| Base legal por finalidade | ● | ● | | | | | ◐ só nos formulários visíveis | URL |
| Canal para direitos do titular (acesso, correção, exclusão) | ● | ● | | | ● | | ◐ verifica se o canal existe | URL |
| Retenção e exclusão de dados | ● | | | | ● | | ◐ só com código | Código |
| Dados pessoais em logs | ● | | | | ● | ● | ◐ | Código |
| Operadores e transferência internacional | ● | | | | | | ◐ lista terceiros e país de origem | URL |
| Dados de crianças e dados sensíveis | ● | | | | ● | | ◐ só sinaliza quando evidente | Ambos |
| Relatório de impacto (RIPD/DPIA) | ● | | | | | | ✗ exige processo interno | |
| Achado cita o artigo da lei, com nível de confiança e lacuna de evidência | ● | | | | | | ✓ artigos da LGPD | |

## 3. Desempenho

Referências: **WP** web-perf · **CWV** wq-core-web-vitals · **PERF** wq-performance · **LCH** site-launch-checklist (quality gates)

| Ponto | WP | CWV | PERF | LCH | Nossa | Modo |
|---|---|---|---|---|---|---|
| LCP, INP e CLS com faixas bom / precisa melhorar / ruim | ● | ● | ● | ● | ✓ | URL |
| Separar dado de campo (CrUX) de laboratório (Lighthouse) | | ● | ● | ● | ✓ CrUX quando houver | URL |
| Lighthouse mobile e desktop | | | | ● | ✓ | URL |
| Tempo de resposta do servidor (TTFB), CDN | | ● | ● | | ✓ | URL |
| Recursos que bloqueiam a renderização | ● | ● | ● | | ✓ | URL |
| Imagens: formato, tamanho, responsivas, prioridade da imagem LCP | | ● | ● | | ✓ | URL |
| Fontes: font-display, preload | | ● | ● | | ✓ | URL |
| Peso da página por tipo de recurso | ● | | ● | | ✓ | URL |
| Scripts de terceiros | | | ● | | ✓ | URL |
| Cache e compressão | ● | | ● | | ✓ | URL |
| Causas de CLS (espaço reservado, banners, troca de fonte) | ● | ● | | | ✓ | URL |
| Diagnóstico de INP por fase da interação | | ● | | | ◐ só tarefas longas do Lighthouse | URL |
| Bundler, tree-shaking, polyfills, código morto | ● | | | | ◐ só com código | Código |
| Dicas por framework (Next, Nuxt, Astro, React, Vue) | | ● | | | ◐ quando a stack for detectada | Ambos |
| Desempenho em execução (layout thrashing, listas longas) | | | ● | | ✗ fora do macro | |
| Monitoramento de usuário real (RUM) | | | ● | | ✗ só recomenda | |
| Quantificar ganho; ignorar o que tem 0 ms de impacto | ● | | | | ✓ | |

## 4. SEO e AEO

Referências: **MKS** mk-seo-audit · **WQS** wq-seo · **SAN** seo-aeo-best-practices · **AI** mk-ai-seo · **SCH** mk-schema · **PSEO** programmatic-seo · **LCH** site-launch-checklist

| Ponto | MKS | WQS | SAN | AI | SCH | PSEO | LCH | Nossa | Modo |
|---|---|---|---|---|---|---|---|---|---|
| robots.txt e sitemap XML | ● | ● | ● | | | | | ✓ | URL |
| Indexação: noindex, canonical, status HTTP | ● | ● | ● | | | | | ✓ | URL |
| Title e meta description | ● | ● | ● | | | | | ✓ | URL |
| Estrutura de headings (um H1, hierarquia) | ● | ● | | | | | | ✓ | URL |
| Imagens: alt e nome do arquivo | ● | ● | | | | | | ✓ | URL |
| Links internos e páginas órfãs | ● | ● | | | | ● | | ✓ | URL |
| URLs limpas | ● | ● | | | | ● | | ✓ | URL |
| Mobile | ● | ● | | | | | | → Design | |
| Core Web Vitals | ● | | ● | | | | | → Desempenho | |
| HTTPS | ● | ● | | | | | | → Segurança | |
| Dados estruturados (JSON-LD) e validação | | ● | ● | ● | ● | | | ✓ tipos principais | URL |
| Schema injetado por JS não aparece no HTML bruto | ● | | | | | | | ✓ comparar HTML bruto e renderizado | URL |
| Open Graph e cartões de redes sociais | | | ● | | | | ● | ✓ | URL |
| Hreflang e sites multilíngues | ● | ● | ● | | | | | ◐ só se multilíngue | URL |
| Sinais de E-E-A-T (autor, sobre, contato, fontes) | ● | | ● | ● | | | | ◐ sinais visíveis | URL |
| Crawlers de IA no robots.txt, llms.txt | | ● | ● | ● | | | ● | ✓ | URL |
| Conteúdo extraível por IA (resposta direta, listas, tabelas, FAQ) | | | ● | ● | | | | ✓ | URL |
| Visibilidade real nas respostas de ChatGPT, Perplexity etc. | | | | ● | | | | ✗ exige ferramenta de monitoramento | |
| Intenção de busca e palavras-chave | ● | | | | | | | ◐ sem dados de volume | URL |
| Problemas típicos por tipo de site | ● | | | | | | | ✓ via tipo de site | |
| SEO local: perfil no Google Meu Negócio localizado; nome, endereço e telefone iguais no site e no perfil | ● | | | | ● | | | ✓ busca pelo nome da empresa e cidade | URL |
| Oportunidade de páginas em escala | | | | | | ● | | ◐ seção "oportunidades" | |
| Texto com cara de IA | ● | | | | | | | → Copy | |

## 5. Acessibilidade

Referências: **A11** accessibility · **VWG** vercel-web-design-guidelines · **WDR** web-design-reviewer · **LCH** site-launch-checklist

| Ponto | A11 | VWG | WDR | LCH | Nossa | Modo |
|---|---|---|---|---|---|---|
| Automático (Lighthouse/axe) + verificação manual | ● | | | ● | ✓ | URL |
| Texto alternativo em imagens e ícones | ● | ● | ● | | ✓ | URL |
| Contraste de cores (4.5:1) | ● | | ● | ● | ✓ | URL |
| Navegação por teclado e ordem de foco | ● | ● | | ● | ✓ | URL |
| Foco visível e não encoberto (2.4.7, 2.4.11) | ● | ● | ● | ● | ✓ | URL |
| Skip link e landmarks | ● | | | | ✓ | URL |
| Tamanho de alvo de toque (2.5.8) | ● | ● | ● | | ✓ | URL |
| Idioma da página declarado | ● | | | | ✓ | URL |
| Rótulos e mensagens de erro em formulários | ● | ● | | | ✓ | URL |
| Movimento e prefers-reduced-motion | ● | ● | | | ✓ | URL |
| ARIA e live regions | ● | ● | | | ◐ uso incorreto evidente | Ambos |
| Legendas e transcrição de mídia | ● | | | | ◐ só se houver vídeo/áudio | URL |
| Autenticação acessível e entrada redundante (3.3.7, 3.3.8) | ● | | | | ◐ só se houver login/cadastro | URL |
| Movimentos de arrastar (2.5.7) | ● | | | | ✗ raro em sites institucionais | |
| Nota 100 no Lighthouse não é conformidade | ● | | | | ✓ regra do agente | |
| Severidade por impacto (crítico, sério, moderado) | ● | | ● | | ✓ mapeada para a nossa | |

## 6. Design e UI

Referências: **WDR** web-design-reviewer · **IMP** impeccable (reference/critique.md, audit.md, craft-floor.md) · **WDE** web-design-engineer (critique-guide + failure-patterns) · **STI** stitch-extract-design-md · **VWG** vercel-web-design-guidelines

| Ponto | WDR | IMP | WDE | STI | VWG | Nossa | Modo |
|---|---|---|---|---|---|---|---|
| Inspeção visual real com screenshots | ● | ● | | | | ✓ | URL |
| Responsivo por viewport (estouro, quebra de layout) | ● | ● | | | ● | ✓ 375 / 768 / 1440 | URL |
| Sobreposição, alinhamento, espaçamento | ● | | ● | | | ✓ | URL |
| Hierarquia visual (escala de tipos, para onde o olho vai) | | ● | ● | | | ✓ | URL |
| Consistência de fontes, cores e espaçamentos | ● | | ● | ● | | ✓ | URL |
| Inventário de tokens a partir do código | | | | ● | | ◐ só com código | Código |
| Tipografia (até 2 famílias, contraste de tamanhos) | | | ● | | ● | ✓ | URL |
| Design "genérico", que serviria para qualquer produto | | ● | ● | | | ✓ | URL |
| Padrões de site feito por IA (hero centrado padrão, cards em tudo, bento sem ritmo) | | ● | ● | | | ✓ | URL |
| Estados: hover, vazio, erro, carregando | | | ● | | ● | ◐ nos elementos visíveis | URL |
| Botões de contato visíveis em todas as páginas e no celular | | | | | | → Conversão e UX | |
| Tema claro/escuro | | ● | | | ● | ◐ só se o site tiver | URL |
| Carga cognitiva (decisões com mais de 4 opções) | | ● | | | | ◐ | URL |
| Heurísticas de Nielsen com nota | | ● | | | | → Conversão e UX | |
| Nota de saúde do design com faixas | | ● | ● | | | ✓ dentro da nota 0 a 100 | |
| "O que está funcionando" | | ● | ● | | | ✓ pontos fortes | |
| Corrigir no código e reverificar | ● | | | | | ✗ a análise é somente leitura | |

## 7. Copy e Conteúdo

Referências: **CE** copy-editing (Seven Sweeps) · **NAS** no-ai-slop · **UXC** design:ux-copy (instalada) · **BR** marketing:brand-review (instalada) · **VWG** vercel-web-design-guidelines (content & copy)

| Ponto | CE | NAS | UXC | BR | VWG | Nossa | Modo |
|---|---|---|---|---|---|---|---|
| Clareza | ● | ● | | | | ✓ | URL |
| Voz e tom consistentes | ● | | | ● | | ✓ | URL |
| "E daí?": benefício em vez de recurso | ● | | | | | ✓ | URL |
| Prova: números, depoimentos, casos | ● | | | ● | | ✓ | URL |
| Especificidade (nomes, números, mecanismo) | ● | ● | | | | ✓ | URL |
| Emoção | ● | | | | | ◐ | URL |
| Risco zero (objeções respondidas perto do CTA) | ● | | | | | → Conversão | |
| Padrões de texto gerado por IA, citando o trecho | ● | ● | | | | ✓ lista em pt-BR | URL |
| Palavras e frases vazias | ● | ● | | | | ✓ | URL |
| Ortografia e gramática em português | ● | | | | | ✓ nas páginas principais, para não alongar a análise | URL |
| Microcopy: botões, erros, estados vazios | | | ● | | ● | ✓ | URL |
| Alegações sem prova e riscos legais | | | | ● | | ✓ | URL |
| Conteúdo desatualizado (anos antigos, ofertas vencidas) | ● | | | | | ◐ | URL |
| Problemas comuns (parede de recursos, corporativês, CTA enterrado) | ● | | | | | ✓ | URL |
| Painel de especialistas com nota 1 a 10 | ● | | | | | ◐ vira a nota do segmento | |
| Reescrever preservando a voz do autor | ● | ● | | | | ✗ a análise sugere, não reescreve | |

## 8. Conversão e UX

Referências: **CRO** mk-cro · **LPA** autonnel landing-page-conversion-audit · **UXH** ux-heuristics · **SIG** mk-signup · **POP** mk-popups · **PSY** mk-marketing-psychology · **LP15** copy-lp-queiroz (15 blocos)

| Ponto | CRO | LPA | UXH | SIG | POP | PSY | LP15 | Nossa | Modo |
|---|---|---|---|---|---|---|---|---|---|
| Proposta de valor entendida em 5 segundos | ● | ● | | | | | ● | ✓ | URL |
| Headline | ● | | | | | | ● | ✓ | URL |
| CTA: um principal, texto, posição | ● | ● | | | | | ● | ✓ | URL |
| Oferta e CTA visíveis na primeira tela do celular | | ● | | | | | | ✓ | URL |
| Hierarquia e escaneabilidade | ● | | ● | | | | | ✓ | URL |
| Prova social e confiança perto do CTA | ● | ● | | | | | ● | ✓ | URL |
| Objeções respondidas e garantia | ● | ● | | | | | ● | ✓ | URL |
| Preço visível e oferta clara | | ● | | | | | ● | ✓ | URL |
| Fricção em formulários (campos, validação inline) | ● | ● | ● | ● | | | | ✓ | URL |
| Botões de contato funcionando: WhatsApp com número e mensagem certos, telefone clicável, formulário que envia | | | | | | | | ✓ checagem própria; envio real do formulário só com autorização do cliente | URL |
| Caminho depois do clique (página de obrigado, próximo passo) | | ● | | ● | | | | ◐ se o fluxo for acessível | URL |
| Coerência entre anúncio e página | | ● | | | | | | ◐ só se o anúncio for informado | URL |
| Pop-ups: gatilho, momento, facilidade de fechar | | | | | ● | | | ◐ se houver | URL |
| Heurísticas de Nielsen e Krug (trunk test) | | | ● | | | | | ✓ resumido | URL |
| Dark patterns | | | ● | | | | | ✓ | URL |
| Gatilhos psicológicos | | | | | | ● | ● | ◐ nas recomendações | |
| Ideias de teste A/B | ● | ● | | | | | | ✓ seção "testar" | |
| Checagens por tipo de página (home, preço, landing page) | ● | | | | | | | ✓ | URL |
| Estrutura completa de landing page de vendas | | | | | | | ● | ✓ só quando o tipo for landing page | URL |

## 9. Analytics e rastreamento

Referências: **MKA** mk-analytics · **LCH** site-launch-checklist · **LPA** autonnel (medição)

| Ponto | MKA | LCH | LPA | Nossa | Modo |
|---|---|---|---|---|---|
| Ferramenta instalada (GA4, Tag Manager, Meta Pixel, outras) | ● | ● | | ✓ | URL |
| Evento de conversão disparando | ● | | ● | ✓ via requisições de rede | URL |
| Tags duplicadas ou disparo duplo | ● | | | ✓ | URL |
| Search Console / Bing verificados | | ● | | ◐ meta de verificação no HTML | URL |
| UTMs e click ids preservados até a conversão | ● | | ● | ◐ | URL |
| Plano de mensuração e nomenclatura de eventos | ● | | | ✗ só recomenda | |
| Rastreamento só depois do consentimento | ● | ● | | → Privacidade | |

## 10. Arquitetura, Código e Infra

Referências: **LCH** site-launch-checklist · **RES** resend email-best-practices · **TSC** tob-supply-chain · **SCR** sentry-code-review · **MSA** mk-site-architecture · **SQL** sql-optimization · **WQB** wq-best-practices · **WP** web-perf

| Ponto | LCH | RES | TSC | SCR | MSA | SQL | WQB | WP | Nossa | Modo |
|---|---|---|---|---|---|---|---|---|---|---|
| Detecção de stack, CMS e hospedagem | | | | | | | | ● | ✓ | Ambos |
| www x domínio raiz com redirecionamento único | ● | | | | | | | | ✓ | URL |
| Certificado TLS e HTTP → HTTPS | ● | | | | | | ● | | ✓ | URL |
| SPF, DKIM, DMARC do domínio | ● | ● | | | | | | | ✓ | URL |
| CAA e DNSSEC | ● | | | | | | | | ◐ | URL |
| Páginas 404 e 500 próprias, com status correto | ● | | | | | | | | ✓ | URL |
| Redirecionamentos em cadeia e links quebrados | ● | | | | | | | | ✓ | URL |
| Favicons e manifest | ● | | | | | | | | ✓ | URL |
| Erros no console e APIs obsoletas | | | | | | | ● | | ✓ | URL |
| Arquitetura de informação (hierarquia, 3 cliques, menu, URLs) | | | | | ● | | | | ✓ | URL |
| Dependências vulneráveis, abandonadas, scripts de instalação | | | ● | | | | ● | | ✓ | Código |
| Qualidade e organização do código, testes | | | | ● | | | | | ◐ visão geral | Código |
| Consultas ao banco (N+1, índices) | | | | | | ● | | | ◐ só com acesso ao banco | Código |
| Build de produção e variáveis de ambiente | ● | | | | | | | ● | ◐ | Código |
| Backups e teste de restauração | ● | | | | | | | | ✗ pergunta na fase de escopo | |
| Reputação de envio, bounces, aquecimento de IP | | ● | | | | | | | ✗ fora do escopo de site | |

## 11. Negócio e Mercado

Referências: **BMC** business-model · **PMK** mk-product-marketing · **CPR** mk-competitor-profiling · **MCB** marketing:competitive-brief (instalada)

| Ponto | BMC | PMK | CPR | MCB | Nossa |
|---|---|---|---|---|---|
| Resumo do modelo de negócio | ● | | | | ✓ na fase 0, resumido |
| Público, dores e linguagem do cliente | | ● | | | ✓ contexto para os agentes |
| Posicionamento e diferenciais | | ● | ● | ● | ✓ |
| Identificar e citar até 5 concorrentes (sem analisar os sites deles) | | | ● | ● | ✓ |
| Dados de mercado e SEO de concorrentes | | | ● | | ✗ exige API paga |
| Reputação do domínio: marcado como perigoso pelo Google, presença em listas de spam | | | | | ✓ checagem própria |
| Tráfego estimado | | | | | ✗ sem fonte gratuita |

## 12. Orquestração e relatório

Referências: **WQA** wq-web-quality-audit · **SQS** squirrelscan · **P2** Prompt 2 · **SEN** sentry · **GDA** gdpr-audit · **IMP** impeccable · **LLM** owasp-llm-top10

| Ponto | WQA | SQS | P2 | SEN | GDA | IMP | LLM | Nossa |
|---|---|---|---|---|---|---|---|---|
| Coletar evidência antes de opinar | ● | ● | | ● | | | | ✓ fase de coleta |
| Níveis de profundidade (rápido / completo) | | ● | | | | | | ✓ modos rápida e completa |
| Severidade padronizada | ● | | ● | ● | ● | | ● | ✓ |
| Nota por categoria e geral | | ● | | | | ● | | ✓ |
| Evidência em cada achado | ● | | ● | ● | ● | | | ✓ |
| Separar confirmado, provável e lacuna de evidência | | | | ● | ● | | | ✓ |
| Pontos fortes | | | ● | | | ● | | ✓ |
| Roteiro por prazo (7, 30, 90 dias) | ● | | | | | | ● | ✓ P1, P2, P3 |
| Issues prontas para o GitHub | | | ● | | | | | ✓ |
| Reauditar depois das correções | ● | ● | | | | | | ◐ modo por segmento |
| Checklists por cadência (deploy, semanal, mensal) | ● | | | | | | | ✗ evolução futura |

---

## Resumo de cobertura

| Segmento | Pontos mapeados | ✓ | ◐ | ✗ | → |
|---|---|---|---|---|---|
| Segurança | 29 | 20 | 5 | 3 | 1 |
| Privacidade | 13 | 6 | 6 | 1 | 0 |
| Desempenho | 17 | 12 | 3 | 2 | 0 |
| SEO e AEO | 23 | 14 | 4 | 1 | 4 |
| Acessibilidade | 16 | 12 | 3 | 1 | 0 |
| Design e UI | 17 | 10 | 4 | 1 | 2 |
| Copy | 16 | 11 | 3 | 1 | 1 |
| Conversão e UX | 19 | 15 | 4 | 0 | 0 |
| Analytics | 7 | 3 | 2 | 1 | 1 |
| Arquitetura e Infra | 16 | 10 | 4 | 2 | 0 |
| Negócio | 7 | 5 | 0 | 2 | 0 |
| Orquestração | 11 | 9 | 1 | 1 | 0 |
| **Total** | **191** | **127** | **39** | **16** | **9** |
