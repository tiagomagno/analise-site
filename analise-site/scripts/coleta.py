#!/usr/bin/env python3
"""
Coleta compartilhada da skill analise-site.

Visita o site uma vez e grava tudo o que os agentes de segmento precisam em
<saida>/coleta/. Nenhum agente precisa navegar de novo no site para a maior
parte das checagens.

Uso:
    python coleta.py https://exemplo.com.br --saida docs/analise/2026-10-10 --modo completa
    python coleta.py https://exemplo.com.br --saida ./analise --modo rapida --sem-lighthouse

Dependências: playwright (pip install playwright && python -m playwright install chromium).
Opcionais: Node/npx (Lighthouse e axe-core). Tudo que falhar é registrado em
coleta/resumo.json -> "falhas" e a coleta continua.

Somente leitura: o script faz requisições GET/HEAD e carrega páginas. Não envia
formulários, não testa senhas, não faz carga.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import random
import re
import shutil
import socket
import ssl
import string
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse, parse_qs, quote

try:
    from playwright.sync_api import sync_playwright, Error as PWError
except ImportError:  # pragma: no cover
    sys.exit("Playwright não instalado. Rode: pip install playwright && python -m playwright install chromium")

UA_DESKTOP = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/126.0.0.0 Safari/537.36 analise-site/1.0")
UA_MOBILE = ("Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) "
             "Chrome/126.0.0.0 Mobile Safari/537.36 analise-site/1.0")

VIEWPORTS = {"desktop": (1440, 900), "tablet": (768, 1024), "mobile": (390, 844)}
MAX_SHOT_HEIGHT = 6000
ESPERA_ABERTURA = 3.0  # segundos após o carregamento (ajustável com --espera-abertura)
PALAVRAS_PRIORIDADE = ["contato", "fale-conosco", "sobre", "quem-somos", "servico", "servicos", "produto", "produtos",
                       "preco", "precos", "planos", "orcamento", "loja", "shop", "blog", "empresa", "solucoes",
                       "contact", "about", "pricing", "services"]
EXT_ARQUIVO = re.compile(r"\.(pdf|jpe?g|png|gif|webp|svg|zip|rar|docx?|xlsx?|pptx?|mp4|mp3|avi|mov|ico|xml|txt|json)$", re.I)

FALHAS: list[dict] = []


# ---------------------------------------------------------------- utilidades
def log(msg: str) -> None:
    print(f"[coleta] {msg}", flush=True)


def falha(etapa: str, erro: Exception | str) -> None:
    texto = str(erro).split("\n")[0][:300]
    FALHAS.append({"etapa": etapa, "erro": texto})
    log(f"falhou {etapa}: {texto}")


def salvar_json(caminho: Path, dados) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")


def salvar_texto(caminho: Path, texto: str) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(texto, encoding="utf-8", errors="replace")


def mascarar(valor: str) -> str:
    valor = valor.strip()
    return (valor[:8] + "...") if len(valor) > 8 else "***"


def normalizar_url(url: str) -> str:
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    p = urlparse(url)
    caminho = p.path or "/"
    return urlunparse((p.scheme.lower(), p.netloc.lower(), caminho, "", p.query, ""))


def dominio_base(host: str) -> str:
    host = host.split(":")[0]
    return host[4:] if host.startswith("www.") else host


def mesmo_site(url: str, host: str) -> bool:
    h = urlparse(url).netloc.lower()
    return dominio_base(h) == dominio_base(host)


def slug_de(url: str) -> str:
    caminho = urlparse(url).path.strip("/")
    if not caminho:
        return "home"
    s = re.sub(r"[^a-zA-Z0-9]+", "-", caminho).strip("-").lower()
    return s[:60] or "pagina"


def limpar_link(href: str, base: str) -> str | None:
    if not href or href.startswith(("mailto:", "tel:", "javascript:", "#", "data:", "whatsapp:")):
        return None
    absoluto = urljoin(base, href)
    p = urlparse(absoluto)
    if p.scheme not in ("http", "https"):
        return None
    return urlunparse((p.scheme, p.netloc.lower(), p.path or "/", "", p.query, ""))


# ---------------------------------------------------------------- HTTP passivo
def get(req, url: str, *, redirects: int = 0, headers: dict | None = None, timeout: int = 15000):
    """GET sem seguir redirecionamento por padrão. Retorna dict ou None."""
    try:
        r = req.get(url, max_redirects=redirects, headers=headers or {}, timeout=timeout, fail_on_status_code=False)
        corpo = b""
        try:
            corpo = r.body()
        except Exception:
            pass
        return {"url": url, "status": r.status, "headers": dict(r.headers), "corpo": corpo,
                "headers_lista": r.headers_array}
    except Exception as e:  # rede, DNS, TLS
        return {"url": url, "status": None, "erro": str(e).split("\n")[0][:200], "headers": {}, "corpo": b"",
                "headers_lista": []}


def cadeia_redirecionamento(req, url: str, max_saltos: int = 8) -> list[dict]:
    cadeia = []
    atual = url
    for _ in range(max_saltos):
        r = get(req, atual)
        passo = {"url": atual, "status": r["status"]}
        if r.get("erro"):
            passo["erro"] = r["erro"]
            cadeia.append(passo)
            break
        local = r["headers"].get("location")
        if local:
            passo["location"] = urljoin(atual, local)
        cadeia.append(passo)
        if r["status"] in (301, 302, 303, 307, 308) and local:
            atual = urljoin(atual, local)
            continue
        break
    return cadeia


def coletar_http(req, url_inicial: str, pasta: Path, host: str) -> dict:
    log("HTTP: redirecionamentos, headers, arquivos padrão")
    base = dominio_base(host)
    variantes = [f"http://{base}/", f"http://www.{base}/", f"https://{base}/", f"https://www.{base}/"]
    redirects = {v: cadeia_redirecionamento(req, v) for v in variantes}
    salvar_json(pasta / "http" / "redirects.json", redirects)

    final = get(req, url_inicial, redirects=10)
    url_final = url_inicial
    cadeia = cadeia_redirecionamento(req, url_inicial)
    if cadeia and cadeia[-1].get("status") and not cadeia[-1].get("erro"):
        url_final = cadeia[-1]["url"]
    cookies = [v for k, v in [(h["name"], h["value"]) for h in final.get("headers_lista", [])] if k.lower() == "set-cookie"]
    hdr = {k.lower(): v for k, v in final["headers"].items()}
    seg = ["content-security-policy", "strict-transport-security", "x-frame-options", "x-content-type-options",
           "referrer-policy", "permissions-policy", "cross-origin-opener-policy", "cross-origin-resource-policy",
           "cross-origin-embedder-policy"]
    headers_info = {
        "url_final": url_final,
        "status": final["status"],
        "headers": hdr,
        "seguranca": {h: hdr.get(h) for h in seg},
        "ausentes": [h for h in seg[:6] if not hdr.get(h)],
        "cookies_set_cookie": [
            {"cookie": c.split(";")[0].split("=")[0],
             "httponly": "httponly" in c.lower(), "secure": "secure" in c.lower(),
             "samesite": (re.search(r"samesite=(\w+)", c, re.I).group(1) if re.search(r"samesite=(\w+)", c, re.I) else None)}
            for c in cookies],
        "servidor": hdr.get("server"), "x_powered_by": hdr.get("x-powered-by"),
        "compressao": hdr.get("content-encoding"), "cache_control": hdr.get("cache-control"),
    }
    salvar_json(pasta / "http" / "headers.json", headers_info)

    # robots, sitemap, llms
    origem = f"{urlparse(url_final).scheme}://{urlparse(url_final).netloc}"
    arquivos = {}
    robots = get(req, origem + "/robots.txt", redirects=3)
    arquivos["robots.txt"] = robots["status"]
    sitemaps = []
    if robots["status"] == 200:
        texto = robots["corpo"].decode("utf-8", "replace")
        salvar_texto(pasta / "http" / "robots.txt", texto)
        sitemaps = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", texto)
    if not sitemaps:
        sitemaps = [origem + "/sitemap.xml", origem + "/sitemap_index.xml"]
    urls_sitemap: list[str] = []
    for sm in sitemaps[:3]:
        r = get(req, sm, redirects=3)
        arquivos[sm] = r["status"]
        if r["status"] == 200:
            texto = r["corpo"].decode("utf-8", "replace")
            salvar_texto(pasta / "http" / ("sitemap-" + slug_de(sm) + ".xml"), texto[:2_000_000])
            locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", texto)
            filhos = [l for l in locs if l.endswith(".xml")]
            urls_sitemap += [l for l in locs if not l.endswith(".xml")]
            for f in filhos[:3]:
                rf = get(req, f, redirects=3)
                if rf["status"] == 200:
                    urls_sitemap += [l for l in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", rf["corpo"].decode("utf-8", "replace"))
                                     if not l.endswith(".xml")]
            break
    for nome in ["/llms.txt", "/.well-known/security.txt", "/favicon.ico", "/apple-touch-icon.png",
                 "/manifest.json", "/site.webmanifest", "/ads.txt"]:
        r = get(req, origem + nome, redirects=3)
        arquivos[nome] = r["status"]
        if nome == "/llms.txt" and r["status"] == 200:
            salvar_texto(pasta / "http" / "llms.txt", r["corpo"].decode("utf-8", "replace")[:200_000])

    # página inexistente
    aleatorio = "".join(random.choices(string.ascii_lowercase, k=10))
    r404 = get(req, f"{origem}/pagina-que-nao-existe-{aleatorio}", redirects=5)
    corpo404 = r404["corpo"].decode("utf-8", "replace")
    titulo404 = re.search(r"<title[^>]*>(.*?)</title>", corpo404, re.I | re.S)
    arquivos["teste_404"] = {"status": r404["status"], "titulo": titulo404.group(1).strip()[:120] if titulo404 else None,
                             "tamanho": len(corpo404)}
    salvar_json(pasta / "http" / "arquivos-padrao.json", {"origem": origem, "status": arquivos,
                                                         "sitemaps": sitemaps, "urls_no_sitemap": len(urls_sitemap)})
    salvar_json(pasta / "http" / "urls-sitemap.json", urls_sitemap[:5000])

    # exposição de arquivos sensíveis (GET passivo)
    log("HTTP: arquivos expostos")
    sondas = ["/.env", "/.env.local", "/.env.production", "/.git/HEAD", "/.git/config", "/.svn/entries", "/.DS_Store",
              "/backup.zip", "/site.zip", "/backup.sql", "/dump.sql", "/db.sql", "/wp-config.php.bak", "/config.php.bak",
              "/phpinfo.php", "/server-status", "/.htaccess", "/docker-compose.yml", "/package.json", "/composer.json"]
    pastas_listagem = ["/uploads/", "/wp-content/uploads/", "/images/", "/assets/", "/files/", "/backup/"]
    exposicao = []
    for s in sondas:
        r = get(req, origem + s)
        corpo = r["corpo"][:4000].decode("utf-8", "replace")
        real = False
        detalhe = None
        if r["status"] == 200:
            ct = r["headers"].get("content-type", "")
            parece_html = "<html" in corpo.lower() or "<!doctype" in corpo.lower()
            if s.startswith("/.env") and re.search(r"(?m)^[A-Z][A-Z0-9_]{2,}\s*=", corpo) and not parece_html:
                real = True
                detalhe = "variáveis: " + ", ".join(sorted(set(re.findall(r"(?m)^([A-Z][A-Z0-9_]{2,})\s*=", corpo)))[:25])
            elif s == "/.git/HEAD" and corpo.startswith("ref:"):
                real, detalhe = True, corpo.strip()[:60]
            elif s == "/.git/config" and "[core]" in corpo:
                real, detalhe = True, "[core] presente"
            elif s in ("/phpinfo.php",) and "phpinfo" in corpo.lower():
                real, detalhe = True, "página phpinfo"
            elif s == "/server-status" and "apache server status" in corpo.lower():
                real, detalhe = True, "Apache server-status"
            elif s in ("/package.json", "/composer.json") and corpo.lstrip().startswith("{") and not parece_html:
                real, detalhe = True, "arquivo de dependências público"
            elif s.endswith((".zip", ".sql", ".bak", ".DS_Store", ".yml", ".htaccess", "/entries")) and not parece_html \
                    and "text/html" not in ct:
                real, detalhe = True, f"{ct or 'tipo desconhecido'}, {len(r['corpo'])} bytes"
        exposicao.append({"caminho": s, "status": r["status"], "exposto": real, "detalhe": detalhe})
    for pl in pastas_listagem:
        r = get(req, origem + pl)
        corpo = r["corpo"][:6000].decode("utf-8", "replace")
        exposicao.append({"caminho": pl, "status": r["status"],
                          "exposto": r["status"] == 200 and ("index of /" in corpo.lower() or "<title>index of" in corpo.lower()),
                          "detalhe": "listagem de diretório" if "index of /" in corpo.lower() else None})
    salvar_json(pasta / "http" / "exposicao.json", exposicao)

    # CORS com Origin arbitrário na página principal
    rc = get(req, url_final, headers={"Origin": "https://origem-teste.invalid"})
    salvar_json(pasta / "http" / "cors.json", [{
        "url": url_final,
        "access-control-allow-origin": rc["headers"].get("access-control-allow-origin"),
        "access-control-allow-credentials": rc["headers"].get("access-control-allow-credentials"),
    }])
    return {"url_final": url_final, "origem": origem, "urls_sitemap": urls_sitemap, "headers": headers_info}


# ---------------------------------------------------------------- DNS (DNS over HTTPS)
def doh(req, nome: str, tipo: str) -> dict:
    for servidor in ("https://cloudflare-dns.com/dns-query", "https://dns.google/resolve"):
        try:
            r = req.get(f"{servidor}?name={quote(nome)}&type={tipo}&do=1",
                        headers={"accept": "application/dns-json"}, timeout=10000, fail_on_status_code=False)
            if r.status == 200:
                return r.json()
        except Exception:
            continue
    raise RuntimeError(f"DNS over HTTPS indisponível para {nome} {tipo}")


def respostas(j: dict) -> list[str]:
    return [a.get("data", "").strip('"') for a in j.get("Answer", []) or []]


def coletar_dns(req, host: str, pasta: Path) -> dict:
    log("DNS: registros, e-mail, reputação")
    dom = dominio_base(host)
    out: dict = {"dominio": dom}
    try:
        for tipo in ("A", "AAAA", "MX", "CAA", "NS"):
            out[tipo] = respostas(doh(req, dom, tipo))
        a = doh(req, dom, "A")
        out["dnssec_validado"] = bool(a.get("AD"))
        txt = respostas(doh(req, dom, "TXT"))
        out["SPF"] = [t for t in txt if t.lower().startswith("v=spf1")]
        out["TXT_verificacoes"] = [t[:120] for t in txt if any(k in t.lower() for k in
                                   ("google-site-verification", "facebook-domain-verification", "ms=", "msvalidate"))]
        out["DMARC"] = [t for t in respostas(doh(req, "_dmarc." + dom, "TXT")) if "v=dmarc1" in t.lower()]
        dkim = {}
        for sel in ["google", "selector1", "selector2", "default", "k1", "s1", "s2", "mail", "dkim", "resend",
                    "amazonses", "mandrill", "zoho", "hostinger", "locaweb"]:
            r = respostas(doh(req, f"{sel}._domainkey.{dom}", "TXT"))
            if any("p=" in x for x in r):
                dkim[sel] = True
        out["DKIM_seletores_encontrados"] = list(dkim)
        out["DKIM_observacao"] = ("Só dá para testar seletores comuns. Não encontrar não prova que o DKIM falta.")
        # listas de bloqueio (best effort; resolvedores públicos às vezes são recusados)
        listas = {}
        for zona in ("dbl.spamhaus.org", "multi.surbl.org", "multi.uribl.com"):
            try:
                j = doh(req, f"{dom}.{zona}", "A")
                ips = respostas(j)
                if not ips:
                    listas[zona] = "não listado"
                elif any(i.startswith("127.255.255.") or i == "127.0.0.1" and zona == "multi.uribl.com" for i in ips):
                    listas[zona] = f"inconclusivo (consulta recusada: {ips})"
                else:
                    listas[zona] = f"LISTADO ({ips})"
            except Exception as e:
                listas[zona] = f"erro: {e}"
        out["listas_bloqueio"] = listas
    except Exception as e:
        falha("dns", e)
        out["erro"] = str(e)
    salvar_json(pasta / "dns" / "dns.json", out)
    return out


def _certificado_entregue(nome: str, porta: int) -> dict | None:
    """Lê o certificado que o servidor entrega, sem verificar a cadeia de confiança (só para ler datas e nomes)."""
    import tempfile
    try:
        import _ssl
        ctx = ssl._create_unverified_context()
        with socket.create_connection((nome, porta), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=nome) as s:
                der, versao = s.getpeercert(True), s.version()
        with tempfile.NamedTemporaryFile("w", suffix=".pem", delete=False) as f:
            f.write(ssl.DER_cert_to_PEM_cert(der))
            caminho = f.name
        try:
            cert = _ssl._test_decode_cert(caminho)
        finally:
            os.unlink(caminho)
        cert["_versao_tls"] = versao
        return cert
    except Exception:
        return None


def _navegador_confia(browser, host: str) -> bool | None:
    """Segunda opinião: o Chromium abre o site verificando o certificado de verdade.
    True = abriu; False = recusou por causa do certificado; None = não deu para concluir."""
    if browser is None:
        return None
    ctx = browser.new_context(ignore_https_errors=False)
    try:
        ctx.new_page().goto(f"https://{host}", wait_until="commit", timeout=30000)
        return True
    except Exception as e:
        return False if "ERR_CERT" in str(e) else None
    finally:
        ctx.close()


def coletar_tls(host: str, pasta: Path, browser=None) -> dict:
    """Certificado do site. O Python do computador às vezes não monta a cadeia de confiança (antivírus que inspeciona
    HTTPS, lojas de certificados desatualizadas) e diz 'vencido' mesmo com o certificado válido. Por isso, só se afirma
    que está inválido se o certificado entregue pelo servidor estiver mesmo fora da validade/nome, ou se o navegador
    também recusar."""
    log("TLS: certificado")
    out: dict = {"host": host}
    nome, _, porta = host.partition(":")
    porta_n = int(porta or 443)
    agora = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((nome, porta_n), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=nome) as s:
                cert = s.getpeercert()
                out["versao_tls"] = s.version()
                out["emissor"] = dict(x[0] for x in cert.get("issuer", []))
                out["valido_ate"] = cert.get("notAfter")
                expira = dt.datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
                out["dias_para_expirar"] = (expira - agora).days
                out["nomes"] = [v for k, v in cert.get("subjectAltName", []) if k == "DNS"][:20]
                out["valido"] = True
    except ssl.SSLCertVerificationError as e:
        out["erro_verificacao_python"] = str(e)[:200]
        cert = _certificado_entregue(nome, porta_n)
        datas_ok = nomes_ok = None
        if cert:
            try:
                ini = dt.datetime.strptime(cert["notBefore"], "%b %d %H:%M:%S %Y %Z")
                fim = dt.datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
                datas_ok = ini <= agora <= fim
                out["valido_ate"] = cert["notAfter"]
                out["dias_para_expirar"] = (fim - agora).days
            except Exception:
                pass
            out["versao_tls"] = cert.get("_versao_tls")
            out["emissor"] = dict(x[0] for x in cert.get("issuer", []))
            out["nomes"] = [v for k, v in cert.get("subjectAltName", []) if k == "DNS"][:20]
            alvo = nome.lower()
            nomes_ok = any(n.lower() == alvo or (n.startswith("*.") and alvo.split(".", 1)[-1] == n[2:].lower())
                           for n in out["nomes"]) if out["nomes"] else None
        no_navegador = _navegador_confia(browser, host)
        out["confere_no_navegador"] = no_navegador
        if datas_ok and nomes_ok is not False and no_navegador is True:
            out["valido"] = True
            out["aviso"] = ("O Python deste computador não conseguiu verificar a cadeia do certificado (comum com antivírus que "
                            "inspeciona HTTPS ou com lista de certificados desatualizada), mas o certificado entregue pelo servidor "
                            "está dentro da validade e o navegador confia nele. Não é problema do site.")
        elif datas_ok is False or nomes_ok is False or no_navegador is False:
            out["valido"] = False
            out["erro"] = str(e)[:200]
        else:
            out["valido"] = None
            out["aviso"] = ("Não foi possível confirmar o certificado: a verificação local falhou e a segunda checagem foi "
                            "inconclusiva. Não trate como problema do site; registre como não verificado.")
    except Exception as e:
        falha("tls", e)
        out["erro"] = str(e)[:200]
    salvar_json(pasta / "tls" / "tls.json", out)
    return out


# ---------------------------------------------------------------- JS executado nas páginas
JS_DADOS = r"""
() => {
  const q = (s) => Array.from(document.querySelectorAll(s));
  const meta = (n) => { const e = document.querySelector(`meta[name="${n}"],meta[property="${n}"]`); return e ? e.content : null; };
  const vis = (el) => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
     return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && cs.opacity !== '0'; };
  const host = location.host.replace(/^www\./,'');
  const imgs = q('img').map(i => ({src: i.currentSrc || i.src, alt: i.getAttribute('alt'), tem_alt: i.hasAttribute('alt'),
      largura_attr: i.getAttribute('width'), altura_attr: i.getAttribute('height'),
      natural: [i.naturalWidth, i.naturalHeight], exibida: [Math.round(i.getBoundingClientRect().width), Math.round(i.getBoundingClientRect().height)],
      loading: i.getAttribute('loading'), fetchpriority: i.getAttribute('fetchpriority'), srcset: !!i.getAttribute('srcset')}));
  const links = q('a[href]').map(a => { let interno = false; try { interno = new URL(a.href).host.replace(/^www\./,'') === host } catch(e){}
      return {href: a.getAttribute('href'), abs: a.href, texto: (a.innerText || a.getAttribute('aria-label') || '').trim().slice(0,80),
              rel: a.getAttribute('rel'), target: a.getAttribute('target'), interno, no_menu: !!a.closest('nav,header'), no_rodape: !!a.closest('footer')}; });
  const forms = q('form').map(f => ({action: f.getAttribute('action'), method: (f.getAttribute('method')||'get').toLowerCase(),
      campos: Array.from(f.querySelectorAll('input,select,textarea')).filter(c => c.type !== 'hidden').map(c => {
        const id = c.id; const lab = (id && document.querySelector(`label[for="${CSS.escape(id)}"]`)) || c.closest('label');
        return {tag: c.tagName.toLowerCase(), tipo: c.type || null, nome: c.name || null, obrigatorio: c.required,
                tem_label: !!lab || !!c.getAttribute('aria-label') || !!c.getAttribute('aria-labelledby'),
                placeholder: c.getAttribute('placeholder'), autocomplete: c.getAttribute('autocomplete'),
                marcado_por_padrao: (c.type === 'checkbox') ? c.defaultChecked : undefined,
                rotulo: lab ? lab.innerText.trim().slice(0,120) : null}; }),
      botao: (f.querySelector('[type=submit],button') || {}).innerText || null,
      captcha: !!f.querySelector('.g-recaptcha,[data-sitekey],iframe[src*="recaptcha"],iframe[src*="hcaptcha"],.cf-turnstile')}));
  const contatos = links.filter(l => /wa\.me|api\.whatsapp\.com|whatsapp:|^tel:|^mailto:/i.test(l.href || '')).map(l => l.href);
  const og = {}; q('meta[property^="og:"]').forEach(m => og[m.getAttribute('property')] = m.content);
  const tw = {}; q('meta[name^="twitter:"]').forEach(m => tw[m.getAttribute('name')] = m.content);
  const verif = {}; ['google-site-verification','msvalidate.01','facebook-domain-verification','yandex-verification'].forEach(n => { const v = meta(n); if (v) verif[n] = v; });
  return {
    url: location.href, titulo: document.title, meta_description: meta('description'), meta_robots: meta('robots'),
    canonical: (document.querySelector('link[rel=canonical]')||{}).href || null,
    lang: document.documentElement.getAttribute('lang'), viewport: meta('viewport'), generator: meta('generator'),
    headings: q('h1,h2,h3,h4,h5,h6').map(h => ({nivel: +h.tagName[1], texto: h.innerText.trim().slice(0,150), visivel: vis(h)})),
    imagens: imgs, links, formularios: forms, contatos,
    jsonld: q('script[type="application/ld+json"]').map(s => s.textContent.trim().slice(0, 20000)),
    open_graph: og, twitter: tw,
    hreflang: q('link[rel=alternate][hreflang]').map(l => ({hreflang: l.hreflang, href: l.href})),
    verificacoes: verif,
    iframes: q('iframe').map(f => f.src).slice(0,30),
    videos: q('video').map(v => ({src: v.currentSrc || v.src, legendas: !!v.querySelector('track[kind=captions],track[kind=subtitles]'), autoplay: v.autoplay})),
    scripts: q('script[src]').map(s => ({src: s.src, async: s.async, defer: s.defer, type: s.type || null, no_head: !!s.closest('head')})),
    scripts_inline: q('script:not([src])').length,
    estilos: q('link[rel=stylesheet]').map(l => l.href),
    preloads: q('link[rel=preload],link[rel=preconnect],link[rel=dns-prefetch]').map(l => ({rel: l.rel, href: l.href, as: l.getAttribute('as')})),
    favicons: q('link[rel*=icon]').map(l => ({rel: l.rel, href: l.href, sizes: l.getAttribute('sizes')})),
    manifest: (document.querySelector('link[rel=manifest]')||{}).href || null,
    skip_link: q('a[href^="#"]').slice(0,5).some(a => /pular|skip|conteúdo|content/i.test(a.innerText)),
    landmarks: {header: q('header,[role=banner]').length, nav: q('nav,[role=navigation]').length, main: q('main,[role=main]').length, footer: q('footer,[role=contentinfo]').length},
    aria_live: q('[aria-live]').length,
    usa_reduced_motion: Array.from(document.styleSheets).some(ss => { try { return Array.from(ss.cssRules).some(r => (r.conditionText||'').includes('prefers-reduced-motion')); } catch(e) { return false; } }),
    usa_color_scheme: Array.from(document.styleSheets).some(ss => { try { return Array.from(ss.cssRules).some(r => (r.conditionText||'').includes('prefers-color-scheme')); } catch(e) { return false; } }),
    palavras: (document.body ? document.body.innerText.split(/\s+/).filter(Boolean).length : 0),
  };
}
"""

JS_LAYOUT = r"""
() => {
  const W = document.documentElement.clientWidth, H = window.innerHeight;
  const sel = (el) => el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (el.classList.length ? '.' + Array.from(el.classList).slice(0,2).join('.') : '');
  const vis = (el) => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
     return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && parseFloat(cs.opacity) > 0; };
  const estouro = [];
  for (const el of document.querySelectorAll('body *')) { const r = el.getBoundingClientRect();
    if (r.width > 0 && r.right > W + 2 && getComputedStyle(el).position !== 'fixed') { estouro.push(sel(el) + ' (+' + Math.round(r.right - W) + 'px)'); if (estouro.length >= 12) break; } }
  const clicaveis = Array.from(document.querySelectorAll('a[href],button,input[type=submit],input[type=button],[role=button]')).filter(vis);
  const pequenos = clicaveis.map(el => ({el, r: el.getBoundingClientRect()})).filter(x => x.r.width < 24 || x.r.height < 24)
     .slice(0, 15).map(x => sel(x.el) + ' "' + (x.el.innerText||x.el.getAttribute('aria-label')||'').trim().slice(0,30) + '" ' + Math.round(x.r.width) + 'x' + Math.round(x.r.height));
  const contar = (arr) => { const m = {}; arr.forEach(v => m[v] = (m[v]||0) + 1); return Object.entries(m).sort((a,b) => b[1]-a[1]).slice(0,12); };
  const textos = Array.from(document.querySelectorAll('body *')).filter(el => vis(el) && Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim().length > 1));
  const cs = textos.map(el => getComputedStyle(el));
  const btnLike = clicaveis.filter(el => el.tagName === 'BUTTON' || /btn|button|cta/i.test(el.className || '') || el.getAttribute('role') === 'button');
  const primeiraTela = Array.from(document.querySelectorAll('h1,h2,p,a,button')).filter(el => vis(el) && el.getBoundingClientRect().top < H && el.getBoundingClientRect().bottom > 0)
     .map(el => ({tag: el.tagName.toLowerCase(), texto: (el.innerText||'').trim().slice(0,120)})).filter(x => x.texto).slice(0, 30);
  const whats = Array.from(document.querySelectorAll('a[href*="wa.me"],a[href*="api.whatsapp.com"],a[href^="tel:"],a[href^="mailto:"]')).filter(vis)
     .map(el => { const r = el.getBoundingClientRect(); return {href: el.getAttribute('href'), fixo: getComputedStyle(el).position === 'fixed' || !!el.closest('[style*="fixed"]'), na_primeira_tela: r.top < H}; });
  const h1 = document.querySelector('h1'); const corpo = document.querySelector('p');
  return {
    largura: W, altura_tela: H, altura_pagina: document.documentElement.scrollHeight,
    estouro_horizontal: document.documentElement.scrollWidth > W + 2, elementos_estourando: estouro,
    alvos_pequenos: pequenos, total_clicaveis: clicaveis.length,
    fontes: contar(cs.map(s => s.fontFamily.split(',')[0].replace(/["']/g,'').trim())),
    tamanhos_fonte: contar(cs.map(s => s.fontSize)),
    cores_texto: contar(cs.map(s => s.color)),
    cores_fundo: contar(Array.from(document.querySelectorAll('body *')).filter(vis).map(el => getComputedStyle(el).backgroundColor).filter(c => c !== 'rgba(0, 0, 0, 0)')),
    h1_px: h1 ? parseFloat(getComputedStyle(h1).fontSize) : null, texto_px: corpo ? parseFloat(getComputedStyle(corpo).fontSize) : null,
    botoes_cta: btnLike.slice(0, 20).map(el => ({texto: (el.innerText||'').trim().slice(0,60), topo: Math.round(el.getBoundingClientRect().top + scrollY), na_primeira_tela: el.getBoundingClientRect().top < H})),
    primeira_tela: primeiraTela, contatos_visiveis: whats,
  };
}
"""

JS_METRICAS = r"""
() => new Promise(resolve => {
  const out = {lcp: null, lcp_elemento: null, cls: 0};
  try {
    new PerformanceObserver(l => { const e = l.getEntries().pop(); if (e) { out.lcp = Math.round(e.startTime);
      out.lcp_elemento = e.element ? (e.element.tagName.toLowerCase() + (e.element.id ? '#'+e.element.id : '') + (e.url ? ' ' + e.url.slice(0,150) : '')) : (e.url || null); } })
      .observe({type: 'largest-contentful-paint', buffered: true});
    new PerformanceObserver(l => { for (const e of l.getEntries()) if (!e.hadRecentInput) out.cls += e.value; })
      .observe({type: 'layout-shift', buffered: true});
  } catch (e) {}
  setTimeout(() => {
    const n = performance.getEntriesByType('navigation')[0] || {};
    out.cls = Math.round(out.cls * 1000) / 1000;
    out.ttfb = n.responseStart ? Math.round(n.responseStart) : null;
    out.dom_content_loaded = n.domContentLoadedEventEnd ? Math.round(n.domContentLoadedEventEnd) : null;
    out.load = n.loadEventEnd ? Math.round(n.loadEventEnd) : null;
    out.long_tasks_aviso = 'Métricas de laboratório sem limitação de CPU/rede; use Lighthouse/PSI para a nota oficial.';
    resolve(out);
  }, 1500);
})
"""

RASTREADORES = {
    "google-analytics.com": ("Google Analytics", "analytics", "EUA"),
    "analytics.google.com": ("Google Analytics", "analytics", "EUA"),
    "googletagmanager.com": ("Google Tag Manager", "gerenciador de tags", "EUA"),
    "doubleclick.net": ("Google Ads / DoubleClick", "publicidade", "EUA"),
    "googleadservices.com": ("Google Ads", "publicidade", "EUA"),
    "googlesyndication.com": ("Google AdSense", "publicidade", "EUA"),
    "facebook.net": ("Meta Pixel", "publicidade", "EUA"),
    "facebook.com": ("Meta", "publicidade", "EUA"),
    "analytics.tiktok.com": ("TikTok Pixel", "publicidade", "China/EUA"),
    "clarity.ms": ("Microsoft Clarity", "analytics/gravação de sessão", "EUA"),
    "hotjar.com": ("Hotjar", "analytics/gravação de sessão", "Malta/UE"),
    "licdn.com": ("LinkedIn Insight", "publicidade", "EUA"),
    "hs-scripts.com": ("HubSpot", "marketing", "EUA"), "hubspot.com": ("HubSpot", "marketing", "EUA"),
    "rdstation.com.br": ("RD Station", "marketing", "Brasil"), "rdstation.com": ("RD Station", "marketing", "Brasil"),
    "intercom.io": ("Intercom", "chat", "EUA"), "crisp.chat": ("Crisp", "chat", "França/UE"),
    "tawk.to": ("Tawk.to", "chat", "EUA"), "jivosite.com": ("JivoChat", "chat", "Rússia/EUA"),
    "zdassets.com": ("Zendesk", "chat", "EUA"), "posthog.com": ("PostHog", "analytics", "EUA/UE"),
    "mixpanel.com": ("Mixpanel", "analytics", "EUA"), "segment.com": ("Segment", "analytics", "EUA"),
    "pinimg.com": ("Pinterest", "publicidade", "EUA"), "ads-twitter.com": ("X/Twitter Ads", "publicidade", "EUA"),
    "cloudflareinsights.com": ("Cloudflare Web Analytics", "analytics", "EUA"),
    "fonts.googleapis.com": ("Google Fonts", "fontes", "EUA"), "fonts.gstatic.com": ("Google Fonts", "fontes", "EUA"),
    "youtube.com": ("YouTube", "vídeo", "EUA"), "vimeo.com": ("Vimeo", "vídeo", "EUA"),
    "recaptcha.net": ("reCAPTCHA", "segurança", "EUA"), "hcaptcha.com": ("hCaptcha", "segurança", "EUA"),
    "kwai.com": ("Kwai Pixel", "publicidade", "China"),
}


def classificar_terceiro(url: str, host: str):
    h = urlparse(url).netloc.lower()
    if dominio_base(h).endswith(dominio_base(host)):
        return None
    for dom, info in RASTREADORES.items():
        if h == dom or h.endswith("." + dom):
            return {"dominio": h, "servico": info[0], "categoria": info[1], "pais": info[2]}
    return {"dominio": h, "servico": None, "categoria": "outro", "pais": None}


def analisar_analytics(urls: list[str]) -> dict:
    ga4, gtm, meta, outros = {}, set(), {}, set()
    for u in urls:
        p = urlparse(u)
        qs = parse_qs(p.query)
        if re.search(r"google-analytics\.com/(g|mp)/collect|analytics\.google\.com/g/collect", u):
            tid = (qs.get("tid") or ["?"])[0]
            ev = (qs.get("en") or ["?"])[0]
            ga4.setdefault(tid, {}).setdefault(ev, 0)
            ga4[tid][ev] += 1
        if "googletagmanager.com/gtm.js" in u:
            gtm.add((qs.get("id") or ["?"])[0])
        if "googletagmanager.com/gtag/js" in u:
            ga4.setdefault((qs.get("id") or ["?"])[0], {})
        if "facebook.com/tr" in u:
            pid = (qs.get("id") or ["?"])[0]
            ev = (qs.get("ev") or ["?"])[0]
            meta.setdefault(pid, {}).setdefault(ev, 0)
            meta[pid][ev] += 1
        for k, nome in (("clarity.ms", "Microsoft Clarity"), ("hotjar", "Hotjar"), ("analytics.tiktok.com", "TikTok Pixel"),
                        ("snap.licdn.com", "LinkedIn Insight"), ("rdstation", "RD Station"), ("posthog", "PostHog"),
                        ("plausible.io", "Plausible"), ("matomo", "Matomo"), ("cloudflareinsights", "Cloudflare Analytics")):
            if k in u:
                outros.add(nome)
    return {"ga4": ga4, "gtm": sorted(gtm), "meta_pixel": meta, "outros": sorted(outros)}


# ---------------------------------------------------------------- páginas
def escolher_paginas(url_final: str, links_home: list[str], urls_sitemap: list[str], host: str, n: int) -> list[str]:
    candidatos = []
    vistos = {re.sub(r"/index\.(html?|php)$", "", urlparse(url_final).path).rstrip("/") or "/"}
    for u in links_home + urls_sitemap:
        lu = limpar_link(u, url_final)
        if not lu or not mesmo_site(lu, host) or EXT_ARQUIVO.search(urlparse(lu).path):
            continue
        caminho = re.sub(r"/index\.(html?|php)$", "", urlparse(lu).path).rstrip("/") or "/"
        if caminho in vistos:
            continue
        vistos.add(caminho)
        candidatos.append(lu)

    def pontos(u: str) -> float:
        c = urlparse(u).path.lower()
        p = 0.0
        if any(k in c for k in PALAVRAS_PRIORIDADE):
            p += 10
        p -= c.count("/") * 1.5
        if u in links_home:
            p += 3
        return p

    candidatos.sort(key=pontos, reverse=True)
    escolhidos, primeiros = [], set()
    for u in candidatos:  # diversidade pelo primeiro segmento do caminho
        seg = (urlparse(u).path.strip("/").split("/") or [""])[0]
        if seg in primeiros and len(candidatos) > n * 2:
            continue
        primeiros.add(seg)
        escolhidos.append(u)
        if len(escolhidos) >= n - 1:
            break
    return [url_final] + escolhidos


def rolar_ate_o_fim(page) -> None:
    try:
        page.evaluate("""async () => { const h = document.documentElement.scrollHeight; for (let y = 0; y < Math.min(h, 12000); y += 700) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 120)); } window.scrollTo(0, 0); }""")
        page.wait_for_timeout(400)
    except Exception:
        pass


def abrir(page, url: str) -> int | None:
    resp = page.goto(url, wait_until="load", timeout=45000)
    try:
        page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass
    # telas de abertura/animações de entrada: espera antes de qualquer captura
    page.wait_for_timeout(int(ESPERA_ABERTURA * 1000))
    return resp.status if resp else None


def screenshot(page, caminho: Path, largura: int) -> None:
    # animações de entrada por rolagem deixam faixas em branco na página inteira:
    # pede movimento reduzido (sites que respeitam mostram tudo) e rola de novo
    try:
        page.emulate_media(reduced_motion="reduce")
        rolar_ate_o_fim(page)
        page.wait_for_timeout(600)
    except Exception:
        pass
    altura = page.evaluate("document.documentElement.scrollHeight")
    page.screenshot(path=str(caminho), full_page=True, clip={"x": 0, "y": 0, "width": largura, "height": min(altura, MAX_SHOT_HEIGHT)})
    try:
        page.emulate_media(reduced_motion="no-preference")
    except Exception:
        pass


def coletar_pagina(browser, req, url: str, pasta_pag: Path, host: str, axe_js: str | None) -> dict:
    pasta_pag.mkdir(parents=True, exist_ok=True)
    info: dict = {"url": url, "slug": pasta_pag.name}
    bruto = get(req, url, redirects=5)
    info["status_http"] = bruto["status"]
    salvar_texto(pasta_pag / "html-bruto.html", bruto["corpo"].decode("utf-8", "replace"))

    # ---- desktop: dados, rede, métricas, console
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, user_agent=UA_DESKTOP, ignore_https_errors=True, locale="pt-BR")
    page = ctx.new_page()
    requisicoes, console = [], []
    page.on("request", lambda r: requisicoes.append(r))
    page.on("console", lambda m: console.append({"tipo": m.type, "texto": m.text[:300]}) if m.type in ("error", "warning") else None)
    page.on("pageerror", lambda e: console.append({"tipo": "pageerror", "texto": str(e)[:300]}))
    t0 = time.time()
    info["status"] = abrir(page, url)
    info["tempo_carregamento_s"] = round(time.time() - t0, 2)
    metricas = page.evaluate(JS_METRICAS)
    rolar_ate_o_fim(page)
    dados = page.evaluate(JS_DADOS)
    salvar_json(pasta_pag / "dados.json", dados)
    salvar_texto(pasta_pag / "html-renderizado.html", page.content())
    texto = page.evaluate("document.body ? document.body.innerText : ''")
    salvar_texto(pasta_pag / "texto.md", f"# {dados.get('titulo') or ''}\nURL: {url}\n\n{texto}")
    layout = {"desktop": page.evaluate(JS_LAYOUT)}
    screenshot(page, pasta_pag / "desktop.png", 1440)

    if axe_js:
        try:
            page.add_script_tag(content=axe_js)
            axe = page.evaluate("""async () => { const r = await axe.run(document, {resultTypes: ['violations']});
                return r.violations.map(v => ({id: v.id, impacto: v.impact, descricao: v.help, wcag: v.tags.filter(t => /wcag/.test(t)),
                   ocorrencias: v.nodes.length, exemplos: v.nodes.slice(0,3).map(n => ({alvo: n.target.join(' '), html: n.html.slice(0,200)}))})); }""")
            salvar_json(pasta_pag / "axe.json", axe)
            info["axe_violacoes"] = len(axe)
        except Exception as e:
            falha(f"axe {url}", e)

    # tablet: mesmo contexto, outra largura
    page.set_viewport_size({"width": 768, "height": 1024})
    page.wait_for_timeout(600)
    layout["tablet"] = page.evaluate(JS_LAYOUT)
    screenshot(page, pasta_pag / "tablet.png", 768)

    rede = []
    for r in requisicoes:
        try:
            resp = r.response()
            tam = r.sizes().get("responseBodySize") if resp else None
            rede.append({"url": r.url[:400], "tipo": r.resource_type, "metodo": r.method,
                         "status": resp.status if resp else None, "bytes": tam,
                         "content_type": (resp.headers.get("content-type") if resp else None),
                         "cache_control": (resp.headers.get("cache-control") if resp else None),
                         "encoding": (resp.headers.get("content-encoding") if resp else None),
                         "terceiro": classificar_terceiro(r.url, host)})
        except Exception:
            rede.append({"url": r.url[:400], "tipo": r.resource_type, "status": None})
    salvar_json(pasta_pag / "rede.json", rede)
    salvar_json(pasta_pag / "console.json", console)
    ctx.close()

    # ---- mobile: layout, primeira tela
    mctx = browser.new_context(viewport={"width": 390, "height": 844}, user_agent=UA_MOBILE, is_mobile=True, has_touch=True,
                               device_scale_factor=1, ignore_https_errors=True, locale="pt-BR")
    mpage = mctx.new_page()
    abrir(mpage, url)
    mpage.screenshot(path=str(pasta_pag / "dobra-mobile.png"))
    rolar_ate_o_fim(mpage)
    layout["mobile"] = mpage.evaluate(JS_LAYOUT)
    screenshot(mpage, pasta_pag / "mobile.png", 390)
    mctx.close()
    salvar_json(pasta_pag / "layout.json", layout)

    # resumo da rede
    por_tipo: dict = {}
    for r in rede:
        t = r.get("tipo") or "outro"
        por_tipo.setdefault(t, {"qtd": 0, "bytes": 0})
        por_tipo[t]["qtd"] += 1
        por_tipo[t]["bytes"] += r.get("bytes") or 0
    pesadas = sorted([r for r in rede if (r.get("bytes") or 0) > 150_000], key=lambda r: -(r.get("bytes") or 0))[:15]
    terceiros = {}
    for r in rede:
        t = r.get("terceiro")
        if t:
            terceiros.setdefault(t["dominio"], {**t, "requisicoes": 0})
            terceiros[t["dominio"]]["requisicoes"] += 1
    info.update({
        "titulo": dados.get("titulo"),
        "metricas_lab": metricas,
        "requisicoes": len(rede), "bytes_total": sum((r.get("bytes") or 0) for r in rede),
        "por_tipo": por_tipo, "recursos_pesados": [{"url": r["url"], "bytes": r["bytes"], "tipo": r["tipo"]} for r in pesadas],
        "terceiros": list(terceiros.values()),
        "erros_console": len([c for c in console if c["tipo"] in ("error", "pageerror")]),
        "links_internos": [l["abs"] for l in dados.get("links", []) if l.get("interno")],
        "links_externos": [l["abs"] for l in dados.get("links", []) if not l.get("interno") and l.get("abs", "").startswith("http")],
        "urls_rede": [r["url"] for r in rede],
    })
    return info


# ---------------------------------------------------------------- consentimento (LGPD)
PADRAO_ACEITAR = re.compile(r"^\s*(aceitar|aceito|aceitar todos|aceitar tudo|concordo|permitir|permitir todos|ok|entendi|ok, entendi|accept|accept all|allow all|agree|got it|prosseguir)\s*!?\s*$", re.I)
PADRAO_RECUSAR = re.compile(r"(recus|rejeit|reject|negar|decline|apenas (os )?necess|somente (os )?necess|only necessary)", re.I)


def coletar_consentimento(browser, url: str, host: str, pasta: Path) -> dict:
    log("Privacidade: antes e depois do consentimento")
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, user_agent=UA_DESKTOP, ignore_https_errors=True, locale="pt-BR")
    page = ctx.new_page()
    reqs: list[str] = []
    page.on("request", lambda r: reqs.append(r.url))
    abrir(page, url)
    page.wait_for_timeout(2500)
    antes_urls = list(reqs)
    antes_cookies = ctx.cookies()
    # espera o banner aparecer (muitos só surgem após 1 a 6 s) e o localiza pelo botão de aceitar/recusar,
    # não pelo texto: rodapés que citam "privacidade" ou "cookies" não podem ser confundidos com o banner
    js_banner = r"""([aceitar, recusar]) => {
        const re1 = new RegExp(aceitar, 'i'), re2 = new RegExp(recusar, 'i');
        const visivel = (e) => { const r = e.getBoundingClientRect(); const st = getComputedStyle(e);
            return r.width > 0 && r.height > 0 && st.visibility !== 'hidden' && st.display !== 'none'; };
        const botoes = Array.from(document.querySelectorAll('button,[role=button],a')).filter(visivel);
        const alvo = botoes.find(b => re1.test((b.innerText || '').trim()));
        if (!alvo) return null;
        let e = alvo.parentElement;
        while (e && e.parentElement && (e.innerText || '').length < 60) e = e.parentElement;
        if (!e) return null;
        const nomes = Array.from(e.querySelectorAll('button,[role=button],a')).filter(visivel).map(b => (b.innerText || '').trim()).filter(Boolean).slice(0, 10);
        return {texto: (e.innerText || '').trim().slice(0, 600), botoes: nomes}; }"""
    banner = None
    for _ in range(8):
        banner = page.evaluate(js_banner, [PADRAO_ACEITAR.pattern, PADRAO_RECUSAR.pattern])
        if banner:
            break
        page.wait_for_timeout(1000)
    if banner is None:
        log("Privacidade: banner de cookies não detectado (registrado em consentimento.json)")
    clicou = None
    if banner:
        for texto_botao in banner.get("botoes", []):
            if PADRAO_ACEITAR.match(texto_botao):
                try:
                    page.get_by_role("button", name=texto_botao, exact=True).first.click(timeout=3000)
                except Exception:
                    try:
                        page.get_by_text(texto_botao, exact=True).first.click(timeout=3000)
                    except Exception:
                        continue
                clicou = texto_botao
                break
    page.wait_for_timeout(3500)
    depois_urls = reqs[len(antes_urls):]
    depois_cookies = ctx.cookies()
    ctx.close()

    def resumo(urls):
        vistos = {}
        for u in urls:
            t = classificar_terceiro(u, host)
            if t:
                vistos.setdefault(t["dominio"], t)
        return list(vistos.values())

    def resumo_cookies(cs):
        return [{"nome": c["name"], "dominio": c["domain"], "httponly": c.get("httpOnly"), "secure": c.get("secure"),
                 "samesite": c.get("sameSite"), "expira": c.get("expires")} for c in cs]

    antes = {"terceiros": resumo(antes_urls), "cookies": resumo_cookies(antes_cookies),
             "analytics": analisar_analytics(antes_urls)}
    depois = {"botao_clicado": clicou, "terceiros_novos": resumo(depois_urls),
              "cookies": resumo_cookies(depois_cookies), "analytics_novos": analisar_analytics(depois_urls)}
    out = {"banner": banner, "banner_detectado": bool(banner),
           "aviso": None if banner else "Nenhum banner com botão de aceitar foi detectado em 8 s; não conclua que não há banner, confira no código.",
           "tem_opcao_recusar": bool(banner and any(PADRAO_RECUSAR.search(b) for b in banner.get("botoes", []))),
           "antes": antes, "depois": depois}
    salvar_json(pasta / "privacidade" / "consentimento.json", out)
    return out


# ---------------------------------------------------------------- JS público: segredos e source maps
PADROES_SEGREDO = [
    ("Chave AWS", r"AKIA[0-9A-Z]{16}", "critica"),
    ("Stripe secreta", r"sk_live_[0-9a-zA-Z]{24,}", "critica"),
    ("Stripe restrita", r"rk_live_[0-9a-zA-Z]{24,}", "alta"),
    ("Anthropic", r"sk-ant-[A-Za-z0-9_\-]{20,}", "critica"),
    ("OpenAI", r"sk-(?:proj-)?[A-Za-z0-9_\-]{32,}", "critica"),
    ("GitHub token", r"(?:ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{40,})", "critica"),
    ("Slack token", r"xox[baprs]-[A-Za-z0-9\-]{10,}", "alta"),
    ("Chave privada", r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", "critica"),
    ("Chave Google (pode ser pública)", r"AIza[0-9A-Za-z_\-]{35}", "info"),
    ("Mercado Pago access token", r"APP_USR-[0-9]{10,}-[0-9]{6}-[a-f0-9]{32}-[0-9]{6,}", "critica"),
]


def jwt_service_role(texto: str) -> list[str]:
    achados = []
    for tok in set(re.findall(r"eyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}", texto)):
        try:
            carga = tok.split(".")[1]
            carga += "=" * (-len(carga) % 4)
            j = json.loads(base64.urlsafe_b64decode(carga))
            if j.get("role") == "service_role":
                achados.append(tok)
        except Exception:
            continue
    return achados


def coletar_js_publico(req, paginas: list[dict], host: str, pasta: Path) -> None:
    log("JavaScript público: segredos e source maps")
    scripts = []
    for p in paginas:
        for u in p.get("urls_rede", []):
            if urlparse(u).path.endswith((".js", ".mjs")) and mesmo_site(u, host):
                scripts.append(u)
        bruto = (pasta / "paginas" / p["slug"] / "html-renderizado.html")
        if bruto.exists():
            scripts.append(("inline", p["slug"], bruto.read_text(encoding="utf-8", errors="replace")))
    vistos, segredos, mapas = set(), [], []
    for s in scripts[:60]:
        if isinstance(s, tuple):
            origem, texto = f"inline em paginas/{s[1]}", s[2]
        else:
            if s in vistos:
                continue
            vistos.add(s)
            r = get(req, s, redirects=3, timeout=20000)
            if r["status"] != 200:
                continue
            texto = r["corpo"][:6_000_000].decode("utf-8", "replace")
            origem = s
            m = re.search(r"//[#@]\s*sourceMappingURL=(\S+)\s*$", texto[-500:])
            mapa_url = urljoin(s, m.group(1)) if m and not m.group(1).startswith("data:") else s + ".map"
            rm = get(req, mapa_url, redirects=2)
            mapas.append({"script": s, "mapa": mapa_url, "status": rm["status"],
                          "publico": rm["status"] == 200 and rm["corpo"][:200].lstrip().startswith(b"{"),
                          "referenciado_no_js": bool(m)})
        for nome, padrao, sev in PADROES_SEGREDO:
            for mt in list(dict.fromkeys(re.findall(padrao, texto)))[:5]:
                segredos.append({"tipo": nome, "severidade_sugerida": sev, "onde": origem, "valor_mascarado": mascarar(mt)})
        for tok in jwt_service_role(texto):
            segredos.append({"tipo": "JWT Supabase service_role", "severidade_sugerida": "critica", "onde": origem,
                             "valor_mascarado": mascarar(tok)})
    salvar_json(pasta / "http" / "segredos-bundle.json", segredos)
    salvar_json(pasta / "http" / "source-maps.json", mapas)


# ---------------------------------------------------------------- links e contatos
def coletar_links(req, paginas: list[dict], pasta: Path, limite_int: int, limite_ext: int) -> None:
    log("Links: internos, externos e botões de contato")
    internos, externos, origem_link = [], [], {}
    for p in paginas:
        for u in p.get("links_internos", []):
            lu = limpar_link(u, p["url"])
            if lu and lu not in origem_link:
                origem_link[lu] = p["url"]
                internos.append(lu)
        for u in p.get("links_externos", []):
            lu = limpar_link(u, p["url"])
            if lu and lu not in origem_link:
                origem_link[lu] = p["url"]
                externos.append(lu)
    resultado = []
    for u in internos[:limite_int]:
        cadeia = cadeia_redirecionamento(req, u, max_saltos=6)
        final = cadeia[-1] if cadeia else {}
        resultado.append({"url": u, "encontrado_em": origem_link[u], "interno": True, "status_final": final.get("status"),
                          "saltos": len(cadeia) - 1, "erro": final.get("erro")})
    for u in externos[:limite_ext]:
        r = get(req, u, redirects=6, timeout=12000)
        resultado.append({"url": u, "encontrado_em": origem_link[u], "interno": False, "status_final": r["status"],
                          "erro": r.get("erro")})
    salvar_json(pasta / "links" / "links.json", {
        "verificados": resultado,
        "quebrados": [r for r in resultado if (r["status_final"] or 0) >= 400],
        "sem_resposta": [r for r in resultado if r["status_final"] is None],
        "observacao": "sem_resposta = erro de rede, DNS ou tempo esgotado. Pode ser bloqueio do servidor ao robô; confirmar antes de chamar de quebrado.",
        "cadeias": [r for r in resultado if r.get("saltos", 0) >= 2],
        "nao_verificados": max(0, len(internos) - limite_int) + max(0, len(externos) - limite_ext),
    })

    # contatos
    contatos = []
    vistos = set()
    for p in paginas:
        dados = json.loads((pasta / "paginas" / p["slug"] / "dados.json").read_text(encoding="utf-8"))
        layout = json.loads((pasta / "paginas" / p["slug"] / "layout.json").read_text(encoding="utf-8"))
        visiveis_mobile = {c["href"] for c in layout["mobile"].get("contatos_visiveis", [])}
        for href in dados.get("contatos", []):
            chave = (href, p["slug"])
            if chave in vistos:
                continue
            vistos.add(chave)
            item = {"pagina": p["url"], "href": href, "visivel_no_celular": href in visiveis_mobile or any(href.endswith(v) for v in visiveis_mobile)}
            if re.search(r"wa\.me|api\.whatsapp\.com|whatsapp:", href, re.I):
                numero = re.search(r"wa\.me/(\+?\d+)", href) or re.search(r"phone=(\+?\d+)", href)
                digitos = re.sub(r"\D", "", numero.group(1)) if numero else ""
                txt = parse_qs(urlparse(href).query).get("text", [None])[0]
                item.update({"tipo": "whatsapp", "numero": digitos or None,
                             "numero_valido_br": bool(re.fullmatch(r"55\d{10,11}", digitos)),
                             "mensagem_padrao": txt})
                if href.startswith("http"):
                    r = get(req, href, redirects=5, timeout=12000)
                    item["status_link"] = r["status"]
            elif href.lower().startswith("tel:"):
                d = re.sub(r"\D", "", href)
                item.update({"tipo": "telefone", "numero": d, "formato_ok": 10 <= len(d) <= 13})
            elif href.lower().startswith("mailto:"):
                em = href[7:].split("?")[0]
                item.update({"tipo": "email", "email": em, "formato_ok": bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", em))})
            contatos.append(item)
    formularios = []
    for p in paginas:
        dados = json.loads((pasta / "paginas" / p["slug"] / "dados.json").read_text(encoding="utf-8"))
        for f in dados.get("formularios", []):
            formularios.append({"pagina": p["url"], **f})
    salvar_json(pasta / "links" / "contatos.json", {"links_contato": contatos, "formularios": formularios,
                                                    "observacao": "Formulários não são enviados pela coleta. Envio real só com autorização do cliente."})


# ---------------------------------------------------------------- reputação
def coletar_reputacao(browser, host: str, pasta: Path) -> None:
    log("Reputação: Google Transparency Report (Navegação segura)")
    dom = dominio_base(host)
    out = {"dominio": dom, "fonte": f"https://transparencyreport.google.com/safe-browsing/search?url={dom}&hl=pt-BR"}
    try:
        ctx = browser.new_context(locale="pt-BR")
        page = ctx.new_page()
        page.goto(out["fonte"], wait_until="load", timeout=30000)
        page.wait_for_timeout(6000)
        texto = page.evaluate("document.body.innerText")[:3000]
        out["texto"] = texto
        t = texto.lower()
        if "nenhum conteúdo não seguro" in t or "no unsafe content found" in t:
            out["situacao"] = "limpo"
        elif "não seguro" in t or "perigos" in t or "unsafe" in t or "dangerous" in t:
            out["situacao"] = "atenção: ler o texto"
        else:
            out["situacao"] = "inconclusivo"
        ctx.close()
    except Exception as e:
        out["situacao"] = "não verificado"
        out["erro"] = str(e)[:200]
        falha("reputacao", e)
    salvar_json(pasta / "reputacao" / "safe-browsing.json", out)


# ---------------------------------------------------------------- Lighthouse, PSI, axe
def preparar_axe(pasta_tmp: Path) -> str | None:
    if not shutil.which("npm"):
        return None
    try:
        subprocess.run(["npm", "install", "--no-save", "--silent", "--prefix", str(pasta_tmp), "axe-core@4"],
                       check=True, timeout=180, capture_output=True, shell=(os.name == "nt"))
        arq = pasta_tmp / "node_modules" / "axe-core" / "axe.min.js"
        return arq.read_text(encoding="utf-8") if arq.exists() else None
    except Exception as e:
        falha("axe-core (instalação)", e)
        return None


def rodar_lighthouse(url: str, destino: Path, chrome: str, form_factor: str) -> dict | None:
    if not shutil.which("npx"):
        return None
    destino.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["npx", "-y", "lighthouse@12", url, "--output=json", f"--output-path={destino}", "--quiet",
           "--chrome-flags=--headless=new --no-sandbox --disable-gpu --disable-extensions", "--locale=pt-BR", "--max-wait-for-load=45000"]
    if form_factor == "desktop":
        cmd.append("--preset=desktop")
    env = {**os.environ, "CHROME_PATH": chrome}
    try:
        subprocess.run(cmd, check=True, timeout=240, capture_output=True, env=env, shell=(os.name == "nt"))
        return resumir_lighthouse(json.loads(destino.read_text(encoding="utf-8")))
    except Exception as e:
        falha(f"lighthouse {form_factor} {url}", e)
        return None


def resumir_lighthouse(lh: dict) -> dict:
    cats = {k: (round(v["score"] * 100) if v.get("score") is not None else None) for k, v in lh.get("categories", {}).items()}
    a = lh.get("audits", {})

    def num(k):
        return a.get(k, {}).get("numericValue")

    metricas = {"LCP_ms": num("largest-contentful-paint"), "CLS": num("cumulative-layout-shift"),
                "TBT_ms": num("total-blocking-time"), "FCP_ms": num("first-contentful-paint"),
                "SI_ms": num("speed-index"), "TTFB_ms": num("server-response-time")}
    oportunidades = []
    for k, v in a.items():
        d = v.get("details") or {}
        ganho = d.get("overallSavingsMs") or 0
        if v.get("score") is not None and v["score"] < 0.9 and (ganho > 0 or d.get("overallSavingsBytes")):
            oportunidades.append({"id": k, "titulo": v.get("title"), "ganho_ms": round(ganho),
                                  "ganho_bytes": d.get("overallSavingsBytes"), "valor": v.get("displayValue")})
    oportunidades.sort(key=lambda x: -(x["ganho_ms"] or 0))
    falhas_por_cat = {}
    for cid, cat in lh.get("categories", {}).items():
        falhas_por_cat[cid] = [{"id": r["id"], "titulo": a.get(r["id"], {}).get("title"),
                                "itens": len((a.get(r["id"], {}).get("details") or {}).get("items", []) or [])}
                               for r in cat.get("auditRefs", []) if a.get(r["id"], {}).get("score") == 0][:25]
    # antivírus que injeta scripts na página falseia a nota; avisa em vez de deixar passar
    suspeitos = ("kaspersky", "kis.v2.scr", "avast", "avg.com", "bitdefender", "norton", "mcafee", "eset.com", "webroot")
    itens_rede = (a.get("network-requests", {}).get("details") or {}).get("items", []) or []
    contaminado = sorted({i.get("url", "")[:120] for i in itens_rede if any(x in i.get("url", "").lower() for x in suspeitos)})
    return {"contaminado_por_antivirus": contaminado or None,
            "aviso": ("Scripts de antivírus apareceram na medição; não use estas notas como medida do site. Rode de novo com o antivírus pausado ou em outra máquina." if contaminado else None),
            "categorias": cats, "metricas": metricas, "oportunidades": oportunidades[:15], "falhas": falhas_por_cat,
            "elemento_lcp": ((a.get("largest-contentful-paint-element", {}).get("details") or {}).get("items") or [{}])[0] if a.get("largest-contentful-paint-element") else None}


def _ler_relatorio_pagespeed(texto: str) -> dict:
    """Extrai notas, métricas de laboratório, dados de campo e recomendações do texto do relatório (em inglês)."""
    out: dict = {"categorias": {}, "metricas_lab": {}, "campo": None, "recomendacoes": []}
    for nota, nome in re.findall(r"\n(\d{1,3})\n(Performance|Accessibility|Best Practices|SEO)\n", texto):
        out["categorias"].setdefault(nome, int(nota))
    m = re.search(r"METRICS\nExpand view\n(.*?)Captured at", texto, re.S)
    if m:
        linhas = [x.strip() for x in m.group(1).splitlines() if x.strip()]
        for i in range(0, len(linhas) - 1, 2):
            out["metricas_lab"][linhas[i]] = linhas[i + 1]
    campo = re.search(r"Discover what your real users are experiencing\n(.*?)Diagnose performance issues", texto, re.S)
    if campo:
        bruto = campo.group(1).strip()
        out["campo"] = None if bruto.startswith("No Data") else bruto[:3000]
    for secao in ("INSIGHTS", "DIAGNOSTICS"):
        m = re.search(secao + r"\n(.*?)(?:\n(?:DIAGNOSTICS|PASSED AUDITS|These insights|More information)|$)", texto, re.S)
        if m:
            out["recomendacoes"] += [x.strip() for x in m.group(1).splitlines() if "Est savings" in x or "found" in x]
    return out


def rodar_pagespeed_web(p, alvos: list[tuple[str, str, str]], pasta: Path) -> dict | None:
    """Mede pelo site pagespeed.web.dev, como uma pessoa faria no navegador. O teste roda nos servidores do
    Google (sem influência de antivírus ou do computador local) e traz dados de campo quando o site tem tráfego.
    Não precisa de chave. alvos = [(slug, url, mobile|desktop)]."""
    ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
          "Chrome/141.0.0.0 Safari/537.36")
    out: dict = {}
    br = p.chromium.launch(args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
    try:
        for slug, url, estrategia in alvos:
            log(f"PageSpeed (site do Google) {estrategia}: {url}")
            ctx = br.new_context(viewport={"width": 1366, "height": 900}, locale="pt-BR", user_agent=ua)
            ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
            pg = ctx.new_page()
            chave = f"{slug}-{estrategia}"
            try:
                pg.goto("https://pagespeed.web.dev/analysis?url=" + quote(url, safe="") + f"&form_factor={estrategia}&hl=en",
                        wait_until="load", timeout=60000)
                texto, pronto = "", False
                for _ in range(45):
                    pg.wait_for_timeout(3000)
                    texto = pg.inner_text("body")
                    if "Captured at" in texto:
                        pronto = True
                        break
                    if "Unable to" in texto or "unusual traffic" in texto.lower() or "captcha" in texto.lower():
                        break
                if not pronto:
                    falha(f"pagespeed web {chave}", "o site do PageSpeed não devolveu o relatório (limite, bloqueio ou erro)")
                    continue
                salvar_texto(pasta / "psi" / f"web-{chave}.txt", texto)
                pg.screenshot(path=str(pasta / "psi" / f"web-{chave}.png"), full_page=False)
                dados = _ler_relatorio_pagespeed(texto)
                dados["fonte"] = "pagespeed.web.dev"
                dados["url"] = url
                out[chave] = dados
            except Exception as e:
                falha(f"pagespeed web {chave}", e)
            finally:
                ctx.close()
    finally:
        br.close()
    if out:
        salvar_json(pasta / "psi" / "resumo-psi.json", out)
    return out or None


def rodar_psi(req, url: str, pasta: Path) -> dict | None:
    """Dados de campo (usuários reais, CrUX) pelo PageSpeed Insights. Só roda com PSI_API_KEY:
    sem chave a cota diária do Google é zero (HTTP 429), então não vale tentar."""
    chave = os.environ.get("PSI_API_KEY")
    if not chave:
        return None
    log("PageSpeed Insights (dados de campo do Chrome, quando houver)")
    out = {}
    for estrategia in ("mobile", "desktop"):
        api = ("https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=" + quote(url, safe="") +
               f"&strategy={estrategia}&locale=pt_BR&category=performance&category=accessibility&category=seo&category=best-practices"
               "&key=" + quote(chave, safe=""))
        try:
            r = req.get(api, timeout=120000, fail_on_status_code=False)
            if r.status != 200:
                falha(f"psi {estrategia}", f"HTTP {r.status}")
                continue
            j = r.json()
            salvar_json(pasta / "psi" / f"psi-{estrategia}.json", j)
            campo = j.get("loadingExperience", {})
            out[estrategia] = {
                "campo_pagina": {k: v.get("percentile") for k, v in (campo.get("metrics") or {}).items()},
                "campo_categoria": campo.get("overall_category"),
                "campo_origem": {k: v.get("percentile") for k, v in ((j.get("originLoadingExperience") or {}).get("metrics") or {}).items()},
                "lighthouse": resumir_lighthouse(j.get("lighthouseResult", {})) if j.get("lighthouseResult") else None,
            }
        except Exception as e:
            falha(f"psi {estrategia}", e)
    if out:
        salvar_json(pasta / "psi" / "resumo-psi.json", out)
    return out or None


# ---------------------------------------------------------------- stack
ASSINATURAS = [
    ("WordPress", r"wp-content|wp-includes"), ("Elementor", r"elementor"), ("WooCommerce", r"woocommerce"),
    ("Next.js", r"__NEXT_DATA__|/_next/"), ("Nuxt", r"__NUXT__|/_nuxt/"), ("Astro", r"astro-island|data-astro"),
    ("Gatsby", r"___gatsby"), ("SvelteKit", r"__sveltekit|/_app/immutable"), ("Angular", r"ng-version"),
    ("React", r"data-reactroot|react-dom"), ("Vue", r"data-v-[0-9a-f]{6,}|__vue"), ("Shopify", r"cdn\.shopify\.com"),
    ("Wix", r"wixstatic|_wix"), ("Squarespace", r"squarespace"), ("Webflow", r"webflow"), ("Nuvemshop", r"nuvemshop|d26lpennugtm8s"),
    ("Tray", r"tray\.com\.br"), ("Loja Integrada", r"lojaintegrada"), ("VTEX", r"vtex"), ("Framer", r"framerusercontent"),
    ("Lovable", r"lovable"), ("Hostinger Website Builder", r"zyrosite|hostinger"), ("Tailwind CSS", r"\b(?:tw-|tailwind)"),
    ("Bootstrap", r"bootstrap(\.min)?\.(css|js)"), ("jQuery", r"jquery(\.min)?\.js"),
]


def detectar_stack(paginas: list[dict], headers: dict, pasta: Path) -> dict:
    html = ""
    home = pasta / "paginas" / paginas[0]["slug"] / "html-renderizado.html"
    if home.exists():
        html = home.read_text(encoding="utf-8", errors="replace")
    encontrados = [nome for nome, pad in ASSINATURAS if re.search(pad, html, re.I)]
    h = headers.get("headers", {})
    hospedagem = []
    for chave, nome in (("x-vercel-id", "Vercel"), ("cf-ray", "Cloudflare"), ("x-nf-request-id", "Netlify"),
                        ("x-amz-cf-id", "AWS CloudFront"), ("x-github-request-id", "GitHub Pages"),
                        ("x-hostinger", "Hostinger"), ("fly-request-id", "Fly.io"), ("x-render-origin-server", "Render")):
        if chave in h:
            hospedagem.append(nome)
    gerador = re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)', html, re.I)
    out = {"tecnologias": encontrados, "hospedagem_cdn": hospedagem, "servidor": h.get("server"),
           "x_powered_by": h.get("x-powered-by"), "gerador": gerador.group(1) if gerador else None}
    salvar_json(pasta / "stack.json", out)
    return out


# ---------------------------------------------------------------- principal
def main() -> None:
    ap = argparse.ArgumentParser(description="Coleta compartilhada da skill analise-site")
    ap.add_argument("url")
    ap.add_argument("--saida", required=True, help="Pasta da análise. A coleta vai para <saida>/coleta")
    ap.add_argument("--modo", choices=["rapida", "completa"], default="completa")
    ap.add_argument("--max-paginas", type=int, default=None)
    ap.add_argument("--paginas-extra", nargs="*", default=[], help="URLs que precisam entrar na amostra")
    ap.add_argument("--espera-abertura", type=float, default=3.0, help="segundos de espera após carregar, para telas de abertura (padrão 3)")
    ap.add_argument("--sem-lighthouse", action="store_true")
    ap.add_argument("--sem-psi", action="store_true")
    ap.add_argument("--sem-axe", action="store_true")
    ap.add_argument("--sem-dns", action="store_true")
    ap.add_argument("--sem-reputacao", action="store_true")
    ap.add_argument("--limite-links-internos", type=int, default=200)
    ap.add_argument("--limite-links-externos", type=int, default=60)
    args = ap.parse_args()
    global ESPERA_ABERTURA
    ESPERA_ABERTURA = args.espera_abertura

    inicio = time.time()
    url = normalizar_url(args.url)
    host = urlparse(url).netloc
    pasta = Path(args.saida) / "coleta"
    pasta.mkdir(parents=True, exist_ok=True)
    (Path(args.saida) / ".analise-site").write_text("pasta de trabalho da skill analise-site", encoding="utf-8")
    n_paginas = args.max_paginas or (1 if args.modo == "rapida" else 10)
    log(f"Início: {url} | modo {args.modo} | até {n_paginas} páginas | saída {pasta}")

    resumo: dict = {"url_informada": args.url, "url": url, "host": host, "modo": args.modo,
                    "data": dt.datetime.now().isoformat(timespec="seconds"), "ferramentas": {}}
    with sync_playwright() as p:
        req = p.request.new_context(ignore_https_errors=True, user_agent=UA_DESKTOP)
        browser = p.chromium.launch(args=["--no-sandbox"])
        chrome = p.chromium.executable_path

        try:
            http = coletar_http(req, url, pasta, host)
        except Exception as e:
            falha("http", e)
            http = {"url_final": url, "origem": f"https://{host}", "urls_sitemap": [], "headers": {}}
        url_final = http["url_final"]
        host = urlparse(url_final).netloc or host
        resumo["url_final"] = url_final

        if not args.sem_dns:
            resumo["ferramentas"]["dns"] = "erro" not in coletar_dns(req, host, pasta)
        if url_final.startswith("https"):
            coletar_tls(host, pasta, browser)

        axe_js = None
        if not args.sem_axe:
            axe_js = preparar_axe(Path(tempfile.mkdtemp(prefix="axe-")))
        resumo["ferramentas"]["axe"] = bool(axe_js)

        paginas: list[dict] = []
        try:
            home = coletar_pagina(browser, req, url_final, pasta / "paginas" / "home", host, axe_js)
            paginas.append(home)
        except Exception as e:
            falha("pagina home", e)
            traceback.print_exc()
        if paginas:
            lista = escolher_paginas(url_final, paginas[0].get("links_internos", []), http.get("urls_sitemap", []), host, n_paginas)
            lista = lista[1:] + [normalizar_url(u) for u in args.paginas_extra]
            usados = {"home"}
            for u in lista[: max(0, n_paginas - 1) + len(args.paginas_extra)]:
                slug = slug_de(u)
                while slug in usados:
                    slug += "-2"
                usados.add(slug)
                st = get(req, u, redirects=5)["status"]
                if st is None or st >= 400:
                    resumo.setdefault("paginas_descartadas", []).append({"url": u, "status": st})
                    log(f"Página descartada ({st}): {u}")
                    continue
                log(f"Página: {u}")
                try:
                    paginas.append(coletar_pagina(browser, req, u, pasta / "paginas" / slug, host, axe_js))
                except Exception as e:
                    falha(f"pagina {u}", e)

        # capa do relatório
        try:
            ctx = browser.new_context(viewport={"width": 1440, "height": 900}, user_agent=UA_DESKTOP, ignore_https_errors=True)
            pg = ctx.new_page(); abrir(pg, url_final)
            (pasta / "capa").mkdir(exist_ok=True)
            pg.screenshot(path=str(pasta / "capa" / "desktop.jpg"), type="jpeg", quality=70)
            ctx.close()
            ctx = browser.new_context(viewport={"width": 390, "height": 844}, user_agent=UA_MOBILE, is_mobile=True, has_touch=True, ignore_https_errors=True)
            pg = ctx.new_page(); abrir(pg, url_final)
            pg.screenshot(path=str(pasta / "capa" / "mobile.jpg"), type="jpeg", quality=70)
            ctx.close()
        except Exception as e:
            falha("capa", e)

        if paginas:
            try:
                coletar_consentimento(browser, url_final, host, pasta)
            except Exception as e:
                falha("consentimento", e)
            try:
                coletar_js_publico(req, paginas, host, pasta)
            except Exception as e:
                falha("javascript publico", e)
            try:
                coletar_links(req, paginas, pasta, args.limite_links_internos, args.limite_links_externos)
            except Exception as e:
                falha("links", e)
            todas = [u for pg in paginas for u in pg.get("urls_rede", [])]
            salvar_json(pasta / "analytics" / "analytics.json", {
                "por_pagina": {pg["slug"]: analisar_analytics(pg.get("urls_rede", [])) for pg in paginas},
                "geral": analisar_analytics(todas)})
            resumo["stack"] = detectar_stack(paginas, http.get("headers", {}), pasta)

        if not args.sem_reputacao:
            coletar_reputacao(browser, host, pasta)

        # Lighthouse local (home mobile e desktop; mais 2 páginas no modo completo)
        lh = {}
        if not args.sem_lighthouse and paginas:
            alvos = [(paginas[0], "mobile"), (paginas[0], "desktop")]
            if args.modo == "completa":
                alvos += [(pg, "mobile") for pg in paginas[1:3]]
            for pg, ff in alvos:
                log(f"Lighthouse {ff}: {pg['url']}")
                r = rodar_lighthouse(pg["url"], pasta / "lighthouse" / f"{pg['slug']}-{ff}.json", chrome, ff)
                if r:
                    lh[f"{pg['slug']}-{ff}"] = r
            if lh:
                salvar_json(pasta / "lighthouse" / "resumo-lighthouse.json", lh)
        resumo["ferramentas"]["lighthouse"] = bool(lh)
        # Desempenho medido pelo Google: com chave usa a API; sem chave, abre o site do PageSpeed no navegador
        psi = None
        if not args.sem_psi:
            if os.environ.get("PSI_API_KEY"):
                psi = rodar_psi(req, url_final, pasta)
            elif paginas:
                alvos_psi = [(paginas[0]["slug"], paginas[0]["url"], "mobile"), (paginas[0]["slug"], paginas[0]["url"], "desktop")]
                if args.modo == "completa":
                    alvos_psi += [(pg["slug"], pg["url"], "mobile") for pg in paginas[1:3]]
                psi = rodar_pagespeed_web(p, alvos_psi, pasta)
        resumo["ferramentas"]["psi"] = bool(psi)
        if psi:
            resumo["ferramentas"]["psi_origem"] = "api" if os.environ.get("PSI_API_KEY") else "pagespeed.web.dev"
        else:
            resumo["dados_de_campo"] = {
                "disponivel": False,
                "motivo": "o PageSpeed do Google não respondeu (limite de uso, bloqueio ou --sem-psi)",
                "alternativa": "metricas_lab de cada página (medidas no navegador) e Lighthouse local"}
            log("PageSpeed do Google indisponível: a análise usa as medições de laboratório do navegador e o Lighthouse local.")

        browser.close()
        req.dispose()

    resumo["paginas"] = [{k: v for k, v in pg.items() if k not in ("urls_rede", "links_internos", "links_externos")}
                         for pg in paginas]
    resumo["falhas"] = FALHAS
    resumo["duracao_s"] = round(time.time() - inicio, 1)
    resumo["mapa_de_arquivos"] = {
        "paginas/<slug>/": "html-bruto.html, html-renderizado.html, texto.md, dados.json, layout.json, rede.json, console.json, axe.json, desktop.png, tablet.png, mobile.png, dobra-mobile.png",
        "http/": "redirects.json, headers.json, arquivos-padrao.json, robots.txt, sitemap-*.xml, urls-sitemap.json, llms.txt, exposicao.json, cors.json, segredos-bundle.json, source-maps.json",
        "dns/dns.json": "A, MX, SPF, DMARC, DKIM, CAA, DNSSEC, listas de bloqueio",
        "tls/tls.json": "certificado",
        "privacidade/consentimento.json": "banner, terceiros e cookies antes e depois do aceite",
        "links/": "links.json (status, quebrados, cadeias), contatos.json (WhatsApp, telefone, e-mail, formulários)",
        "analytics/analytics.json": "GA4, GTM, Meta Pixel e outros, por página",
        "reputacao/safe-browsing.json": "Google Navegação segura",
        "lighthouse/": "relatórios completos e resumo-lighthouse.json",
        "psi/": "PageSpeed do Google (medido nos servidores dele): resumo-psi.json, web-<pagina>-<mobile|desktop>.txt e .png; traz dados de campo (usuários reais) quando o site tem tráfego",
        "stack.json": "tecnologias e hospedagem detectadas",
        "capa/": "desktop.jpg e mobile.jpg para o relatório",
    }
    salvar_json(pasta / "resumo.json", resumo)
    log(f"Fim em {resumo['duracao_s']} s. {len(paginas)} páginas. {len(FALHAS)} etapas com falha. Índice: {pasta / 'resumo.json'}")


if __name__ == "__main__":
    main()
