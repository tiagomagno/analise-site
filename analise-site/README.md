# analise-site

Skill do Claude para analisar um site por completo e gerar um relatório para o cliente: nota geral, problemas priorizados, o que está bom e o que não pôde ser verificado.

A análise é **somente leitura e passiva**: não altera o site nem o código, não envia formulários (a menos que o dono autorize) e não faz teste de ataque.

## Como funciona

```
Escopo  ->  Coleta  ->  Negócio  ->  10 agentes em paralelo  ->  Verificador  ->  Consolidação  ->  Relatório
```

1. **Escopo.** Lê o que o projeto já documenta e pergunta só o que falta: URL, código (se houver), tipo de site, objetivo, cidade, concorrentes, se pode enviar o formulário de teste. Grava `escopo.json`.
2. **Coleta única.** Um script (`scripts/coleta.py`) visita o site uma vez e guarda tudo em `coleta/`. Todos os agentes leem os mesmos dados, então os números não divergem entre segmentos.
3. **Negócio primeiro.** Resume o que a empresa vende, para quem e como, e confere a reputação do domínio. Os outros agentes usam esse resumo.
4. **Agentes de segmento, em paralelo.** Cada um segue a checklist do seu arquivo em `agents/` e grava um JSON no formato de `schemas/achados.schema.json`.
5. **Verificador independente.** Um agente que não viu o raciocínio dos outros refaz a evidência dos achados críticos e altos e de uma amostra dos médios. Pode confirmar, rebaixar ou descartar.
6. **Consolidação** (`scripts/consolidar.py`). Valida os JSONs, aplica a verificação, junta repetições, recalcula as notas, aplica pesos por tipo de site e tetos, e define a prioridade (P1, P2, P3).
7. **Relatório** (`scripts/relatorio.py`). Gera `relatorio.html` (autossuficiente, com as capturas de tela e as issues do GitHub dentro; botão "Baixar PDF") e `relatorio.pdf`.
8. **Entrega e limpeza** (`scripts/finalizar.py`). Copia só o relatório para a pasta de destino e apaga os arquivos de trabalho.

## Modos

| Modo | Quando | Páginas | Agentes |
|---|---|---|---|
| `completa` (padrão) | Projeto de cliente | até 10 | todos + verificador |
| `rapida` | Pré-venda, primeira impressão | só a home | sem subagentes; segurança passiva, desempenho, SEO, acessibilidade, copy e conversão de forma resumida |
| `segmento` | Reauditoria após correções ou pedido de um segmento | conforme o pedido | só os segmentos pedidos |

## O que você recebe

Só duas coisas, numa pasta com o nome do site e a data (por exemplo `analise-exemplo.com.br-2026-10-12/`):

- **`relatorio.html`**: o relatório completo, num único arquivo (as capturas de tela e as issues para o GitHub ficam dentro dele). Tem botão "Baixar PDF".
- **`relatorio.pdf`**: o mesmo relatório em A4, para enviar ao cliente.

Durante a análise a skill trabalha numa pasta temporária (coleta do site, resultados de cada agente, rascunhos em JSON). Esses arquivos só servem para montar o relatório e **são apagados no fim**. Se você quiser guardá-los (para refazer o relatório, comparar com uma reauditoria ou conferir a evidência bruta), peça "manter os dados da análise". Para receber também as issues como arquivos separados, peça "gerar as issues em arquivos".

**Antivírus:** se o seu antivírus atrapalhar alguma medição (alguns injetam scripts nas páginas abertas por navegadores automatizados), a skill avisa no fim. A skill nunca mexe no antivírus: se quiser, pause-o por conta própria e peça uma nova análise daquele segmento.

## O que a coleta reúne

