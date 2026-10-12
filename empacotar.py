#!/usr/bin/env python3
"""
Gera o .zip de distribuição da skill analise-site.

Uso:
    python empacotar.py --versao 1.1

Cria dist/analise-site-<versao>.zip com:
    analise-site-<versao>/instalar.py
    analise-site-<versao>/LEIA-ME.txt
    analise-site-<versao>/analise-site/   (a skill, sem __pycache__ e sem backups)
"""
from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent


def main() -> None:
    ap = argparse.ArgumentParser(description="Gera o .zip de distribuição da skill analise-site")
    ap.add_argument("--versao", required=True, help="por exemplo 1.1")
    args = ap.parse_args()

    skill = RAIZ / "analise-site"
    if not (skill / "SKILL.md").exists():
        raise SystemExit("Pasta analise-site/ com SKILL.md não encontrada ao lado deste script.")
    pasta = f"analise-site-{args.versao}"
    saida = RAIZ / "dist" / f"{pasta}.zip"
    saida.parent.mkdir(exist_ok=True)

    n = 0
    with zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(RAIZ / "instalar.py", f"{pasta}/instalar.py")
        z.write(RAIZ / "LEIA-ME.txt", f"{pasta}/LEIA-ME.txt")
        for f in sorted(skill.rglob("*")):
            if not f.is_file() or "__pycache__" in f.parts or f.suffix in (".pyc", ".bak"):
                continue
            z.write(f, f"{pasta}/analise-site/{f.relative_to(skill).as_posix()}")
            n += 1
    print(f"{saida} ({saida.stat().st_size // 1024} KB, {n} arquivos da skill)")


if __name__ == "__main__":
    main()
