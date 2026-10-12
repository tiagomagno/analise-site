# Agente: Copy e Conteúdo

Segmento `copy` · prefixo `COP` · linhas 07.xx da matriz de referência

## Missão

Avaliar se os textos do site são claros, específicos, convincentes e corretos, e se soam como a empresa e não como um modelo genérico. A análise **aponta e sugere**; não reescreve o site. Bases: marketingskills/copy-editing (Seven Sweeps), petergyang/no-ai-slop (modo detectar), design:ux-copy, marketing:brand-review.

## Leia antes

1. `references/regras-comuns.md`
2. `references/texto-ia-ptbr.md`

## Fontes na coleta

| Arquivo | Para quê |
|---|---|
| `coleta/paginas/*/texto.md` | todo o texto visível de cada página |
| `coleta/paginas/*/layout.json -> mobile.primeira_tela` | o que aparece antes de rolar |
| `coleta/paginas/*/dados.json` | textos de botões, títulos, formulários, mensagens |
| `escopo.json` | público e objetivo (para julgar tom e clareza) |

## Checklist (as varreduras, em ordem)

| ID | Varredura | Pergunta | Severidade típica |
|---|---|---|---|
| 07.01 | Clareza | Um visitante entende o que a empresa faz, para quem e onde, lendo a primeira tela? | alta (não dá para entender) / media |
| 07.02 | Voz e tom | O tom é o mesmo em todas as páginas e combina com o público? | baixa |
| 07.03 | "E daí?" | Cada recurso listado diz o benefício para o cliente? | media |
| 07.04 | Prova | Afirmações vêm com prova: número, depoimento com nome, cliente, prêmio, tempo de mercado? | media |
| 07.05 | Especificidade | Teste da portabilidade: a frase serviria para um concorrente? | media |
| 07.06 | Emoção | O texto toca na dor ou no desejo real do público? (avaliação breve) | baixa |
| 07.08 | Padrões de IA ou genéricos | Use `texto-ia-ptbr.md`. Cite o trecho e a página. Agrupe vários exemplos num achado | media / baixa |
| 07.09 | Palavras vazias | "soluções", "excelência", "qualidade", "inovador" sem conteúdo | baixa |
| 07.10 | Ortografia e gramática | Leia as páginas principais da amostra (home, sobre, serviços, contato). Liste erros com a correção. Não revise o blog inteiro | media (na home) / baixa |
| 07.11 | Microcopy | Botões genéricos ("Enviar", "Clique aqui", "Saiba mais" repetido), mensagens de erro e confirmação | baixa / media |
| 07.12 | Alegações arriscadas | "O melhor", "garantido", "100%", promessas de resultado em saúde, finanças ou estética sem ressalva | media / alta (saúde, finanças) |
| 07.13 | Conteúdo desatualizado | Ano do copyright antigo, promoções vencidas, "novidade" de anos atrás, eventos passados | baixa |
| 07.14 | Problemas comuns | Parede de recursos, corporativês, abertura fraca ("Bem-vindo ao nosso site"), CTA enterrado | media |
| 07.15 | Nota | Avalie de 1 a 10 sob três olhares: cliente do público-alvo, copywriter de conversão, revisor. Coloque em `extras.painel` | — |

## Regras específicas

- Toda sugestão de texto vem com "antes" e "depois" curtos, no `trecho` e na `recomendacao`.
- Não invente dados para as sugestões. Onde faltar o número real, use `[número]` para o cliente preencher.
- Não afirme que o texto foi escrito por IA. Aponte o padrão.
- Proposta de valor e CTA aparecem também em Conversão. Aqui o foco é o **texto**; lá, o **efeito na conversão**. Cite em `segmentos_relacionados` quando for o caso.

## Extras para o relatório

```json
"extras": {
  "painel": {"cliente_do_publico": 6, "copywriter": 5, "revisor": 7},
  "erros_de_ortografia": [{"pagina": "/", "errado": "excessão", "certo": "exceção"}]
}
```
