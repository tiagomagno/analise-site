#!/usr/bin/env python3
"""
Gera o relatório da análise.

Lê   <saida>/consolidado.json, <saida>/escopo.json, <saida>/resumo-executivo.md (opcional),
     <saida>/coleta/resumo.json e <saida>/coleta/capa/*.jpg
Grava <saida>/relatorio.html  (com botão "Baixar PDF")
      <saida>/relatorio.pdf   (A4, via Playwright; pule com --sem-pdf)
      <saida>/issues/ISSUE-NNN.md e <saida>/issues/todas.md

Estrutura do documento (cada item abre página nova no PDF):
  1. Capa                      imagem do site, nome, URL, nota; data e versão no canto
  2. Resumo executivo          nota geral, cartões por segmento (com âncora), sobre o relatório, diagnóstico
  3. Inconsistências           cartões por severidade e por prazo, tabela de todos os achados, o que está funcionando
  4. Um capítulo por segmento  capa do segmento com sumário (âncoras) e os achados
  5. Metodologia
  (Issues do GitHub: dentro do HTML; a pasta issues/ só com --issues)

Uso: python relatorio.py --saida docs/analise/2026-10-10
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import html
import json
import re
from pathlib import Path
from urllib.parse import urlparse

RAIZ = Path(__file__).resolve().parent.parent
SEV = {"critica": ("Crítica", "#B91C1C"), "alta": ("Alta", "#EA580C"), "media": ("Média", "#D97706"),
       "baixa": ("Baixa", "#2563EB"), "info": ("Info", "#6B7280")}
COR_FORTE = "#059669"
FAIXA_COR = [(90, "#047857"), (75, "#059669"), (50, "#D97706"), (0, "#B91C1C")]
FAIXA_NOME = [(90, "Excelente"), (75, "Bom"), (50, "Precisa melhorar"), (0, "Crítico")]
PRIO = {"P1": "Esta semana", "P2": "Este mês", "P3": "Próximos 90 dias"}
PRIO_COR = {"P1": "#B91C1C", "P2": "#D97706", "P3": "#2563EB"}

# ícones de traço (24x24), desenhados para este relatório
ICONES = {
    "seguranca": '<path d="M12 3l7 3v5c0 4.5-3 8.4-7 10-4-1.6-7-5.5-7-10V6z"/><path d="M9 12l2 2 4-4"/>',
    "privacidade": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    "desempenho": '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
    "seo": '<circle cx="11" cy="11" r="7"/><path d="M16.5 16.5L21 21"/>',
    "acessibilidade": '<circle cx="12" cy="4.5" r="2"/><path d="M5 8.5h14M12 8.5V14m0 0l-4 7m4-7l4 7"/>',
    "design": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 9v12"/>',
    "copy": '<path d="M4 6h16M4 11h16M4 16h10M4 21h6"/>',
    "conversao": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
    "analytics": '<path d="M3 21h18M6 17v-6M11 17V5M16 17v-9M21 17v-3"/>',
    "arquitetura": '<rect x="3" y="4" width="18" height="7" rx="1.5"/><rect x="3" y="13" width="18" height="7" rx="1.5"/><path d="M7 7.5h.01M7 16.5h.01"/>',
    "negocio": '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2M3 13h18"/>',
    "resumo": '<path d="M7 3h8l4 4v14H7z"/><path d="M15 3v4h4M10 12h6M10 16h6"/>',
    "alerta": '<path d="M12 3l9.5 17h-19z"/><path d="M12 10v4M12 17h.01"/>',
    "ok": '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.5 2.5L16 9.5"/>',
    "metodo": '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M5 19l2-2M17 7l2-2"/>',
    "relogio": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "lista": '<path d="M9 6h11M9 12h11M9 18h11M4 6h.01M4 12h.01M4 18h.01"/>',
    "github": '<path d="M9 19c-4 1.5-4-2-6-2.5M15 22v-3.5a3 3 0 0 0-.9-2.4c3-.3 6.1-1.5 6.1-6.6a5 5 0 0 0-1.4-3.6 4.7 4.7 0 0 0-.1-3.6s-1.1-.3-3.7 1.4a12.6 12.6 0 0 0-6.6 0C5.8 1.6 4.7 2 4.7 2a4.7 4.7 0 0 0-.1 3.6A5 5 0 0 0 3.2 9.2c0 5 3.1 6.3 6.1 6.6A3 3 0 0 0 8.4 18v4"/>',
}


def icone(nome: str, classe: str = "ic") -> str:
    return (f'<svg class="{classe}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONES.get(nome, ICONES["lista"])}</svg>')


def e(x) -> str:
    return html.escape("" if x is None else str(x))


def cor_nota(n):
    if n is None:
        return "#9CA3AF"
    return next(c for m, c in FAIXA_COR if n >= m)


def faixa(n):
    if n is None:
        return "Informativo"
    return next(c for m, c in FAIXA_NOME if n >= m)


RAIZ_SAIDA: Path = Path(".")
_NAV: dict = {}
_CACHE_MINI: dict = {}


def _navegador():
    if "b" not in _NAV:
        from playwright.sync_api import sync_playwright
        _NAV["p"] = sync_playwright().start()
        _NAV["b"] = _NAV["p"].chromium.launch(args=["--no-sandbox"])
    return _NAV["b"]


def fechar_navegador() -> None:
    try:
        if "b" in _NAV:
            _NAV["b"].close()
            _NAV["p"].stop()
    except Exception:
        pass
    _NAV.clear()


def miniatura(rel: str, largura_max: int = 900, altura_max: int = 2200) -> str | None:
    """Reduz uma captura de tela e a devolve embutida (data URI), para o HTML não depender de arquivos externos."""
    if rel in _CACHE_MINI:
        return _CACHE_MINI[rel]
    arq = RAIZ_SAIDA / rel
    resultado = None
    if arq.exists():
        try:
            dados = base64.b64encode(arq.read_bytes()).decode()
            pg = _navegador().new_page(viewport={"width": largura_max, "height": 800})
            pg.set_content(f'<body style="margin:0;background:#fff"><img id="i" style="display:block;max-width:{largura_max}px" '
                           f'src="data:image/png;base64,{dados}"></body>')
            pg.wait_for_function("document.getElementById('i').complete")
            w, h = pg.evaluate("[document.getElementById('i').width, document.getElementById('i').height]")
            jpg = pg.screenshot(type="jpeg", quality=55, full_page=True, clip={"x": 0, "y": 0, "width": w, "height": min(h, altura_max)})
            pg.close()
            resultado = "data:image/jpeg;base64," + base64.b64encode(jpg).decode()
        except Exception:
            resultado = None
    _CACHE_MINI[rel] = resultado
    return resultado


def img_b64(p: Path) -> str | None:
    if not p.exists():
        return None
    return "data:image/jpeg;base64," + base64.b64encode(p.read_bytes()).decode()


def inline(t: str) -> str:
    t = e(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    return t


def md_simples(texto: str) -> str:
    """Markdown mínimo: parágrafos, listas, negrito, títulos com #."""
    blocos, lista = [], []
    for linha in texto.strip().splitlines():
        l = linha.strip()
        if l.startswith(("- ", "* ")):
            lista.append(f"<li>{inline(l[2:])}</li>")
            continue
        if lista:
            blocos.append("<ul>" + "".join(lista) + "</ul>")
            lista = []
        if not l:
            continue
        if l.startswith("#"):
            blocos.append(f"<h4>{inline(l.lstrip('#').strip())}</h4>")
        else:
            blocos.append(f"<p>{inline(l)}</p>")
    if lista:
        blocos.append("<ul>" + "".join(lista) + "</ul>")
    return "\n".join(blocos)


