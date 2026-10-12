# analise-site

Skill para o [Claude Code](https://claude.com/claude-code) que analisa um site por completo e entrega um relatório em HTML e PDF.

Cobre segurança, privacidade e LGPD, desempenho, SEO, acessibilidade, design, texto, conversão, medição, base técnica e negócio. Um agente por segmento trabalha em paralelo sobre os mesmos dados coletados, um verificador independente confere os achados mais graves, e o resultado são só dois arquivos: `relatorio.html` e `relatorio.pdf`.

A análise é somente leitura: não altera o site e não envia formulários sem autorização. Não precisa de chave de API nem de conta.

## Instalar

Requisitos: Python 3.9+ e internet. Node.js 18+ é recomendado.

```bash
git clone https://github.com/tiagomagno/analise-site.git
cd analise-site
python instalar.py
```

O instalador copia a skill para `~/.claude/skills/analise-site` (ou só para um projeto, com `--projeto <pasta>`) e instala o que faltar (playwright, Chromium, jsonschema). Depois, no Claude Code:

```
analisa o site https://exemplo.com.br
```

Também dá para baixar o `.zip` da página de [Releases](../../releases), quando houver.

## Documentação

A documentação completa (o que cada segmento analisa, métodos, requisitos, limites) está em [`analise-site/README.md`](analise-site/README.md). O fluxo que o Claude segue está em [`analise-site/SKILL.md`](analise-site/SKILL.md).

## Estrutura do repositório

```
analise-site/            a skill (é isto que vai para ~/.claude/skills)
instalar.py              instala a skill e confere o ambiente
empacotar.py             gera o .zip de distribuição em dist/
LEIA-ME.txt              instruções curtas que vão dentro do .zip
```

## Atualizar a skill

1. Edite os arquivos dentro de `analise-site/` neste repositório.
2. Instale a versão editada para testar: `python instalar.py` (a versão anterior é guardada ao lado, sem apagar).
3. Faça o commit.
4. Para distribuir: `python empacotar.py --versao 1.1` gera `dist/analise-site-1.1.zip`.

Mantenha o repositório como fonte da verdade: não edite direto em `~/.claude/skills/analise-site`, senão as mudanças se perdem na próxima instalação.
