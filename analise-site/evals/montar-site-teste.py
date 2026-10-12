#!/usr/bin/env python3
"""
Monta um site de teste com falhas propositais, para conferir se a skill as encontra.

Uso:
    python montar-site-teste.py ./site-teste
    cd site-teste && python -m http.server 8765 --bind 127.0.0.1
    (em outro terminal) python ../scripts/coleta.py http://127.0.0.1:8765/ --saida ./analise-teste --max-paginas 5 --sem-psi --sem-reputacao --sem-dns

Os segredos são montados em tempo de execução e são falsos. Nenhum arquivo desta
pasta contém um padrão de chave real, para não disparar a proteção de push do GitHub.
O gabarito do que a análise deve encontrar está em gabarito.md.
"""
import os
import random
import string
import sys
from pathlib import Path

destino = Path(sys.argv[1] if len(sys.argv) > 1 else "site-teste")
(destino / ".git").mkdir(parents=True, exist_ok=True)
(destino / "img").mkdir(exist_ok=True)


def escrever(nome: str, conteudo: str) -> None:
    (destino / nome).write_text(conteudo, encoding="utf-8")


# imagem pesada (~1,4 MB, PNG de ruído) e um logo pequeno
try:
    from PIL import Image
    Image.frombytes("RGB", (800, 600), os.urandom(800 * 600 * 3)).save(destino / "img" / "hero.png")
    Image.new("RGB", (64, 64), (30, 80, 160)).save(destino / "img" / "logo.png")
except ImportError:
    (destino / "img" / "hero.png").write_bytes(os.urandom(1_400_000))
    (destino / "img" / "logo.png").write_bytes(os.urandom(2_000))

escrever(".git/HEAD", "ref: refs/heads/main\n")
escrever(".env", "DATABASE_URL=postgres://usuario:senha@db/producao\nJWT_SECRET=troque-isto\nSTRIPE_KEY=chave_de_teste\n")
escrever("robots.txt", "User-agent: *\nAllow: /\nSitemap: http://127.0.0.1:8765/sitemap.xml\n")
escrever("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
         + "".join(f"<url><loc>http://127.0.0.1:8765/{p}</loc></url>" for p in ["", "sobre.html", "servicos.html", "contato.html"])
         + "</urlset>\n")
falsa = "sk_" + "live_" + "".join(random.choices(string.ascii_letters + string.digits, k=28))
escrever("app.js", f'console.log("app"); const cfg={{k:"{falsa}"}};\n'
         'document.querySelectorAll(".x").forEach(e=>e.innerHTML=location.hash);\n//# sourceMappingURL=app.js.map\n')
escrever("app.js.map", '{"version":3,"sources":["src/app.ts"],"mappings":""}\n')

HEAD = ('<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{font-family:Arial;margin:0}'
        'header{display:flex;gap:8px;padding:10px;background:#123}header a{color:#fff;font-size:11px}.largo{width:600px;background:#eee}'
        '.cinza{color:#bbb;background:#fff}.mini{font-size:10px;padding:1px 3px}#cookie{position:fixed;bottom:0;left:0;right:0;background:#333;color:#fff;padding:12px}</style>')
NAV = ('<header><a href="index.html">Início</a><a href="sobre.html">Sobre</a><a href="servicos.html">Serviços</a>'
       '<a href="contato.html">Contato</a><a href="pagina-quebrada.html">Promoções</a></header>')

escrever("index.html", f"""<!doctype html><html><head><title>Empresa Exemplo Soluções Inovadoras de Excelência para Você e Sua Família em Toda Região</title>{HEAD}
<script async src="https://www.googletagmanager.com/gtag/js?id=G-TESTE123"></script>
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Organization","name":"Empresa Exemplo"}}</script>
<meta property="og:title" content="Empresa Exemplo"></head><body>{NAV}
<h1>Bem-vindo ao nosso site</h1><h1>Soluções completas</h1>
<p>Somos uma empresa que oferece as melhores soluções do mercado, com qualidade, compromisso e transparência. Não é só um serviço. É uma experiência.</p>
<p class="cinza">Atendemos com excessão de feriados.</p>
<img src="img/hero.png"><img src="img/logo.png" alt="Logo">
<div class="largo">Tabela larga que estoura no celular</div>
<a class="mini" href="https://wa.me/999">Whats</a> <a href="tel:9299">Ligue</a>
<script src="app.js"></script>
<div id="cookie">Usamos cookies para melhorar sua experiência. <button onclick="this.parentNode.remove()">Aceitar</button></div>
</body></html>""")

for pg in ("sobre", "servicos"):
    escrever(f"{pg}.html", f"""<!doctype html><html lang="pt-BR"><head><title>{pg} | Empresa Exemplo</title><meta name="description" content="Página {pg} da Empresa Exemplo">{HEAD}</head><body>{NAV}
<main><h1>{pg}</h1><p>Texto da página {pg}. Cada vez mais, potencializamos resultados com soluções robustas.</p></main><footer>© 2019 Empresa Exemplo</footer></body></html>""")

escrever("contato.html", f"""<!doctype html><html lang="pt-BR"><head><title>Contato | Empresa Exemplo</title>{HEAD}</head><body>{NAV}
<main><h1>Fale conosco</h1><form action="/enviar" method="post"><input name="nome" placeholder="Nome"><input name="cpf" placeholder="CPF"><input name="email" type="email" placeholder="E-mail"><input type="checkbox" name="news" checked> Quero receber ofertas<button>Enviar</button></form>
<a href="https://api.whatsapp.com/send?phone=5592991234567&text=Ol%C3%A1">WhatsApp</a> <a href="mailto:contato@exemplo">E-mail</a></main></body></html>""")

print(f"Site de teste montado em {destino.resolve()}")