def pill(texto: str, cor: str) -> str:
    return f'<span class="pill" style="--c:{cor}">{e(texto)}</span>'


def chip(sev: str) -> str:
    nome, cor = SEV.get(sev, (sev, "#6B7280"))
    return pill(nome, cor)


def chip_prazo(p: str) -> str:
    return pill(f"{p} · {PRIO[p]}", PRIO_COR[p])


def barra(nota, largura="100%") -> str:
    if nota is None:
        return '<div class="barra-nota vazia"></div>'
    return f'<div class="barra-nota" style="width:{largura}"><span style="width:{nota}%;--c:{cor_nota(nota)}"></span></div>'


# ---------------------------------------------------------------- nome do site
def nome_do_site(meta: dict, escopo: dict, saida: Path) -> str:
    """Nome como o próprio site se apresenta: og:site_name, depois o título da home.
    Se o título não tiver separador (|, -, ·) e for longo, usa o nome do cliente do escopo."""
    cliente = escopo.get("nome_site") or escopo.get("cliente") or meta.get("cliente")
    if escopo.get("nome_site"):
        return escopo["nome_site"]
    dados = saida / "coleta" / "paginas" / "home" / "dados.json"
    if dados.exists():
        d = json.loads(dados.read_text(encoding="utf-8"))
        if (d.get("open_graph") or {}).get("og:site_name"):
            return d["open_graph"]["og:site_name"]
        titulo = (d.get("titulo") or "").strip()
        partes = [p.strip() for p in re.split(r"\s[|\-–—·:]\s", titulo) if p.strip()]
        if len(partes) > 1:
            return min(partes, key=len)
        if titulo and (len(titulo) <= 40 or not cliente):
            return titulo if len(titulo) <= 60 else titulo[:60].rsplit(" ", 1)[0]
    return cliente or urlparse(meta.get("site") or "").netloc or "Site analisado"


