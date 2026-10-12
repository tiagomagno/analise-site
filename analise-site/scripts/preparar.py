#!/usr/bin/env python3
"""
Confere (e, se pedido, instala) o que a skill analise-site precisa para rodar.

Uso:
    python preparar.py              só confere e mostra o que falta
    python preparar.py --instalar   instala o que for seguro instalar sozinho (pacotes Python e o navegador da coleta)

O que ela precisa:
    OBRIGATÓRIO   Python 3.9 ou mais novo
    OBRIGATÓRIO   pacote Python "playwright" e o navegador Chromium dele (coleta, capturas de tela, PageSpeed e PDF)
    RECOMENDADO   pacote Python "jsonschema" (valida o que os agentes gravam)
    RECOMENDADO   Node.js 18 ou mais novo (Lighthouse local e axe-core, que medem desempenho e acessibilidade)
    Internet      para visitar o site analisado e consultar o PageSpeed do Google

O Node.js é um programa do sistema; por isso este script nunca o instala sozinho. Ele mostra o comando
ou o endereço de download e você decide.
"""
from __future__ import annotations

import argparse
import importlib.util
import platform
import shutil
import subprocess
import sys
import urllib.request

OK, FALTA, AVISO = "[ok]   ", "[falta]", "[aviso]"
problemas_obrigatorios: list[str] = []
problemas_recomendados: list[str] = []


def linha(estado: str, texto: str) -> None:
    print(f"{estado} {texto}")


def executar(cmd: list[str], timeout: int = 600) -> bool:
    try:
        r = subprocess.run(cmd, timeout=timeout, capture_output=True, text=True, shell=(platform.system() == "Windows" and cmd[0] in ("npm", "npx", "node")))
        return r.returncode == 0
    except Exception:
        return False


def tem_modulo(nome: str) -> bool:
    return importlib.util.find_spec(nome) is not None


def chromium_instalado() -> bool:
    if not tem_modulo("playwright"):
        return False
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            caminho = p.chromium.executable_path
        import os
        return bool(caminho) and os.path.exists(caminho)
    except Exception:
        return False


def versao_node() -> tuple[int, str] | None:
    exe = shutil.which("node")
    if not exe:
        return None
    try:
        saida = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=15).stdout.strip()
        return int(saida.lstrip("v").split(".")[0]), saida
    except Exception:
        return None


def comando_node() -> str:
    so = platform.system()
    if so == "Windows":
        return "winget install OpenJS.NodeJS.LTS   (ou baixe em https://nodejs.org)"
    if so == "Darwin":
        return "brew install node   (ou baixe em https://nodejs.org)"
    return "sudo apt install nodejs npm   (ou veja https://nodejs.org)"


def internet() -> bool:
    try:
        urllib.request.urlopen("https://pagespeed.web.dev", timeout=10)
        return True
    except Exception:
        return False


def main() -> None:
    ap = argparse.ArgumentParser(description="Confere e prepara o ambiente da skill analise-site")
    ap.add_argument("--instalar", action="store_true", help="instala pacotes Python e o Chromium do Playwright, se faltarem")
    args = ap.parse_args()

    print(f"Sistema: {platform.system()} | Python em uso: {sys.executable}\n")

    # Python
    if sys.version_info >= (3, 9):
        linha(OK, f"Python {platform.python_version()}")
    else:
        linha(FALTA, f"Python {platform.python_version()} é antigo demais; instale o 3.9 ou mais novo (https://python.org)")
        problemas_obrigatorios.append("python")
    if platform.system() == "Windows" and "WindowsApps" in sys.executable:
        linha(AVISO, "Este Python parece ser o atalho da Microsoft Store. Se algo falhar, instale o Python em https://python.org "
                     "ou use o caminho completo do interpretador (comando `py -0p` lista os instalados).")

    # playwright
    if tem_modulo("playwright"):
        linha(OK, "pacote playwright")
    else:
        linha(FALTA, "pacote playwright")
        if args.instalar and executar([sys.executable, "-m", "pip", "install", "playwright"]):
            linha(OK, "pacote playwright instalado agora")
        else:
            problemas_obrigatorios.append("playwright")

    # chromium
    if chromium_instalado():
        linha(OK, "navegador Chromium do Playwright")
    elif tem_modulo("playwright"):
        linha(FALTA, "navegador Chromium do Playwright (uns 150 MB, baixados uma única vez)")
        if args.instalar and executar([sys.executable, "-m", "playwright", "install", "chromium"], timeout=1200) and chromium_instalado():
            linha(OK, "Chromium instalado agora")
        else:
            problemas_obrigatorios.append("chromium")
    else:
        problemas_obrigatorios.append("chromium")

    # jsonschema
    if tem_modulo("jsonschema"):
        linha(OK, "pacote jsonschema (validação rigorosa)")
    else:
        linha(FALTA, "pacote jsonschema (recomendado)")
        if args.instalar and executar([sys.executable, "-m", "pip", "install", "jsonschema"]):
            linha(OK, "pacote jsonschema instalado agora")
        else:
            problemas_recomendados.append("jsonschema")

    # node
    node = versao_node()
    if node and node[0] >= 18:
        linha(OK, f"Node.js {node[1]} (Lighthouse local e axe-core)")
        if not shutil.which("npx"):
            linha(AVISO, "npx não encontrado; reinstale o Node.js completo")
            problemas_recomendados.append("npx")
    elif node:
        linha(AVISO, f"Node.js {node[1]} é antigo; o recomendado é 18 ou mais novo")
        problemas_recomendados.append("node")
    else:
        linha(FALTA, f"Node.js (recomendado). Instale com: {comando_node()}")
        problemas_recomendados.append("node")

    # internet
    if internet():
        linha(OK, "acesso à internet e ao PageSpeed do Google")
    else:
        linha(AVISO, "não consegui abrir https://pagespeed.web.dev; verifique a conexão, proxy ou firewall")
        problemas_recomendados.append("internet")

    print()
    if problemas_obrigatorios:
        print("Ainda falta algo OBRIGATÓRIO: " + ", ".join(problemas_obrigatorios))
        if not args.instalar:
            print("Rode de novo com --instalar para instalar o que for possível sozinho.")
        sys.exit(1)
    print("Tudo o que é obrigatório está pronto.")
    if problemas_recomendados:
        print("Funciona, mas com menos recursos. Faltam itens recomendados: " + ", ".join(problemas_recomendados))
        if "node" in problemas_recomendados or "npx" in problemas_recomendados:
            print("Sem o Node.js não rodam o Lighthouse local nem o axe-core; o PageSpeed do Google e as demais análises continuam.")


if __name__ == "__main__":
    main()