| Fonte | O que traz |
|---|---|
| Navegador (Playwright) | texto, HTML bruto e renderizado, capturas em desktop, tablet e celular, primeira tela do celular, medidas de layout, console, todas as requisições com tamanho e cache |
| HTTP | redirecionamentos, headers de segurança, `robots.txt`, `sitemap.xml`, `llms.txt`, arquivos sensíveis comuns (`.env`, `.git`, backups) |
| DNS e e-mail | registros, SPF, DKIM, DMARC, CAA, DNSSEC, listas de spam |
| TLS | emissor, validade, versão |
| Privacidade | o que carrega **antes** e **depois** de clicar em "Aceitar" no banner de cookies, cookies criados, terceiros contatados |
| JavaScript público | procura segredos (chaves de nuvem, pagamento, IA) e source maps abertos |
| Links | internos e externos quebrados, botões de WhatsApp, telefone e e-mail |
| axe-core | violações de acessibilidade por página |
| Lighthouse | notas e métricas mobile e desktop (precisa de Node/npx) |
| PageSpeed do Google | notas oficiais, métricas com 4G lento, recomendações e dados de usuários reais quando houver (veja "Desempenho: PageSpeed sem chave") |
| Reputação | Google Navegação segura |

## O que cada segmento analisa

Cada segmento começa com nota 100 e desconta por achado confirmado (crítica 25, alta 12, média 5, baixa 2; suspeita desconta metade). Todo achado tem evidência (URL, arquivo e linha, trecho, métrica ou captura), severidade, impacto no usuário e no negócio, recomendação específica e esforço (P = horas, M = dias, G = semanas).

### Segurança
Falhas reais e exploráveis, no site no ar e, havendo código, na aplicação.
- **Métodos:** análise dos headers (CSP, HSTS, X-Frame-Options e outros), HTTPS e atributos de cookies, arquivos expostos, source maps, segredos no JavaScript público, CORS, sinais de XSS e CSRF. Com código: busca de segredos e defaults inseguros, isolamento por dono, permissão só no front, IDOR, injeção, upload e SSRF, sessão, senhas, webhooks, logs.
- **Limite:** teste passivo; não faz força bruta, injeção nem carga em produção.

### Privacidade e LGPD
Indícios técnicos de não conformidade, com o artigo da lei em cada achado.
- **Métodos:** comparação entre o que carrega antes e depois do consentimento, inventário de terceiros e países de destino, leitura da política de privacidade (finalidade, direitos, encarregado, retenção, transferência internacional), coleta mínima nos formulários, dados sensíveis e de crianças. Com código, também retenção e dados pessoais em log.
- **Limite:** aponta indícios técnicos, não dá parecer jurídico.

### Desempenho
Se o site carrega rápido e estável, principalmente no celular.
- **Métodos:** Lighthouse mobile e desktop, Core Web Vitals (LCP, INP, CLS) em laboratório e, quando houver, dados de campo, TTFB e CDN, bloqueio de renderização, imagens, fontes, peso total, terceiros, cache e compressão. Cada ganho é quantificado (ms ou KB).
- **Aviso automático:** se scripts de antivírus aparecerem na medição, a coleta marca `contaminado_por_antivirus` e as notas mobile não devem ser usadas.

### SEO e AEO
Se o Google e os assistentes de IA conseguem encontrar, entender e mostrar o site.
- **Métodos:** `robots.txt` e sitemap, indexação e canonical, title e description, headings, imagens, links internos, URLs, dados estruturados, conteúdo que só aparece com JavaScript, Open Graph, hreflang, sinais de E-E-A-T, regras para robôs de IA, se o texto é fácil de ser citado por IA, intenção de busca, problemas típicos do tipo de site e Google Meu Negócio (SEO local).

### Acessibilidade
Se pessoas com deficiência conseguem usar o site (WCAG 2.2 AA).
- **Métodos:** axe-core automático somado a revisão manual de texto alternativo, contraste, teclado, foco visível, skip link e landmarks, tamanho do alvo de toque, idioma, formulários, movimento, ARIA, mídia e login.
- **Limite:** o automático cobre só parte dos problemas; leitor de tela real e zoom de 200% precisam de teste humano.