# ---------------------------------------------------------------- blocos de achado
def bloco_evidencia(ev: dict) -> str:
    if not ev:
        return ""
    linhas = []
    if ev.get("url"):
        urls = [u.strip() for u in str(ev["url"]).split(",") if u.strip()]
        links = ", ".join(f'<a href="{e(u)}">{e(u)}</a>' if u.startswith("http") else e(u) for u in urls[:6])
        if len(urls) > 6:
            links += f" e mais {len(urls) - 6}"
        linhas.append(f"<div><b>Onde:</b> {links}</div>")
    if ev.get("arquivo"):
        linhas.append(f"<div><b>Arquivo:</b> <code>{e(ev['arquivo'])}{(':' + e(ev['linhas'])) if ev.get('linhas') else ''}</code></div>")
    if ev.get("metrica"):
        linhas.append(f"<div><b>Medida:</b> {e(ev['metrica'])}</div>")
    if ev.get("trecho"):
        linhas.append(f"<pre>{e(ev['trecho'])}</pre>")
    if ev.get("screenshot"):
        mini = miniatura(str(ev["screenshot"]))
        if mini:
            linhas.append(f'<div class="shot"><img src="{mini}" alt="Captura de tela da evidência"></div>')
    return '<div class="evidencia">' + "".join(linhas) + "</div>"


def cartao_achado(a: dict) -> str:
    rel = a.get("segmentos_relacionados") or []
    meta = [chip(a["severidade"]), chip_prazo(a["prioridade"]), f'<span class="tag">Esforço {e(a.get("esforco"))}</span>']
    if a.get("confianca") == "suspeita":
        meta.append('<span class="tag aviso">Suspeita: confirmar</span>')
    if a.get("severidade_original"):
        meta.append(f'<span class="tag">Reclassificado de {e(SEV[a["severidade_original"]][0])}</span>')
    return f"""
<article class="achado" id="{e(a['id'])}" style="--c:{SEV[a['severidade']][1]}">
  <header><span class="id">{e(a['id'])}</span><h4>{e(a['titulo'])}</h4><a class="topo no-print" href="#seg-{e(a['segmento'])}">↑ sumário</a></header>
  <div class="metas">{''.join(meta)}</div>
  <dl>
    <dt>Para o visitante</dt><dd>{e(a.get('impacto_usuario'))}</dd>
    <dt>Para o negócio</dt><dd>{e(a.get('impacto_negocio'))}</dd>
    <dt>O que fazer</dt><dd>{e(a.get('recomendacao'))}</dd>
  </dl>
  {bloco_evidencia(a.get('evidencia') or {})}
  <footer>{('Referência: ' + e(a['referencia']) + ' · ') if a.get('referencia') else ''}Matriz {e(a.get('check_id'))}{(' · Também afeta: ' + e(', '.join(rel))) if rel else ''}</footer>
</article>"""


TITULOS_EXTRAS = {"concorrentes": "Concorrentes", "reputacao": "Reputação do domínio", "modelo_negocio": "Resumo do negócio",
                  "google_meu_negocio": "Google Meu Negócio", "core_web_vitals": "Core Web Vitals", "ferramentas": "Ferramentas detectadas",
                  "oportunidades": "Oportunidades", "testes_sugeridos": "Testes A/B sugeridos", "terceiros": "Serviços de terceiros",
                  "politica_privacidade": "Política de privacidade", "headers": "Cabeçalhos de segurança", "lighthouse": "Notas do Lighthouse",
                  "dimensoes": "Avaliação por dimensão (0 a 10)", "painel": "Painel de avaliação (1 a 10)", "erros_de_ortografia": "Erros de ortografia",
                  "canais_de_contato": "Canais de contato", "stack": "Tecnologias", "email_dominio": "E-mail do domínio", "certificado": "Certificado",
                  "titulos_sugeridos": "Títulos e descrições sugeridos", "fontes_encontradas": "Fontes encontradas", "paleta_encontrada": "Cores encontradas",
                  "eventos_encontrados": "Eventos de analytics", "handlers_verificados": "Rotas verificadas"}


