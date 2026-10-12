# Agente: Acessibilidade

Segmento `acessibilidade` · prefixo `ACE` · linhas 05.xx da matriz de referência

## Missão

Avaliar se pessoas com deficiência conseguem usar o site, com base na WCAG 2.2 nível AA. Bases: web-quality-skills/accessibility e vercel/web-interface-guidelines.

## Leia antes

`references/regras-comuns.md`

## Fontes na coleta

| Arquivo | Para quê |
|---|---|
| `coleta/paginas/*/axe.json` | violações automáticas do axe-core por página (id, impacto, ocorrências, exemplos) |
| `coleta/lighthouse/resumo-lighthouse.json -> falhas.accessibility` | auditorias do Lighthouse |
| `coleta/paginas/*/dados.json` | `lang`, imagens, formulários (`tem_label`), `skip_link`, `landmarks`, `aria_live`, vídeos, `usa_reduced_motion` |
| `coleta/paginas/*/layout.json -> mobile.alvos_pequenos` | alvos de toque menores que 24 px |
| `coleta/paginas/*/desktop.png`, `mobile.png` | contraste e foco visíveis na imagem |

## Checklist

| ID | Verificar | Como | WCAG | Severidade típica |
|---|---|---|---|---|
| 05.01 | Automático + manual | Use axe e Lighthouse como ponto de partida; confirme cada um no HTML ou na imagem | — | — |
| 05.02 | Texto alternativo | `image-alt`, `tem_alt: false` em imagem com conteúdo; ícone-botão sem nome | 1.1.1 | media / alta (botão sem nome) |
| 05.03 | Contraste | `color-contrast` do axe; texto cinza claro nas imagens | 1.4.3 | media |
| 05.04 | Teclado | Se possível, abra a home e navegue com Tab (ferramenta de navegador). Elementos clicáveis que são `div` sem `tabindex`; menus que só abrem no hover | 2.1.1 | alta |
| 05.05 | Foco visível | `outline: none` sem substituto; foco escondido atrás de cabeçalho fixo | 2.4.7, 2.4.11 | media |
| 05.06 | Skip link e landmarks | `skip_link: false`, `landmarks.main: 0` | 2.4.1 | baixa |
| 05.07 | Alvo de toque | `alvos_pequenos` no celular (< 24 px) | 2.5.8 | media |
| 05.08 | Idioma | `lang` ausente ou diferente de `pt-BR`/`pt` | 3.1.1 | media |
| 05.09 | Formulários | Campos sem rótulo (`tem_label: false`, placeholder não conta); mensagens de erro só por cor | 3.3.2, 3.3.1 | alta |
| 05.10 | Movimento | Animações e carrosséis automáticos sem `prefers-reduced-motion` nem botão de pausa | 2.2.2, 2.3.3 | baixa |
| 05.11 | ARIA | Erros evidentes do axe (`aria-*` inválido, `role` errado) | 4.1.2 | media |
| 05.12 | Mídia | Vídeo com fala sem legenda (`videos[].legendas: false`) | 1.2.2 | media |
| 05.13 | Login e cadastro | Só se existirem: colar senha bloqueado, captcha sem alternativa, dados pedidos duas vezes | 3.3.7, 3.3.8 | media |
| 05.16 | Severidade | axe `critical` → alta, `serious` → media, `moderate` → baixa, `minor` → baixa. Ajuste pelo alcance (página inteira ou um detalhe) | — | — |

## Regras específicas

- Nota 100 no Lighthouse não significa site acessível. Diga isso no `resumo` quando o automático estiver limpo e você não tiver testado teclado.
- Agrupe a mesma violação em várias páginas num achado só, com a contagem.
- Problemas visuais de design (contraste baixo de marca) também aparecem em Design: cite em `segmentos_relacionados`.
