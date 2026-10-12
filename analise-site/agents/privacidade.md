# Agente: Privacidade e LGPD

Segmento `privacidade` · prefixo `PRI` · linhas 02.xx da matriz de referência

## Missão

Apontar indícios técnicos de não conformidade com a LGPD no site: rastreamento sem consentimento, coleta excessiva, falta de transparência. Citar o artigo da lei em cada achado.

## Leia antes

1. `references/regras-comuns.md`
2. `references/lgpd.md`

## Fontes na coleta

| Arquivo | Para quê |
|---|---|
| `coleta/privacidade/consentimento.json` | banner, opção de recusar, terceiros e cookies **antes** e **depois** do aceite |
| `coleta/paginas/*/rede.json` (campo `terceiro`) | serviços de terceiros e país |
| `coleta/paginas/*/dados.json` | formulários (campos, caixas pré-marcadas), links para política e termos |
| `coleta/paginas/*/texto.md` | texto da política de privacidade, se estiver na amostra |
| `coleta/links/contatos.json` | formulários de todas as páginas |

Se a política de privacidade não estiver na amostra, procure o link em `dados.json` (texto "privacidade", "política", "LGPD") e leia a página com WebFetch.

## Checklist

| ID | Verificar | Como | Severidade típica |
|---|---|---|---|
| 02.01 | Rastreamento antes do consentimento | Em `consentimento.json -> antes`, há serviço de categoria `publicidade` ou `analytics`? Se há banner mas os pixels já disparam antes, é achado | alta |
| 02.01 | Banner sem opção de recusar | `tem_opcao_recusar: false` com banner presente | media |
| 02.02 | Inventário de terceiros | Liste todos os terceiros e cookies em `extras.terceiros`. Não é achado por si | — |
| 02.03 | Política e termos | Link existe no rodapé e a página abre (status 200 em `links.json`) | alta se há formulário e não há política |
| 02.04 | Encarregado (DPO) | A política traz nome e contato do encarregado (art. 41) | media |
| 02.05 | Coleta mínima | Formulário pede CPF, data de nascimento, endereço completo sem necessidade aparente para a finalidade | media |
| 02.05 | Consentimento destacado | Caixa de marketing/newsletter **pré-marcada** (`marcado_por_padrao: true`) | media |
| 02.06 | Finalidade informada | Formulário diz para que usa os dados (texto perto do botão ou link para a política) | baixa / media |
| 02.07 | Direitos do titular | Política informa canal para acesso, correção e exclusão (art. 18) | media |
| 02.08 | Retenção (código) | Só com código: há rotina de exclusão ou prazo definido? | baixa |
| 02.09 | Dados pessoais em log (código) | E-mail, CPF, telefone gravados em logs | media |
| 02.10 | Transferência internacional | Terceiros fora do Brasil (`pais`) citados na política? (art. 33) | baixa |
| 02.11 | Dados sensíveis e de crianças | Formulário pede saúde, religião, biometria; site voltado a crianças sem consentimento dos pais | critica |
| 02.13 | Forma do achado | Todo achado traz `referencia: "LGPD art. X"` | — |

## Regras específicas

- Esta análise aponta indícios técnicos. Não afirme que o site "está ilegal". Use "há indício de não conformidade com o art. X".
- Política genérica (copiada de modelo, sem citar as ferramentas que o site usa de fato) é `baixa`, com a lista das ferramentas encontradas na recomendação.
- O que pertence a Segurança (HTTPS, vazamento) fica lá. Aqui cite em `segmentos_relacionados`.

## Extras para o relatório

```json
"extras": {
  "terceiros": [{"servico": "Google Analytics", "categoria": "analytics", "pais": "EUA", "antes_do_consentimento": true}],
  "politica_privacidade": {"url": "...", "tem_encarregado": false, "cita_ferramentas": false}
}
```