def rotulo(k) -> str:
    k = str(k)
    return TITULOS_EXTRAS.get(k, (k[:1].upper() + k[1:]).replace("_", " "))


def celula(x) -> str:
    if isinstance(x, (dict, list)):
        return tabela_generica(x)
    if isinstance(x, bool):
        return "sim" if x else "não"
    s = "" if x is None else str(x)
    if s.startswith("http"):
        return f'<a href="{e(s)}">{e(s)}</a>'
    return e(s) if s else '<span class="muted">–</span>'


def tabela_generica(v) -> str:
    if isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
        cols = list(dict.fromkeys(k for x in v for k in x))
        cab = "".join(f"<th>{e(rotulo(c))}</th>" for c in cols)
        linhas = "".join("<tr>" + "".join(f"<td>{celula(x.get(c))}</td>" for c in cols) + "</tr>" for x in v)
        return f'<table class="tabela"><thead><tr>{cab}</tr></thead><tbody>{linhas}</tbody></table>'
    if isinstance(v, dict):
        return '<table class="tabela kv">' + "".join(f"<tr><th>{e(rotulo(k))}</th><td>{celula(x)}</td></tr>" for k, x in v.items()) + "</table>"
    if isinstance(v, list):
        return ('<p class="muted">Nenhum item.</p>' if not v else "<ul>" + "".join(f"<li>{celula(x)}</li>" for x in v) + "</ul>")
    return f"<p>{celula(v)}</p>"


def bloco_extras(extras: dict | None) -> str:
    if not extras:
        return ""
    partes = [f'<div class="extra"><h5>{e(rotulo(k))}</h5>{tabela_generica(v)}</div>' for k, v in extras.items()]
    return '<div class="extras"><h4 class="sub">Dados do segmento</h4>' + "".join(partes) + "</div>"


# ---------------------------------------------------------------- issues do GitHub
def issue_md(a: dict, n: int) -> str:
    ev = a.get("evidencia") or {}
    evid = []
    if ev.get("url"):
        evid.append(f"- Onde: {ev['url']}")
    if ev.get("arquivo"):
        evid.append(f"- Arquivo: `{ev['arquivo']}{(':' + ev['linhas']) if ev.get('linhas') else ''}`")
    if ev.get("metrica"):
        evid.append(f"- Medida: {ev['metrica']}")
    trecho = f"\n```\n{ev['trecho']}\n```\n" if ev.get("trecho") else ""
    return f"""--- ISSUE {n} ---
**Título:** [{a['segmento_nome']}] {a['titulo']}
**Labels:** {a['segmento']}, severidade:{a['severidade']}, {a['prioridade']}

## Problema
{a.get('impacto_usuario', '')}

## Evidência
{chr(10).join(evid) or '- (ver relatório)'}
{trecho}
## Impacto
{a.get('impacto_negocio', '')}

## Sugestão de correção
{a.get('recomendacao', '')}

## Critérios de aceite
- [ ] O problema descrito em "Evidência" não acontece mais
- [ ] A checagem {a.get('check_id')} da análise passa na reauditoria do segmento {a['segmento_nome']}
- [ ] Nenhuma regressão visual ou funcional nas páginas afetadas

Referência: {a.get('referencia') or '-'} · Achado {a['id']}{(' (+ ' + ', '.join(a['ids_juntados']) + ')') if a.get('ids_juntados') else ''}
--- FIM ISSUE {n} ---
"""


def issue_agrupada(seg_nome: str, itens: list[dict], n: int) -> str:
    lista = "\n".join(f"- [ ] **{a['id']}** {a['titulo']}: {a.get('recomendacao', '')}" for a in itens)
    return f"""--- ISSUE {n} ---
**Título:** [{seg_nome}] Ajustes menores ({len(itens)} itens)
**Labels:** {itens[0]['segmento']}, severidade:baixa, P3

## Itens
{lista}

## Critérios de aceite
- [ ] Todos os itens acima marcados como resolvidos
--- FIM ISSUE {n} ---
"""


def gerar_issues(achados: list[dict], pasta: Path | None) -> list[str]:
    """Monta os textos das issues (que ficam dentro do HTML). Só grava arquivos se `pasta` for informada."""
    if pasta is not None:
        pasta.mkdir(parents=True, exist_ok=True)
        for antigo in pasta.glob("ISSUE-*.md"):
            antigo.unlink()
    textos, n = [], 0
    for a in achados:
        if a["severidade"] in ("critica", "alta", "media"):
            n += 1
            textos.append(issue_md(a, n))
    menores: dict[str, list] = {}
    for a in achados:
        if a["severidade"] == "baixa":
            menores.setdefault(a["segmento_nome"], []).append(a)
    for seg_nome, itens in menores.items():
        n += 1
        textos.append(issue_agrupada(seg_nome, itens, n))
    if pasta is not None:
        for i, texto in enumerate(textos, 1):
            (pasta / f"ISSUE-{i:03d}.md").write_text(texto, encoding="utf-8")
        (pasta / "todas.md").write_text("\n".join(textos), encoding="utf-8")
    return textos


