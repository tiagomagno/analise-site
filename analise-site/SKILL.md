---
name: analise-site
description: Analisa um site por completo (segurança, LGPD, desempenho, SEO e AEO, acessibilidade, design, copy, conversão, analytics, arquitetura e infra, negócio e concorrentes) com um agente por segmento, e entrega relatório HTML com gráficos, PDF e issues para o GitHub. Use quando o usuário pedir análise, auditoria, diagnóstico ou revisão de um site ou landing page, "o que tem de errado no site", "analisa esse site", relatório para cliente ou pré-venda, mesmo citando só um segmento (ex.: "audita a segurança do site X").
---

# Análise de site

Skill para diagnosticar sites de clientes. Ela coleta os dados do site **uma vez**, distribui a análise entre **agentes especializados** que trabalham em paralelo sobre os mesmos dados, verifica os achados mais graves com um **agente independente** e gera um **relatório** para o cliente.

Toda a skill fica nesta pasta. Caminhos relativos abaixo partem dela (`<skill>/`).

| Pasta | Conteúdo |
|---|---|
| `agents/` | um arquivo por segmento + `verificador.md` |
| `references/` | regras comuns, padrões de segurança, LGPD, texto genérico em pt-BR, matriz de referência |
| `schemas/achados.schema.json` | formato obrigatório da saída de cada agente |
| `config/pesos.json` | peso de cada segmento na nota, por tipo de site |
| `scripts/` | `coleta.py`, `consolidar.py`, `relatorio.py` |
| `templates/relatorio.css` | visual do relatório |

## Modos

| Modo | Quando | Páginas | Agentes |
|---|---|---|---|
| `completa` (padrão) | Projeto de cliente | até 10 | todos, em paralelo, + verificador |
| `rapida` | Pré-venda, primeira impressão | só a home | sem subagentes: você mesmo cobre segurança passiva, desempenho, SEO, acessibilidade, copy e conversão, de forma resumida |
| `segmento` | Reauditoria depois de correções, ou pedido de um segmento só | conforme o pedido | só os segmentos pedidos (+ verificador se houver crítico/alto) |

Use o modo que o pedido indica. Na dúvida, `completa`.

## Pré-requisitos

Antes de qualquer análise, rode o verificador de ambiente. Ele confere Python, Playwright e o navegador dele, jsonschema, Node.js e a conexão com o PageSpeed do Google, e diz em português o que falta:

```bash
python <skill>/scripts/preparar.py              # só confere
python <skill>/scripts/preparar.py --instalar   # instala o que for seguro instalar sozinho
```

