# Regras comuns a todos os agentes

Todo agente de segmento lê este arquivo antes de começar. Ele vale tanto quanto o arquivo do próprio agente.

## 1. Evidência ou nada

- Todo achado aponta para algo que outra pessoa consegue conferir: URL, arquivo e linha, trecho de código ou de texto, métrica medida ou screenshot.
- Achado com evidência direta tem `confianca: "verificado"`.
- Achado com indício forte mas sem prova direta tem `confianca: "suspeita"` e a recomendação começa com "Confirmar se...".
- Sem indício, não existe achado. Não preencha categoria com problema genérico para parecer completo.
- Quando um ponto da sua checklist não pôde ser verificado (faltou dado, a página exigia login, a ferramenta falhou), registre em `cobertura.nao_verificado` com o motivo. Isso não é achado.

## 2. Registre o que está certo

- Cada ponto verificado e aprovado com evidência clara pode virar `pontos_fortes`. Liste os 3 a 6 mais relevantes para o cliente, não todos.
- Ponto forte também precisa de evidência ("Todas as 8 páginas têm um único H1", não "boa estrutura").

## 3. Não aplicável é diferente de aprovado

Se a checagem não faz sentido para o site (não há login, não há vídeo, site sem código disponível), coloque em `cobertura.nao_aplicavel`. Não conte como ponto forte nem como achado.

## 4. Severidade

| Severidade | Use quando | Exemplos |
|---|---|---|
| `critica` | Dano sério e imediato, explorável ou visível para qualquer visitante | Segredo exposto, dados de outro usuário acessíveis, site fora do ar no celular, formulário de contato que não envia, domínio marcado como perigoso |
| `alta` | Prejuízo claro para usuário, conversão, ranqueamento ou conformidade | Sem HTTPS em alguma página, LCP acima de 4 s, página principal com noindex, CTA principal invisível no celular, rastreamento antes do consentimento |
| `media` | Problema real, com impacto moderado ou em parte do site | Headers de segurança ausentes, imagens sem alt, meta descriptions duplicadas, contraste baixo em texto secundário |
| `baixa` | Melhoria de qualidade, impacto pequeno | Favicon faltando em um tamanho, título 5 caracteres acima do ideal |
| `info` | Observação útil sem problema concreto | Sugestão de teste A/B, oportunidade de conteúdo |

Na dúvida entre duas, escolha a menor e explique no texto. Severidade inflada derruba a confiança no relatório inteiro.

## 5. Esforço

`P` = horas, `M` = dias, `G` = semanas. Estime pelo que a correção exige de fato, não pelo tamanho do problema.

## 6. Nota do segmento (0 a 100)

Comece em 100 e desconte por achado confirmado. Suspeitas descontam metade.

| Severidade | Desconto |
|---|---|
| critica | 25 |
| alta | 12 |
| media | 5 |
| baixa | 2 |
| info | 0 |

- Nota mínima 0. Se o segmento inteiro não se aplica, use `null`.
- Se mais da metade da checklist ficou em `nao_verificado`, limite a nota a 70 e diga isso no `resumo`.
- O desconto é um ponto de partida. Você pode ajustar até 10 pontos para mais ou para menos, explicando no `resumo`.

## 7. Escreva para o cliente

- Português do Brasil, frases curtas, sem jargão sem explicação. "O site guarda o login num lugar que qualquer script da página consegue ler" antes de "token em localStorage".
- `impacto_usuario` diz o que o visitante sente. `impacto_negocio` diz o que o cliente perde (vendas, contatos, ranqueamento, multa, reputação).
- `recomendacao` diz o que fazer, de forma específica: "Comprimir hero.jpg (1,8 MB) para WebP com até 200 KB" e não "otimizar imagens".
- Quantifique sempre que tiver o número: tempo, tamanho, quantidade de páginas afetadas.

## 8. Somente leitura e segurança na coleta

- A análise não altera nada no site nem no código.
- Não faça teste ativo de ataque (força bruta, injeção, carga) em site no ar. As checagens de segurança em produção são passivas.
- Não envie formulários de contato, cadastro ou compra, a menos que o escopo diga que o cliente autorizou.
- Se encontrar um segredo, nunca copie o valor completo para o relatório. Mostre só o início mascarado (`sk_live_51H...`) e onde está.

## 9. Um achado, um problema

- Não junte problemas diferentes num achado só.
- Problemas iguais em várias páginas viram um achado com a lista de páginas no campo `evidencia.url` (separadas por vírgula) ou na `metrica` ("12 de 15 páginas").
- Se o problema pertence mais a outro segmento, cite em `segmentos_relacionados` em vez de duplicar. A consolidação junta os repetidos.

## 10. Formato de saída

- Grave um único arquivo `achados/<segmento>.json` seguindo `schemas/achados.schema.json`.
- IDs dos achados: prefixo de 3 letras do segmento + número sequencial (`SEG-001`, `PRI-001`, `DES-001`, `SEO-001`, `ACE-001`, `DSG-001`, `COP-001`, `CON-001`, `ANA-001`, `ARQ-001`, `NEG-001`).
- `check_id` é o ID da linha na matriz de referência que motivou o achado (ex.: `01.12`). Ele permite comparar a nossa skill com as referências depois.
- Ao terminar, responda ao orquestrador só com: caminho do arquivo, nota, quantidade de achados por severidade e o `resumo`. Não repita os achados na resposta.
