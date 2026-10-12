#!/usr/bin/env python3
"""
Entrega só o relatório e limpa os arquivos de trabalho da análise.

Durante a análise a skill usa uma pasta de trabalho (coleta, achados dos agentes, JSONs, rascunhos). Depois que o
relatório está pronto, o usuário só precisa de relatorio.html e relatorio.pdf. Este script:

  1. copia relatorio.html e relatorio.pdf para a pasta de destino (e issues/, só com --issues);
  2. apaga a pasta de trabalho, a menos que se use --manter-dados.

Trava de segurança: só apaga pastas que contêm o arquivo-marca .analise-site, criado pela coleta.
Nunca apaga a pasta de destino nem uma pasta que a contenha.

Uso:
    python finalizar.py --trabalho <pasta de trabalho> --destino <pasta do relatório> [--manter-dados] [--issues]
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

MARCA = ".analise-site"


def dentro(filho: Path, pai: Path) -> bool:
    try:
        filho.resolve().relative_to(pai.resolve())
        return True
    except ValueError:
        return False


def main() -> None:
    ap = argparse.ArgumentParser(description="Entrega o relatório e limpa os arquivos de trabalho")
    ap.add_argument("--trabalho", required=True, help="pasta usada como --saida na coleta")
    ap.add_argument("--destino", required=True, help="pasta onde ficam relatorio.html e relatorio.pdf")
    ap.add_argument("--manter-dados", action="store_true", help="não apaga os arquivos de trabalho")
    ap.add_argument("--issues", action="store_true", help="entrega também a pasta issues/ (um arquivo por issue)")
    args = ap.parse_args()

    trabalho, destino = Path(args.trabalho).resolve(), Path(args.destino).resolve()
    html, pdf = trabalho / "relatorio.html", trabalho / "relatorio.pdf"
    if not html.exists():
        sys.exit(f"relatorio.html não encontrado em {trabalho}. Rode relatorio.py antes.")

    mesmo_lugar = trabalho == destino
    destino.mkdir(parents=True, exist_ok=True)
    entregues = ["relatorio.html"]
    if not mesmo_lugar:
        shutil.copy2(html, destino / "relatorio.html")
    if pdf.exists():
        entregues.append("relatorio.pdf")
        if not mesmo_lugar:
            shutil.copy2(pdf, destino / "relatorio.pdf")
    else:
        print("Aviso: relatorio.pdf não foi gerado; entregando só o HTML.")
    if args.issues and (trabalho / "issues").is_dir():
        entregues.append("issues/")
        if not mesmo_lugar:
            shutil.copytree(trabalho / "issues", destino / "issues", dirs_exist_ok=True)

    if args.manter_dados:
        print(f"Relatório em {destino}. Arquivos de trabalho mantidos em {trabalho}.")
        return

    if not (trabalho / MARCA).exists():
        print(f"Relatório em {destino}. Não apaguei nada: {trabalho} não tem a marca {MARCA} (não foi criada pela skill).")
        return

    if mesmo_lugar:
        # limpa no lugar: remove tudo, menos o que foi entregue
        manter = set(entregues) | {e.rstrip("/") for e in entregues}
        for item in trabalho.iterdir():
            if item.name in manter:
                continue
            shutil.rmtree(item) if item.is_dir() else item.unlink()
    else:
        if dentro(destino, trabalho):
            sys.exit(f"Recusado: o destino {destino} está dentro da pasta de trabalho {trabalho}.")
        shutil.rmtree(trabalho, ignore_errors=True)
    print(f"Relatório em {destino}: {', '.join(entregues)}. Arquivos de trabalho removidos.")


if __name__ == "__main__":
    main()