- Se faltar algo **obrigatório** (Python, Playwright, Chromium), rode com `--instalar`, confira de novo e só então siga. Se ainda faltar, explique ao usuário em linguagem simples o que ele precisa fazer.
- O **Node.js** é recomendado (Lighthouse local e axe-core), mas não obrigatório. O script nunca o instala sozinho; mostre ao usuário o comando que ele indica e siga a análise sem o Node se ele preferir.
- **Windows:** o `python` do PATH costuma ser só o atalho da Microsoft Store (imprime "Python não foi encontrado"). Descubra o interpretador real com `py -0p` (ou procure em `%LOCALAPPDATA%\Programs\Python\`) e use o caminho completo dele em todos os comandos no lugar de `python`.
- Não altere configurações de segurança do computador (antivírus, firewall) para a análise rodar.

## Fase 0: Escopo

1. **Pastas.** A análise usa uma **pasta de trabalho temporária** (`<saida>`) para a coleta, os achados dos agentes e os JSONs: crie com `python -c "import tempfile;print(tempfile.mkdtemp(prefix='analise-site-'))"` e use esse caminho em todos os comandos. O que o usuário recebe é só o **relatório** (`relatorio.html` e `relatorio.pdf`), na **pasta de destino** (`<destino>`): se o pedido é sobre um projeto aberto com código, `docs/analise/AAAA-MM-DD/` dentro do projeto; senão, `./analise-<dominio>-AAAA-MM-DD/`. No fim, `finalizar.py` copia o relatório para `<destino>` e apaga a pasta de trabalho.
2. **Contexto já documentado.** Se existirem `CLAUDE.md`, `docs/PRODUTO.md`, `docs/NEGOCIO.md`, `docs/ARQUITETURA.md` ou `docs/DESIGN.md`, leia antes de perguntar qualquer coisa.
3. **Pergunte só o que falta e muda o resultado**, de uma vez, em uma mensagem curta:
   - URL do site (obrigatória).
   - Tem acesso ao código? Caminho da pasta.
   - Tipo de site: `institucional`, `landing_page`, `ecommerce`, `saas_sistema` ou `blog_portal`. Proponha o que parece pelo site e peça só confirmação.
   - Objetivo principal do site (contato no WhatsApp, venda, agendamento, cadastro).
   - Nome da empresa e cidade (para Google Meu Negócio e concorrentes).
   - Concorrentes que o cliente já conhece (opcional).
   - Pode enviar o formulário de contato como teste? Padrão: **não**.
   - Se o site recebe tráfego pago: o texto do anúncio (opcional).

   Se o usuário não estiver presente para responder, siga com o que der para inferir, registre as suposições no `escopo.json` e avise no fim.
4. Grave `<saida>/escopo.json` com a ferramenta de escrita de arquivos (não por heredoc no shell). Em JSON, barras invertidas precisam ser escritas em dobro (duas barras) ou trocadas por `/` (use `C:/Projects/site`). Confira com `python -c "import json;json.load(open('escopo.json',encoding='utf-8'))"` antes de seguir:

```json
{
  "url": "https://exemplo.com.br",
  "cliente": "Empresa Exemplo",
  "cidade": "Manaus - AM",
  "data": "2026-10-10",
  "tipo_site": "institucional",
  "modo": "completa",
  "modo_analise": "url",
  "codigo": null,
  "objetivo": "Contato pelo WhatsApp",
  "concorrentes_informados": [],
  "anuncio": null,
  "autorizacao_envio_formulario": false,
  "segmentos": "todos",
  "suposicoes": ["Tipo de site inferido pela home"],
  "nome_site": null,
  "versao_relatorio": "1.0"
}
```

`modo_analise` é `url`, `codigo` ou `hibrido`. `segmentos` é `"todos"` ou uma lista (`["seguranca", "seo"]`). `nome_site` é opcional: se vazio, a capa usa o nome que o site mostra (`og:site_name` ou o título da home). `versao_relatorio` aparece no canto da capa; aumente a cada reauditoria (1.0, 1.1, 2.0).

## Fase 1: Coleta

```bash
python <skill>/scripts/coleta.py <url> --saida <saida> --modo <completa|rapida>
```

- A coleta espera 3 s após cada carregamento (telas de abertura) e procura o banner de cookies pelo botão Aceitar/Recusar, clica em Aceitar e mede o que carrega depois. Se `privacidade/consentimento.json` vier com `banner_detectado: false`, não conclua que o site não tem banner nem opção de recusar: confira no código. `--espera-abertura N` muda a espera.
- Lighthouse: se `lighthouse/*.json` trouxer `contaminado_por_antivirus`, as notas do Lighthouse local não valem (o antivírus injeta scripts) e o desempenho usa o PageSpeed do Google. **Nunca altere nem peça para a skill alterar o antivírus.** Se algo ficou barrado por ele, avise o usuário, na entrega, que **ele mesmo** pode pausar o antivírus e pedir uma nova análise do segmento, se quiser.
- A amostra é de até 10 páginas. Se o site tiver muitas páginas do mesmo tipo (cases, produtos), diga isso no relatório e use `--paginas-extra` para incluir exemplos de cada tipo.
- O desempenho é medido também pelo **site do PageSpeed do Google**, aberto no navegador da coleta (sem chave, como uma pessoa faria). O teste roda nos servidores do Google, então não sofre interferência de antivírus. Se `PSI_API_KEY` estiver definida, a coleta usa a API oficial no lugar. Se o PageSpeed estiver indisponível, a análise segue com as medições de laboratório. Nunca peça chave nem altere o antivírus ou outras configurações de segurança da máquina.
- Leva de 2 a 10 minutos. Opções úteis: `--max-paginas N`, `--paginas-extra URL ...` (páginas que precisam entrar, como a política de privacidade), `--sem-lighthouse`, `--sem-psi`.
- Ao terminar, leia `<saida>/coleta/resumo.json`. Ele lista as páginas, as ferramentas que funcionaram e as `falhas`. Se a home falhou (site fora do ar, bloqueio a robôs), pare e informe o usuário.
- A coleta é passiva: não envia formulários e não testa senhas.

## Fase 2: Agentes de segmento

### 2a. Negócio primeiro

Rode o agente `agents/negocio.md` antes dos outros (pode ser você mesmo, é rápido). Ele grava `achados/negocio.json` e `contexto-negocio.md`, que os demais agentes leem.

### 2b. Os outros em paralelo

Segmentos: `seguranca`, `privacidade`, `desempenho`, `seo`, `acessibilidade`, `design`, `copy`, `conversao`, `analytics`, `arquitetura`. No modo `segmento`, só os pedidos.

Dispare um subagente por segmento **na mesma mensagem**, para rodarem em paralelo, com a ferramenta de agentes (tipo `general-purpose`). Use este prompt, trocando os campos:

```
Você é o agente de <NOME DO SEGMENTO> da skill analise-site.

Skill: <caminho absoluto da skill>
Análise: <caminho absoluto de <saida>>

1. Leia <skill>/references/regras-comuns.md e <skill>/agents/<segmento>.md. Siga os dois à risca.
2. Leia <saida>/escopo.json, <saida>/contexto-negocio.md e <saida>/coleta/resumo.json.
3. Faça a checklist do seu arquivo usando a coleta em <saida>/coleta/.
   Código do projeto: <caminho absoluto, ou "não há">.
4. Grave o resultado em <saida>/achados/<segmento>.json seguindo <skill>/schemas/achados.schema.json. Use a ferramenta de escrita de arquivos (não heredoc no shell, que falha com aspas e acentos). Depois de gravar, valide: `<python> -c "import json;json.load(open(r'<arquivo>',encoding='utf-8'))"` e corrija se der erro.
5. Se um dado da coleta contradiz o código ou parece falha da ferramenta (certificado "vencido", banner não detectado, nota de Lighthouse com scripts de antivírus), confira por outro meio e registre em cobertura.nao_verificado em vez de gerar achado.
6. Responda só com: caminho do arquivo, nota, achados por severidade e o resumo.
Não altere o site nem o código. Não envie formulários.
```

Se a ferramenta de agentes não estiver disponível, faça os segmentos você mesmo, um de cada vez, lendo um arquivo de agente por vez e gravando o JSON antes de passar ao próximo.

Quando todos responderem, confira se os 11 arquivos existem em `<saida>/achados/`. Se algum agente falhou, rode de novo só ele.

## Fase 3: Verificação independente

Dispare um subagente novo com `agents/verificador.md`. Ele confere todos os achados críticos e altos e uma amostra dos médios, e grava `<saida>/verificacao.json`. Ele não deve receber o raciocínio dos outros agentes, só os caminhos.

Pule esta fase só no modo `rapida`.

## Fase 4: Consolidação e relatório

```bash
python <skill>/scripts/consolidar.py --saida <saida>
```

Leia `<saida>/consolidado.json` (nota geral, notas por segmento, achados priorizados, pontos fortes, avisos de validação). Se houver avisos de validação, corrija o JSON do agente e consolide de novo.

O script junta sozinho o que é claramente o mesmo problema: mesma checagem e mesmo trecho, ou texto muito parecido (pontuação de similaridade a partir de 0,35, sem severidades muito distantes). Cada junção automática aparece no terminal e em `consolidado.json -> estatisticas.juntados_detalhe`, para conferir. Ele nunca perde um achado e avisa se um grupo manual aponta para ID inexistente ou para um só segmento.

Repetições mais sutis (mesmo problema com palavras diferentes) ele só **sugere**, em `<saida>/duplicados-candidatos.json`, com pontuação e títulos lado a lado. Leia só essa lista (no máximo 15 pares), não todos os achados. Para cada par, confira se descrevem **o mesmo problema no mesmo lugar** e grave os confirmados em `<saida>/duplicados.json`; depois consolide de novo:

```json
[["PRI-003", "CON-005"], ["CON-003", "COP-001"]]
```

Não junte problemas parecidos mas diferentes (imagem sem alt e imagem pesada são dois achados). Com menos de 12 achados a pontuação não é confiável e só valem a regra exata e os grupos manuais.

Escreva `<saida>/resumo-executivo.md` para o dono do negócio, não para o desenvolvedor:
- 1 parágrafo: estado geral do site em linguagem simples, com a nota.
- 3 a 5 tópicos: o que fazer primeiro e por quê (vindos dos achados P1).
- 1 frase sobre o que está bom.
- Sem jargão sem explicação. Pode usar **negrito** e `código`.

Depois:

```bash
python <skill>/scripts/relatorio.py --saida <saida>
```

Gera `relatorio.html` (autossuficiente: imagens e issues ficam dentro dele; com botão "Baixar PDF") e `relatorio.pdf`. As issues do GitHub (uma por achado relevante, menores agrupados) ficam numa seção do HTML; só vira pasta `issues/` com `--issues`. O documento tem: capa, resumo executivo (nota geral e cartões por segmento com link), inconsistências (cartões por gravidade e prazo, tabela de todos os achados, o que está funcionando), um capítulo por segmento (capa com nota e sumário com link para cada achado) e metodologia. Cada parte começa em página nova no PDF. As issues ficam só no HTML. Abra o HTML com Playwright ou o navegador e confira se não há seção vazia nem erro visível antes de entregar.

## Fase 5: Entrega

1. Se o projeto tem repositório no GitHub, pergunte **uma vez**, antes de finalizar, se o usuário quer criar as issues (`gh issue create`). Se sim, rode `relatorio.py --saida <saida> --issues` e crie só depois da confirmação. Se não, siga.
2. Entregue o relatório e limpe a pasta de trabalho:

```bash
python <skill>/scripts/finalizar.py --trabalho <saida> --destino <destino>
```

O destino fica só com `relatorio.html` e `relatorio.pdf` (e `issues/` se pedido com `--issues`). Para guardar também os dados brutos (reauditoria, conferência de evidências), use `--manter-dados`; o padrão é apagar. O script só apaga pastas criadas pela skill (marca `.analise-site`).

3. Responda ao usuário com:
- Caminho do relatório HTML e do PDF.
- Nota geral e a faixa.
- Os 3 achados mais importantes, uma linha cada.
- Suposições feitas no escopo e o que não pôde ser verificado (resumido).
- Se alguma medição foi barrada pelo antivírus, uma linha dizendo que o usuário pode pausá-lo por conta própria e pedir nova análise daquele segmento.

Se o projeto já mantém arquivos de acompanhamento (por exemplo `docs/ESTADO.md` e `docs/TASKS.md`), acrescente neles um resumo da análise e os itens P1.

## Regras gerais

- **Somente leitura.** A análise não altera o site nem o código. Corrigir é outra etapa, com aprovação.
- **Testes passivos em produção.** Nada de força bruta, injeção, carga ou envio de formulário sem autorização.
- **Evidência em todo achado.** Sem evidência, não é achado. Ver `references/regras-comuns.md`.
- **Registrar pontos fortes** e o que não foi verificado.
- **Segredos sempre mascarados** no relatório.
- **Português do Brasil** em tudo que o cliente lê.
- A matriz `references/matriz-referencia.md` diz, para cada checagem, quais skills de referência a cobrem. Use-a para aprofundar um ponto e para evoluir a skill.