# ---------------------------------------------------------------- páginas do relatório
def pag_capa(nome: str, site: str, nota, faixa_txt: str, data: str, versao: str, capa_d, capa_m, meta: dict, n_pag: int) -> str:
    dominio = re.sub(r"^https?://", "", site).strip("/")
    imgs = ""
    if capa_d or capa_m:
        imgs = ('<div class="capa-imgs">' + (f'<img class="d" src="{capa_d}" alt="Página inicial no computador">' if capa_d else "")
                + (f'<img class="m" src="{capa_m}" alt="Página inicial no celular">' if capa_m else "") + "</div>")
    return f"""
<section class="pagina capa" id="capa">
  {imgs}
  <div class="capa-texto">
    <p class="sobre">Relatório de análise do site</p>
    <h1>{e(nome)}</h1>
    <p class="url"><a href="{e(site)}">{e(dominio)}</a></p>
    <div class="hero" style="--c:{cor_nota(nota)}">
      <div class="hero-num"><span class="num">{e(nota if nota is not None else '–')}</span><span class="de">/100</span></div>
      <span class="faixa">{e(faixa_txt)}</span>
    </div>
    <p class="capa-meta">Análise {e(meta.get('modo') or 'completa')} · {n_pag} páginas · site {e((meta.get('tipo_site') or '').replace('_', ' '))}</p>
  </div>
  <div class="capa-rodape"><span>{e(data)}</span><span>Versão {e(versao)}</span></div>
</section>"""


def pag_resumo(c: dict, nota, faixa_txt: str, resumo_exec: str, n_pag: int) -> str:
    cartoes = ""
    for seg, info in c["notas_segmento"].items():
        n = info["nota"]
        crit = info["achados_por_severidade"].get("critica", 0)
        total = sum(info["achados_por_severidade"].values())
        cartoes += f"""
  <a class="card-seg" href="#seg-{e(seg)}" style="--c:{cor_nota(n)}">
    <div class="card-topo">{icone(seg)}<span class="card-nome">{e(info['nome'])}</span></div>
    <div class="card-nota"><b>{e(n if n is not None else '–')}</b>{'' if n is None else '<span>/100</span>'}</div>
    {barra(n)}
    <div class="card-rodape"><span>{e(faixa(n))}</span><span>{total} achado{'s' if total != 1 else ''}{f' · {crit} crítico' + ('s' if crit > 1 else '') if crit else ''}</span></div>
  </a>"""
    segs = len(c["notas_segmento"])
    return f"""
<section class="pagina" id="resumo">
  <h2 class="titulo-pag">{icone('resumo')} Resumo executivo</h2>
  <div class="resumo-topo">
    <div class="card-geral" style="--c:{cor_nota(nota)}">
      <span class="rot">Nota geral do site</span>
      <div class="geral-num"><b>{e(nota if nota is not None else '–')}</b><span>/100</span></div>
      {barra(nota)}
      <span class="geral-faixa">{e(faixa_txt)}</span>
    </div>
    <div class="sobre-rel">
      <h3>Sobre este relatório</h3>
      <p>Analisamos {n_pag} páginas do site em {segs} frentes: segurança, privacidade, desempenho, presença no Google e em assistentes de IA, acessibilidade, design, textos, conversão, medição de resultados, infraestrutura e posição no mercado. Cada problema encontrado traz a prova (onde está e como foi medido), o efeito para o visitante e para o negócio, e o que fazer.</p>
      <p>Cada frente recebe uma nota de 0 a 100. A nota geral é a média ponderada pelo tipo de site. Clique em um cartão para ir direto ao capítulo do segmento.</p>
    </div>
  </div>
  <div class="grade-seg">{cartoes}</div>
  <div class="diagnostico">
    <h3>Por que o site recebeu esta nota</h3>
    {md_simples(resumo_exec) if resumo_exec else '<p class="muted">Diagnóstico não informado.</p>'}
  </div>
</section>"""