### Design e UI
O olhar de um diretor de arte.
- **Métodos:** inspeção das capturas em três larguras, responsividade, alinhamento e espaçamento, hierarquia, consistência, tipografia, tokens (no código), design genérico ou feito por modelo, estados (hover, foco, erro), tema escuro e carga cognitiva. Aponta também os pontos fortes.

### Copy e Conteúdo
Se o texto é claro, específico, convincente e correto.
- **Métodos:** leitura em passes (clareza, voz e tom, "e daí?", prova, especificidade, emoção), detecção de frases genéricas e de padrões de texto de IA (`references/texto-ia-ptbr.md`), ortografia, microcopy, alegações arriscadas, conteúdo desatualizado e números que não batem entre páginas.
- **Limite:** aponta e sugere; não reescreve o site.

### Conversão e UX
Onde o site perde contatos e vendas, ordenado pelo impacto esperado.
- **Métodos:** botões de contato funcionando (WhatsApp, telefone, e-mail), proposta de valor em 5 segundos, headline e CTA, primeira tela do celular, prova e confiança perto do CTA, objeções e garantia, oferta e preço, fricção do formulário, o que acontece depois do clique, coerência entre anúncio e página, pop-ups, heurísticas de usabilidade, dark patterns e sugestões de teste A/B.
- **Limite:** o envio real do formulário só é testado com autorização explícita.

### Analytics
Se o cliente consegue medir o que o site gera.
- **Métodos:** ferramentas instaladas e configuradas, eventos de conversão (contato, WhatsApp, compra), eventos duplicados, verificação no Search Console e Bing, captura de UTMs e identificadores de clique.
- **Limite:** sem acesso ao painel, não confirma que os dados chegam.

### Arquitetura, Código e Infra
A base técnica.
- **Métodos:** stack e hospedagem, domínio canônico e `www`, certificado, SPF, DKIM e DMARC, CAA e DNSSEC, página 404, links e redirecionamentos, favicon e manifest, erros de console, arquitetura de informação. Com código: dependências (`npm audit`), visão geral do código, banco, build e ambiente.

### Negócio e Mercado
O contexto que orienta o relatório.
- **Métodos:** resumo do modelo de negócio (proposta de valor, público, canais, receita, diferencial), linguagem do público, posicionamento, até 5 concorrentes por busca na web e reputação do domínio (Google Navegação segura e listas de spam). Não pesa na nota, mas um domínio marcado como perigoso limita a nota geral a 30.

## Verificação independente

O verificador não lê o raciocínio dos agentes. Ele refaz a evidência de **todos** os achados críticos e altos e de até 5 médios, e responde com um de três resultados:
- **confirmado:** a evidência confere e a severidade está adequada.
- **rebaixado:** o problema é real, mas a severidade estava exagerada.
- **descartado:** a evidência não confere (falso positivo).

Rebaixados e descartados são aplicados na consolidação e recalculam a nota do segmento.

## Nota geral e prioridade

- **Média ponderada** das notas dos segmentos, com pesos por tipo de site em `config/pesos.json` (institucional, landing page, e-commerce, SaaS/sistema, blog/portal).
- **Tetos:** achado crítico confirmado em Segurança ou Privacidade limita a nota a 50; domínio perigoso, a 30.
- **Faixas:** 90 ou mais Excelente, 75 a 89 Bom, 50 a 74 Precisa melhorar, abaixo de 50 Crítico.
- **Prioridade:** P1 (crítico, ou alto com esforço P ou M), P2 (alto, ou médio com esforço P ou M), P3 (o resto).
- Se mais da metade da checklist de um segmento ficou sem verificar, a nota dele é limitada a 70 e isso aparece no resumo.

## Junção de achados repetidos

O mesmo problema costuma aparecer em segmentos diferentes (por exemplo, um link quebrado em SEO e em Arquitetura). A consolidação resolve em três camadas:

1. **Regra exata:** mesma checagem e mesmo trecho de evidência são juntados.
2. **Similaridade de texto:** compara títulos, impacto, recomendação e evidência dando mais peso às palavras raras no conjunto. A partir de 0,35 de pontuação, e sem severidades muito distantes, junta sozinho. Cada junção aparece no terminal e em `consolidado.json`.
3. **Candidatos para conferir:** pares entre 0,10 e 0,40 vão para `duplicados-candidatos.json` (até 15). Quem orquestra confere o par e grava os confirmados em `duplicados.json`.

Validações: nenhum achado pode sumir, grupos com ID inexistente ou de um só segmento são ignorados com aviso, e com menos de 12 achados a similaridade fica desligada. Os limites foram calibrados contra pares reais confirmados à mão em duas análises: os pares mais claros são juntados sozinhos (nenhum falso positivo automático nos dados de teste), e os demais pares verdadeiros aparecem entre os primeiros candidatos, ao lado de alguns falsos, por isso a conferência final é humana.

## O que precisa estar instalado

| Item | Para quê | Obrigatório? |
|---|---|---|
| **Python 3.9 ou mais novo** | roda os scripts da coleta, da consolidação e do relatório | sim |
| **Pacote `playwright` e o navegador Chromium dele** (uns 150 MB, baixados uma vez) | visita o site, tira capturas de tela, abre o PageSpeed do Google e gera o PDF | sim |
| **Pacote `jsonschema`** | confere se o que os agentes gravaram está no formato certo | recomendado |
| **Node.js 18 ou mais novo** | roda o Lighthouse local e o axe-core (acessibilidade automática) | recomendado |
| **Internet** | visitar o site analisado e consultar o PageSpeed do Google | sim |

Sem o Node.js a análise funciona, só ficam de fora o Lighthouse local e o axe-core; o PageSpeed do Google e as demais análises continuam.

### Conferir e instalar automaticamente

```bash
python scripts/preparar.py              # só confere e diz o que falta
python scripts/preparar.py --instalar   # instala os pacotes Python e o Chromium que faltarem
```

O script instala sozinho apenas os pacotes Python e o Chromium do Playwright. O **Python** e o **Node.js** são programas do sistema: o script não os instala por você, mas mostra o comando (por exemplo `winget install OpenJS.NodeJS.LTS` no Windows) ou o endereço de download. No Windows, o `python` do PATH pode ser só o atalho da Microsoft Store; se a mensagem for "Python não foi encontrado", instale o Python em https://python.org.

### Instalar a skill

Copie esta pasta para a pasta de skills do Claude Code:

- Global (todos os projetos): `~/.claude/skills/analise-site/` (no Windows: `%USERPROFILE%\.claude\skills\analise-site\`)
- Só em um projeto: `<projeto>/.claude/skills/analise-site/`

## Uso

No Claude Code, peça normalmente: "analisa o site https://exemplo.com.br", "faz uma análise rápida desse site para pré-venda", "reaudita só segurança e SEO".

Os scripts também rodam sozinhos:

```bash
python scripts/coleta.py https://exemplo.com.br --saida ./analise --modo completa
python scripts/consolidar.py --saida ./analise
python scripts/relatorio.py --saida ./analise
python scripts/finalizar.py --trabalho ./analise --destino ./entrega   # fica só o relatório
```

Opções úteis da coleta: `--max-paginas N`, `--paginas-extra URL ...`, `--espera-abertura N` (segundos de espera para telas de abertura, padrão 3), `--sem-lighthouse`, `--sem-psi`, `--sem-axe`, `--sem-dns`, `--sem-reputacao`.

## Desempenho: PageSpeed sem chave

A coleta abre o site **pagespeed.web.dev** num navegador automatizado, digita o endereço e lê o resultado, como uma pessoa faria. O teste roda nos servidores do Google, então:
- não precisa de chave nem de conta;
- não sofre interferência de antivírus nem da máquina de quem rodou;
- traz as notas oficiais (Desempenho, Acessibilidade, Boas práticas e SEO), as métricas com rede 4G lenta, as recomendações do Google e, quando o site tem tráfego suficiente, os **dados de campo** (usuários reais dos últimos 28 dias).

São medidos a home em celular e computador e, no modo completa, mais duas páginas no celular. Cada medição leva de 20 a 60 segundos.

Se o site do PageSpeed estiver indisponível ou limitar o uso (as chamadas dele também têm limite), a análise continua com as medições de laboratório do navegador e o Lighthouse local, e o relatório avisa em uma linha. A nota de desempenho não é reduzida por isso.

Para uso profissional intenso, com muitas análises por dia, dá para definir uma chave gratuita do Google (API "PageSpeed Insights"), e a coleta passa a usar a API oficial:

```bash
export PSI_API_KEY="sua-chave"        # PowerShell: $env:PSI_API_KEY = "sua-chave"
```

**Antivírus:** a skill não altera configurações do antivírus nem cria exceções, e não deve. Alguns antivírus injetam scripts nas páginas abertas em navegadores automatizados e distorcem o Lighthouse local; a coleta detecta isso (`contaminado_por_antivirus`) e o relatório usa o PageSpeed do Google no lugar.

## Estrutura

```
analise-site/
├── SKILL.md                     orquestrador (fases, modos, regras)
├── agents/                      um arquivo por segmento + verificador.md
├── references/
│   ├── regras-comuns.md         evidência, severidade, nota, formato
│   ├── padroes-seguranca.md     padrões de busca no código e no JS público
│   ├── lgpd.md                  artigos e severidade
│   ├── texto-ia-ptbr.md         padrões de texto genérico em português
│   └── matriz-referencia.md     o que cada fonte de referência verifica e o que esta skill cobre
├── schemas/achados.schema.json  contrato de saída dos agentes
├── config/pesos.json            pesos por tipo de site, tetos e faixas
├── scripts/                     preparar.py, coleta.py, consolidar.py, relatorio.py, finalizar.py
├── templates/relatorio.css      visual do relatório
└── evals/                       site de teste com falhas plantadas + gabarito
```

## Personalizar

- **Pesos por tipo de site:** `config/pesos.json`.
- **Visual do relatório:** `templates/relatorio.css` (cores, fontes, logo).
- **Uma checagem nova:** acrescente a linha na matriz (`references/matriz-referencia.md`) e depois no arquivo do agente do segmento, com o mesmo ID.

## Testar a skill

```bash
python evals/montar-site-teste.py ./site-teste
cd site-teste && python -m http.server 8765 --bind 127.0.0.1
```

Em outra janela, peça ao Claude: "analisa o site http://127.0.0.1:8765/ (é o site de teste da skill, tipo institucional, sem código)". Compare o resultado com `evals/gabarito.md`.

## Limites conhecidos

- A coleta precisa de acesso à internet a partir da máquina onde roda.
- Sites que bloqueiam robôs (Cloudflare com desafio) podem devolver páginas de bloqueio; a coleta registra e a análise fica parcial.
- Antivírus que injeta scripts no navegador falseia o Lighthouse mobile; a coleta avisa, mas a medição limpa exige pausá-lo ou usar outra máquina.
- A amostra é de até 10 páginas. Em sites com muitas páginas do mesmo tipo (cases, produtos), o relatório deve dizer isso e a coleta aceita `--paginas-extra`.
- Se o banner de cookies não for detectado (`banner_detectado: false`), não se conclui que ele não existe; confira no código.
- **Certificado:** só é dado como inválido se o certificado entregue pelo servidor estiver mesmo fora da validade ou com nome errado, ou se o navegador também o recusar. Quando a verificação do Python do computador falha mas o navegador confia (comum com antivírus que inspeciona HTTPS), o relatório não trata como problema do site.
- Dados de campo (usuários reais) só existem para sites com tráfego suficiente.
- O site do PageSpeed também limita uso muito intenso; nesse caso a coleta segue sem ele.
- Listas de spam por DNS público às vezes recusam a consulta; o resultado fica "inconclusivo".
- Tráfego estimado e dados de SEO de concorrentes estão fora (exigem serviços pagos).
- Aponta indícios técnicos de LGPD e de segurança; não substitui parecer jurídico nem teste de invasão.
