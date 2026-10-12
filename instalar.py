#!/usr/bin/env python3
"""
Instala a skill analise-site no Claude Code.

Uso:
    python instalar.py                      instala para todos os projetos (~/.claude/skills/analise-site)
    python instalar.py --projeto <pasta>    instala só nesse projeto (<pasta>/.claude/skills/analise-site)

O que faz:
  1. copia a pasta analise-site para o lugar certo (se já existir, guarda a versão antiga ao lado, sem apagar);
  2. roda a verificação de ambiente e instala o que for seguro (pacotes Python e o navegador da coleta).

O Python e o Node.js são programas do sistema: se faltarem, o script mostra como instalar.
"""
from __future__ import annotations

import argparse
import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description="Instala a skill analise-site no Claude Code")
    ap.add_argument("--projeto", help="instala só neste projeto, em vez de para todos")
    ap.add_argument("--destino", help="(avançado) pasta exata onde colocar a skill")
    args = ap.parse_args()

    origem = Path(__file__).resolve().parent / "analise-site"
    if not (origem / "SKILL.md").exists():
        sys.exit(f"Não encontrei a pasta analise-site ao lado deste script ({origem}). Extraia o .zip inteiro antes de instalar.")

    if args.destino:
        destino = Path(args.destino)
    elif args.projeto:
        destino = Path(args.projeto) / ".claude" / "skills" / "analise-site"
    else:
        destino = Path.home() / ".claude" / "skills" / "analise-site"

    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists():
        antigo = destino.with_name(f"analise-site.antiga-{dt.datetime.now():%Y%m%d-%H%M%S}")
        destino.rename(antigo)
        print(f"Já havia uma versão instalada. Guardei em: {antigo}")
    shutil.copytree(origem, destino, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.bak"))
    print(f"Skill copiada para: {destino}\n")

    print("Verificando o ambiente...\n")
    r = subprocess.run([sys.executable, str(destino / "scripts" / "preparar.py"), "--instalar"])
    print()
    if r.returncode != 0:
        print("Falta algo obrigatório (veja acima). Resolva e rode de novo:")
        print(f'    "{sys.executable}" "{destino / "scripts" / "preparar.py"}" --instalar')
        sys.exit(1)
    print("Pronto. Abra o Claude Code e peça, por exemplo:")
    print('    analisa o site https://exemplo.com.br')


if __name__ == "__main__":
    main()