def pag_inconsistencias(c: dict) -> str:
    est = c["estatisticas"]
    achados = c["achados"]
    cards_sev = "".join(f'<div class="card-num" style="--c:{cor}">{icone("alerta")}<span class="rot">{nome}</span><b>{est["por_severidade"].get(k, 0)}</b></div>'
                        for k, (nome, cor) in SEV.items() if k != "info" or est["por_severidade"].get("info"))
    cards_prazo = "".join(f'<div class="card-num" style="--c:{PRIO_COR[p]}">{icone("relogio")}<span class="rot">{p} · {PRIO[p]}</span><b>{est["por_prioridade"].get(p, 0)}</b></div>'
                          for p in ("P1", "P2", "P3"))
    linhas = "".join(
        f'<tr><td class="mono"><a href="#{e(a["id"])}">{e(a["id"])}</a></td><td><a href="#{e(a["id"])}">{e(a["titulo"])}</a></td>'
        f'<td>{e(a["segmento_nome"])}</td><td>{chip(a["severidade"])}</td><td>{pill(a["prioridade"], PRIO_COR[a["prioridade"]])}</td><td class="c">{e(a.get("esforco"))}</td></tr>'
        for a in achados)
    fortes = "".join(
        f'<tr><td>{pill("OK", COR_FORTE)}</td><td>{e(p["segmento_nome"])}</td><td><b>{e(p["titulo"])}</b></td><td class="muted">{e(p.get("evidencia"))}</td></tr>'
        for p in c.get("pontos_fortes", []))
    return f"""
<section class="pagina" id="inconsistencias">
  <h2 class="titulo-pag">{icone('alerta')} Inconsistências encontradas</h2>
  <p class="lead">{est['total_achados']} problemas encontrados, ordenados do mais grave para o menos grave. O prazo sugerido combina gravidade e esforço: o que é grave e rápido de resolver vem primeiro.</p>
  <h4 class="sub">Por gravidade</h4>
  <div class="grade-num">{cards_sev}</div>
  <h4 class="sub">Por prazo sugerido</h4>
  <div class="grade-num tres">{cards_prazo}</div>
  <table class="tabela compacta lista-achados">
    <thead><tr><th>ID</th><th>Problema</th><th>Segmento</th><th>Gravidade</th><th>Prazo</th><th>Esforço</th></tr></thead>
    <tbody>{linhas or '<tr><td colspan=6 class=muted>Nenhum problema encontrado.</td></tr>'}</tbody>
  </table>
  <p class="nota-rodape">Prazo: P1 = esta semana, P2 = este mês, P3 = próximos 90 dias. Esforço: P = horas, M = dias, G = semanas.</p>

  <h2 class="titulo-pag secundario" id="funcionando">{icone('ok')} O que está funcionando</h2>
  <table class="tabela compacta">
    <thead><tr><th>Status</th><th>Segmento</th><th>Ponto</th><th>Evidência</th></tr></thead>
    <tbody>{fortes or '<tr><td colspan=4 class=muted>Nenhum ponto forte registrado.</td></tr>'}</tbody>
  </table>
</section>"""


def pag_segmento(seg: str, info: dict, itens: list[dict], cob: dict, extras) -> str:
    cont = info["achados_por_severidade"]
    mini = "".join(f'<span class="mini" style="--c:{SEV[k][1]}"><b>{v}</b> {SEV[k][0].lower()}</span>' for k, v in cont.items() if v)
    sumario = "".join(
        f'<tr><td class="mono"><a href="#{e(a["id"])}">{e(a["id"])}</a></td><td><a href="#{e(a["id"])}">{e(a["titulo"])}</a></td>'
        f'<td>{chip(a["severidade"])}</td><td>{pill(a["prioridade"], PRIO_COR[a["prioridade"]])}</td></tr>' for a in itens)
    nv = "".join(f"<li>{e(x)}</li>" for x in cob.get("nao_verificado", []))
    na = "".join(f"<li>{e(x)}</li>" for x in cob.get("nao_aplicavel", []))
    n = info["nota"]
    return f"""
<section class="pagina segmento" id="seg-{e(seg)}">
  <div class="seg-capa" style="--c:{cor_nota(n)}">
    <div class="seg-capa-esq">
      <span class="seg-icone">{icone(seg, 'ic grande')}</span>
      <div><p class="sobre">Segmento</p><h2>{e(info['nome'])}</h2></div>
    </div>
    <div class="seg-capa-dir"><div class="seg-num"><b>{e(n if n is not None else '–')}</b>{'' if n is None else '<span>/100</span>'}</div><span class="seg-faixa">{e(faixa(n))}</span></div>
  </div>
  <p class="resumo">{e(info['resumo'])}</p>
  <div class="minis">{mini or '<span class="mini" style="--c:#059669">nenhum problema encontrado</span>'}<span class="mini neutro">peso na nota geral: {e(info['peso'])}</span></div>
  {('<h4 class="sub">' + icone('lista') + ' Sumário do segmento</h4><table class="tabela compacta sumario"><thead><tr><th>ID</th><th>Problema</th><th>Gravidade</th><th>Prazo</th></tr></thead><tbody>' + sumario + '</tbody></table>') if itens else ''}
  {bloco_extras(extras)}
  {('<h4 class="sub">Detalhamento</h4>' + ''.join(cartao_achado(a) for a in itens)) if itens else ''}
  {('<div class="cobertura"><h5>O que não foi verificado</h5><ul>' + nv + '</ul></div>') if nv else ''}
  {('<div class="cobertura"><h5>Não se aplica a este site</h5><ul>' + na + '</ul></div>') if na else ''}
</section>"""


