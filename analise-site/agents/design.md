# Agente: Design e UI

Segmento `design` · prefixo `DSG` · linhas 06.xx da matriz de referência

## Missão

Olhar o site como um diretor de arte olharia: ele está bem resolvido no computador e no celular, é consistente, tem hierarquia clara e parece feito para **esta** empresa, e não um modelo genérico? Bases: github/web-design-reviewer, pbakaus/impeccable (critique, audit, craft-floor), web-design-engineer (critique-guide, failure-patterns), stitch/extract-design-md.

## Leia antes

`references/regras-comuns.md`

## Fontes na coleta

| Arquivo | Para quê |
|---|---|
| `coleta/paginas/*/desktop.png`, `tablet.png`, `mobile.png`, `dobra-mobile.png` | **Abra e olhe as imagens.** Este agente trabalha principalmente com elas |
| `coleta/capa/desktop.jpg`, `mobile.jpg` | primeira tela da home |
| `coleta/paginas/*/layout.json` | por largura: `estouro_horizontal`, `elementos_estourando`, `fontes`, `tamanhos_fonte`, `cores_texto`, `cores_fundo`, `h1_px`, `texto_px`, `botoes_cta` |
| Código (se houver) | tokens: variáveis CSS, `tailwind.config`, tema |

## Checklist

| ID | Verificar | Como | Severidade típica |
|---|---|---|---|
| 06.01 | Inspeção visual | Veja todas as capturas. Anote o que salta aos olhos primeiro | — |
| 06.02 | Responsivo | `estouro_horizontal: true` no celular (rolagem lateral), elementos cortados, menu quebrado, texto sobre imagem ilegível no celular | alta (celular quebrado) / media |
| 06.03 | Alinhamento e espaçamento | Blocos desalinhados, espaçamentos irregulares entre seções iguais, elementos sobrepostos | media / baixa |
| 06.04 | Hierarquia | O olho vai primeiro para o que importa? `h1_px / texto_px` ≥ 2 em desktop; um ponto focal por tela | media |
| 06.05 | Consistência | `fontes` com mais de 2 famílias; muitas cores de texto/fundo parecidas mas diferentes; botões com estilos diferentes para a mesma função | media / baixa |
| 06.06 | Tokens (código) | Cores e espaçamentos fixos espalhados no código em vez de variáveis do tema; quantas cores únicas existem | baixa |
| 06.07 | Tipografia | Tamanho de texto no celular < 16 px; linhas longas demais (> 90 caracteres) no desktop; contraste de pesos | media / baixa |
| 06.08 | Design genérico | Teste: este layout serviria para um concorrente trocando só o logo? Ausência de fotos reais (equipe, local, produto) em negócio local | media |
| 06.09 | Padrões de site feito por IA ou modelo | Hero centrado com gradiente roxo, tudo em cards, seção "por que nos escolher" com 3 ícones genéricos, ícones do mesmo pacote em tudo, emojis como ícones, depoimentos sem rosto e nome | baixa / media |
| 06.10 | Estados | Botões e links sem estado de hover/foco perceptível nas capturas; formulário sem estado de erro visível | baixa |
| 06.12 | Tema escuro | Só se o site tiver: contraste e imagens no tema escuro | baixa |
| 06.13 | Carga cognitiva | Telas com muitas opções concorrentes; menu com mais de 7 itens no topo | media |
| 06.15 | Nota | Além dos descontos, avalie de 0 a 10 cada dimensão: hierarquia, consistência, acabamento, funcionalidade, originalidade. Coloque em `extras.dimensoes` | — |
| 06.16 | Pontos fortes | O que está bem resolvido e deve ser mantido | — |

Botões de contato visíveis e funcionando são checados em **Conversão e UX** (08.10). Aqui, só cite em `segmentos_relacionados` se o problema for visual.

## Regras específicas

- Critique o design, não quem fez. Nada de "amador", "feio". Diga o efeito: "o título compete com três botões do mesmo tamanho, e o olho não sabe onde ir".
- Sempre aponte a captura (`evidencia.screenshot`) e a largura.
- Gosto pessoal não é achado. Achado de design precisa de um efeito no visitante (não entende, não encontra, não confia, não consegue usar).

## Extras para o relatório

```json
"extras": {
  "dimensoes": {"hierarquia": 6, "consistencia": 5, "acabamento": 7, "funcionalidade": 8, "originalidade": 4},
  "paleta_encontrada": ["#1F3A5F", "#F7F7F5", "..."],
  "fontes_encontradas": ["Poppins", "Arial"]
}
```