def pag_metodo(c: dict, coleta: dict) -> str:
    meta = c["meta"]
    est = c["estatisticas"]
    ferramentas = coleta.get("ferramentas", {})
    falhas = coleta.get("falhas", [])
    lista_ferr = ", ".join(f"{k}: {'ok' if v else 'indisponível'}" for k, v in ferramentas.items()) or "-"
    pesos = "".join(f"<tr><td>{e(c['notas_segmento'][s]['nome'])}</td><td class='c'>{p}</td></tr>"
                    for s, p in c["pesos_usados"].items() if s in c["notas_segmento"])
    paginas = "".join(f"<li>{e(p.get('url'))}</li>" for p in coleta.get("paginas", []))
    tetos = "".join(f"<li>{e(t)}</li>" for t in c.get("tetos_aplicados", []))
    return f"""
<section class="pagina" id="metodologia">
  <h2 class="titulo-pag">{icone('metodo')} Metodologia</h2>
  <div class="duas">
    <div>
      <p>Os dados foram coletados uma única vez: páginas, capturas de tela em computador, tablet e celular, cabeçalhos de segurança, DNS, certificado, links, ferramentas de rastreamento e medições de velocidade e acessibilidade. Em seguida, um especialista por segmento analisou esses dados e um verificador independente conferiu os problemas mais graves.</p>
      <p>Cada problema tem um código da matriz de referência da análise, que liga a checagem às boas práticas de mercado usadas como base.</p>
      <p><b>Ferramentas:</b> {e(lista_ferr)}.{(' <b>Etapas sem dados:</b> ' + e('; '.join(f["etapa"] for f in falhas)) + '.') if falhas else ''}</p>
      {('<p><b>Limites aplicados à nota geral:</b></p><ul>' + tetos + '</ul>') if tetos else ''}
      <p class="muted">As checagens de segurança no site publicado são passivas. Os apontamentos de privacidade são indícios técnicos e não substituem avaliação jurídica. Problemas iguais apontados por segmentos diferentes foram unidos ({est['juntados_por_duplicidade']}); itens descartados na verificação: {est['descartados_na_verificacao']}.</p>
    </div>
    <div>
      <table class="tabela compacta"><thead><tr><th>Segmento</th><th>Peso ({e((meta.get('tipo_site') or '').replace('_', ' '))})</th></tr></thead><tbody>{pesos}</tbody></table>
      <h5>Páginas analisadas</h5><ul class="pequena">{paginas}</ul>
    </div>
  </div>
</section>"""


def pag_issues(issues: list[str]) -> str:
    blocos = "".join(f"<details class='issue'><summary>{e(t.splitlines()[1].replace('**Título:** ', ''))}</summary><pre>{e(t)}</pre></details>" for t in issues)
    return f"""
<section class="pagina issues" id="issues">
  <h2 class="titulo-pag">{icone('github')} Issues para o GitHub</h2>
  <p class="muted">Prontas para copiar e colar no GitHub. Esta seção só aparece no HTML, não entra no PDF.</p>
  {blocos or '<p class="muted">Nenhuma issue gerada.</p>'}
</section>"""


def montar_html(c: dict, escopo: dict, coleta: dict, resumo_exec: str, issues: list[str], saida: Path) -> str:
    meta = c["meta"]
    site = meta.get("site") or coleta.get("url_final") or ""
    data_iso = meta.get("data") or dt.date.today().isoformat()
    try:
        data = dt.date.fromisoformat(data_iso[:10]).strftime("%d/%m/%Y")
    except ValueError:
        data = data_iso
    versao = str(escopo.get("versao_relatorio") or "1.0")
    nome = nome_do_site(meta, escopo, saida)
    nota = c.get("nota_geral")
    faixa_txt = c.get("faixa") or faixa(nota)
    n_pag = len(coleta.get("paginas", [])) or meta.get("paginas") or 0
    capa_d = img_b64(saida / "coleta" / "capa" / "desktop.jpg")
    capa_m = img_b64(saida / "coleta" / "capa" / "mobile.jpg")
    css = (RAIZ / "templates" / "relatorio.css").read_text(encoding="utf-8")

    segmentos = "".join(pag_segmento(seg, info, [a for a in c["achados"] if a["segmento"] == seg],
                                     c["cobertura"].get(seg, {}), c["extras"].get(seg))
                        for seg, info in c["notas_segmento"].items())
    menu = "".join(f'<a href="#seg-{e(s)}">{e(i["nome"])}</a>' for s, i in c["notas_segmento"].items())

    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Análise do site · {e(nome)}</title><style>{css}</style></head>
<body>
<div class="barra no-print">
  <span class="barra-titulo">Relatório de análise · {e(nome)}</span>
  <nav><a href="#resumo">Resumo</a><a href="#inconsistencias">Inconsistências</a><details class="menu-seg"><summary>Segmentos</summary><div>{menu}</div></details><a href="#metodologia">Metodologia</a></nav>
  <button onclick="abrirTudo(true);window.print()">Baixar PDF</button>
</div>
<main>
{pag_capa(nome, site, nota, faixa_txt, data, versao, capa_d, capa_m, meta, n_pag)}
{pag_resumo(c, nota, faixa_txt, resumo_exec, n_pag)}
{pag_inconsistencias(c)}
{segmentos}
{pag_metodo(c, coleta)}
{pag_issues(issues)}
</main>
<script>
function abrirTudo(v) {{ document.querySelectorAll('details:not(.menu-seg)').forEach(d => d.open = v); }}
window.addEventListener('beforeprint', () => abrirTudo(true));
document.querySelectorAll('.menu-seg a').forEach(a => a.addEventListener('click', () => a.closest('details').open = false));
</script>
</body></html>"""


def gerar_pdf(html_path: Path, pdf_path: Path, titulo: str) -> None:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox"])
        pg = b.new_page()
        pg.goto(html_path.resolve().as_uri(), wait_until="load")
        pg.evaluate("document.querySelectorAll('details:not(.menu-seg)').forEach(d => d.open = true)")
        pg.emulate_media(media="print")
        rodape = (f'<div style="font-size:7.5px;width:100%;padding:0 14mm;color:#6B7280;display:flex;justify-content:space-between;font-family:Arial">'
                  f'<span>{html.escape(titulo)}</span><span>Página <span class="pageNumber"></span> de <span class="totalPages"></span></span></div>')
        pg.pdf(path=str(pdf_path), format="A4", print_background=True, display_header_footer=True,
               header_template="<div></div>", footer_template=rodape,
               margin={"top": "14mm", "bottom": "16mm", "left": "14mm", "right": "14mm"})
        b.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", required=True)
    ap.add_argument("--sem-pdf", action="store_true")
    ap.add_argument("--issues", action="store_true", help="grava também a pasta issues/ com um arquivo por issue")
    args = ap.parse_args()
    saida = Path(args.saida)
    global RAIZ_SAIDA
    RAIZ_SAIDA = saida
    c = json.loads((saida / "consolidado.json").read_text(encoding="utf-8"))
    escopo = json.loads((saida / "escopo.json").read_text(encoding="utf-8")) if (saida / "escopo.json").exists() else {}
    coleta = json.loads((saida / "coleta" / "resumo.json").read_text(encoding="utf-8")) if (saida / "coleta" / "resumo.json").exists() else {}
    resumo_exec = (saida / "resumo-executivo.md").read_text(encoding="utf-8") if (saida / "resumo-executivo.md").exists() else ""
    issues = gerar_issues(c["achados"], (saida / "issues") if args.issues else None)
    pagina = montar_html(c, escopo, coleta, resumo_exec, issues, saida)
    destino = saida / "relatorio.html"
    destino.write_text(pagina, encoding="utf-8")
    print(f"HTML: {destino}")
    fechar_navegador()
    print(f"Issues: {len(issues)} dentro do HTML" + (f" e em {saida / 'issues'}" if args.issues else ""))
    if not args.sem_pdf:
        nome = nome_do_site(c["meta"], escopo, saida)
        gerar_pdf(destino, saida / "relatorio.pdf", f"Análise do site · {nome}")
        print(f"PDF: {saida / 'relatorio.pdf'}")


if __name__ == "__main__":
    main()
