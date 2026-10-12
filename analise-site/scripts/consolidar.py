#!/usr/bin/env python3
"""
Consolida os achados dos agentes de segmento.

Lê   <saida>/achados/*.json, <saida>/escopo.json e, se existirem, <saida>/verificacao.json e
     <saida>/duplicados.json (lista de grupos de IDs que são o mesmo problema: [["PRI-003", "CON-005"]])
Grava <saida>/consolidado.json

- valida cada arquivo contra schemas/achados.schema.json (se o pacote jsonschema existir)
- aplica a verificação independente (confirmado / rebaixado / descartado)
- junta achados repetidos entre segmentos (regra exata, similaridade de texto e grupos manuais) e lista candidatos a conferir
- recalcula as notas, aplica os pesos do tipo de site e os tetos
- define a prioridade (P1, P2, P3) de cada achado

Uso: python consolidar.py --saida docs/analise/2026-10-10
"""
from __future__ import annotations

import argparse
import difflib
import json
import math
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SEV_ORDEM = ["critica", "alta", "media", "baixa", "info"]
SEV_DESCONTO = {"critica": 25, "alta": 12, "media": 5, "baixa": 2, "info": 0}
NOMES = {"seguranca": "Segurança", "privacidade": "Privacidade e LGPD", "desempenho": "Desempenho", "seo": "SEO e AEO",
         "acessibilidade": "Acessibilidade", "design": "Design e UI", "copy": "Copy e Conteúdo",
         "conversao": "Conversão e UX", "analytics": "Analytics", "arquitetura": "Arquitetura, Código e Infra",
         "negocio": "Negócio e Mercado"}
ORDEM_SEG = list(NOMES)

# Junção de achados repetidos entre segmentos (calibrada contra 12 pares reais confirmados à mão em 2 análises):
# acima de LIMITE_AUTO junta sozinho; entre LIMITE_CANDIDATO e LIMITE_AUTO vira candidato para conferência.
LIMITE_AUTO = 0.35
LIMITE_CANDIDATO = 0.10
MAX_CANDIDATOS = 15
MIN_ACHADOS_SIMILARIDADE = 12  # com poucos achados a raridade das palavras não é confiável
PALAVRAS_COMUNS = set("para como mais sobre nao sem dos das uma uns pelo pela que com por mas ate nas nos seu sua suas seus entre "
                      "quando onde isso esse essa esta este todas todos cada outro outra tem ter ser sao foi pagina paginas site "
                      "pode podem fica ficam muito apenas ainda depois antes alem tambem cliente visitante".split())


def ler_json(p: Path, padrao=None):
    if not p.exists():
        return padrao
    return json.loads(p.read_text(encoding="utf-8"))


def validar(dados: dict, schema: dict | None, nome: str, avisos: list) -> None:
    if schema is None:
        for campo in ("segmento", "nota", "achados", "pontos_fortes", "cobertura"):
            if campo not in dados:
                avisos.append(f"{nome}: campo obrigatório ausente '{campo}'")
        return
    try:
        import jsonschema
        v = jsonschema.Draft202012Validator(schema)
        for erro in list(v.iter_errors(dados))[:10]:
            caminho = "/".join(str(x) for x in erro.absolute_path)
            avisos.append(f"{nome}: {caminho or '(raiz)'}: {erro.message[:160]}")
    except ImportError:
        validar(dados, None, nome, avisos)


def desconto(achados: list[dict]) -> float:
    total = 0.0
    for a in achados:
        d = SEV_DESCONTO.get(a.get("severidade"), 0)
        total += d / 2 if a.get("confianca") == "suspeita" else d
    return total


def prioridade(a: dict) -> str:
    s, e = a.get("severidade"), a.get("esforco", "M")
    if s == "critica" or (s == "alta" and e in ("P", "M")):
        return "P1"
    if s == "alta" or (s == "media" and e in ("P", "M")):
        return "P2"
    return "P3"


def chave_texto(a: dict) -> str:
    return re.sub(r"\W+", " ", (a.get("titulo") or "").lower()).strip()


def local(a: dict) -> str:
    ev = a.get("evidencia") or {}
    return (ev.get("arquivo") or "") + "|" + (ev.get("url") or "").split(",")[0].strip()


def mesmo_problema(a: dict, b: dict) -> bool:
    """Critério conservador: juntar errado é pior que deixar repetido.
    Repetições semânticas que escapam daqui são indicadas em duplicados.json pelo orquestrador."""
    ev_a, ev_b = a.get("evidencia") or {}, b.get("evidencia") or {}
    razao = difflib.SequenceMatcher(None, chave_texto(a), chave_texto(b)).ratio()
    if a.get("check_id") and a.get("check_id") == b.get("check_id") and razao >= 0.6:
        return True
    if local(a) == local(b) and local(a) != "|":
        if razao >= 0.8:
            return True
        if ev_a.get("trecho") and ev_a.get("trecho") == ev_b.get("trecho"):
            return True
    return False


def juntar(alvo: dict, a: dict) -> None:
    rel = set(alvo.get("segmentos_relacionados") or []) | {a["segmento"]} | set(a.get("segmentos_relacionados") or [])
    rel.discard(alvo["segmento"])
    alvo["segmentos_relacionados"] = sorted(rel)
    alvo.setdefault("ids_juntados", []).append(a["id"])


def _tokens(texto: str) -> set[str]:
    t = unicodedata.normalize("NFD", (texto or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return {w[:6] for w in re.findall(r"[a-z0-9]{4,}", t) if w not in PALAVRAS_COMUNS}


def _doc(a: dict) -> set[str]:
    ev = a.get("evidencia") or {}
    return (_tokens(a.get("titulo")) | _tokens((a.get("impacto_usuario") or "") + " " + (a.get("recomendacao") or ""))
            | _tokens(ev.get("trecho")))


def pares_similares(achados: list[dict]) -> list[tuple[float, dict, dict]]:
    """Pontua cada par de achados de segmentos diferentes. Palavras raras no conjunto pesam mais (idf)."""
    if len(achados) < MIN_ACHADOS_SIMILARIDADE:
        return []
    docs = {a["id"]: _doc(a) for a in achados}
    titulos = {a["id"]: _tokens(a.get("titulo")) for a in achados}
    df: dict[str, int] = {}
    for conj in docs.values():
        for w in conj:
            df[w] = df.get(w, 0) + 1
    n = len(achados)

    def peso(w: str) -> float:
        return math.log(n / df[w]) if w in df else 0.0

    def jaccard_idf(x: set, y: set) -> float:
        total = sum(peso(w) for w in x | y)
        return sum(peso(w) for w in x & y) / total if total else 0.0

    pares = []
    for i, a in enumerate(achados):
        for b in achados[i + 1:]:
            if a["segmento"] == b["segmento"]:
                continue
            sc = 0.5 * jaccard_idf(docs[a["id"]], docs[b["id"]]) + 0.5 * jaccard_idf(titulos[a["id"]], titulos[b["id"]])
            pares.append((sc, a, b))
    pares.sort(key=lambda x: -x[0])
    return pares


def deduplicar(achados: list[dict], grupos_manuais: list[list[str]] | None = None) -> tuple[list[dict], int, dict]:
    """Junta achados de segmentos diferentes que descrevem o mesmo problema.
    Devolve (achados, quantidade_juntada, relatorio) com o detalhe do que foi juntado e os candidatos a conferir."""
    resultado: list[dict] = []
    juntados = 0
    relatorio: dict = {"manual": [], "automatico": [], "candidatos": [], "avisos": []}
    ids_originais = {a["id"] for a in achados}
    por_id = {a["id"]: a for a in achados}
    absorvidos: set[str] = set()
    for grupo in grupos_manuais or []:
        desconhecidos = [g for g in grupo if g not in por_id]
        if desconhecidos:
            relatorio["avisos"].append(f"duplicados.json: ID inexistente {desconhecidos} no grupo {grupo}; grupo ignorado")
            continue
        existentes = [por_id[g] for g in grupo if g not in absorvidos]
        if len({e["segmento"] for e in existentes}) < 2:
            relatorio["avisos"].append(f"duplicados.json: o grupo {grupo} não envolve segmentos diferentes; ignorado")
            continue
        existentes.sort(key=lambda x: SEV_ORDEM.index(x.get("severidade", "info")))
        for outro in existentes[1:]:
            juntar(existentes[0], outro)
            absorvidos.add(outro["id"])
            juntados += 1
        relatorio["manual"].append({"mantido": existentes[0]["id"], "juntados": [o["id"] for o in existentes[1:]]})
    achados = [a for a in achados if a["id"] not in absorvidos]

    # regra conservadora: mesma checagem e mesmo trecho
    for a in sorted(achados, key=lambda x: SEV_ORDEM.index(x.get("severidade", "info"))):
        alvo = None
        for b in resultado:
            if b["segmento"] != a["segmento"] and mesmo_problema(a, b):
                alvo = b
                break
        if alvo:
            juntados += 1
            juntar(alvo, a)
            relatorio["automatico"].append({"mantido": alvo["id"], "juntados": [a["id"]], "motivo": "mesma checagem e mesmo trecho"})
            absorvidos.add(a["id"])
        else:
            resultado.append(a)

    # similaridade de texto: junta o que passa do limite e passa nas validações; o resto vira candidato
    vivos = {a["id"]: a for a in resultado}
    for sc, a, b in pares_similares(resultado):
        if sc < LIMITE_CANDIDATO:
            break
        if a["id"] not in vivos or b["id"] not in vivos:
            continue
        dist = abs(SEV_ORDEM.index(a.get("severidade", "info")) - SEV_ORDEM.index(b.get("severidade", "info")))
        if sc >= LIMITE_AUTO and dist <= 2:
            a, b = sorted((a, b), key=lambda x: SEV_ORDEM.index(x.get("severidade", "info")))
            juntar(a, b)
            vivos.pop(b["id"])
            absorvidos.add(b["id"])
            juntados += 1
            relatorio["automatico"].append({"mantido": a["id"], "juntados": [b["id"]], "pontuacao": round(sc, 2),
                                            "titulos": [a["titulo"], b["titulo"]]})
        else:
            relatorio["candidatos"].append({"pontuacao": round(sc, 2), "ids": [a["id"], b["id"]],
                                            "segmentos": [a["segmento"], b["segmento"]],
                                            "titulos": [a["titulo"], b["titulo"]],
                                            "observacao": "severidades muito diferentes" if sc >= LIMITE_AUTO else None})
    resultado = [a for a in resultado if a["id"] in vivos]
    relatorio["candidatos"] = relatorio["candidatos"][:MAX_CANDIDATOS]

    # validação: nenhum achado pode sumir nem apontar para um ID que não existe
    finais = {a["id"] for a in resultado}
    perdidos = ids_originais - finais - absorvidos
    if perdidos:
        relatorio["avisos"].append(f"junção: achados perdidos {sorted(perdidos)}")
    for a in resultado:
        for jid in a.get("ids_juntados", []):
            if jid not in ids_originais:
                relatorio["avisos"].append(f"junção: {a['id']} cita {jid}, que não existe")
    return resultado, juntados, relatorio


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", required=True)
    ap.add_argument("--tipo", help="Sobrescreve escopo.json -> tipo_site")
    args = ap.parse_args()
    saida = Path(args.saida)
    escopo = ler_json(saida / "escopo.json", {}) or {}
    tipo = args.tipo or escopo.get("tipo_site") or "institucional"
    pesos_cfg = ler_json(RAIZ / "config" / "pesos.json")
    if tipo not in pesos_cfg["tipos"]:
        sys.exit(f"Tipo de site desconhecido: {tipo}. Use um de {list(pesos_cfg['tipos'])}")
    pesos = pesos_cfg["tipos"][tipo]
    schema = ler_json(RAIZ / "schemas" / "achados.schema.json")
    verificacao = ler_json(saida / "verificacao.json", {}) or {}
    avisos: list[str] = []

    segmentos: dict[str, dict] = {}
    for arq in sorted((saida / "achados").glob("*.json")):
        try:
            d = json.loads(arq.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            avisos.append(f"{arq.name}: JSON inválido ({e})")
            continue
        validar(d, schema, arq.name, avisos)
        seg = d.get("segmento") or arq.stem
        d["segmento"] = seg
        segmentos[seg] = d
    if not segmentos:
        sys.exit("Nenhum arquivo em achados/. Rode os agentes antes de consolidar.")

    todos, descartados = [], []
    for seg, d in segmentos.items():
        antes = desconto(d.get("achados", []))
        finais = []
        for a in d.get("achados", []):
            a["segmento"] = seg
            v = verificacao.get(a.get("id"))
            if v:
                a["verificacao"] = v
                st = v.get("status")
                if st == "descartado":
                    descartados.append({**a, "motivo": v.get("nota")})
                    continue
                if st == "rebaixado" and v.get("nova_severidade") in SEV_ORDEM:
                    a["severidade_original"] = a["severidade"]
                    a["severidade"] = v["nova_severidade"]
            finais.append(a)
        depois = desconto(finais)
        nota = d.get("nota")
        if nota is not None:
            d["nota_agente"] = nota
            d["nota"] = max(0, min(100, round(nota + (antes - depois))))
        d["achados"] = finais
        todos += finais

    todos, juntados, rel_dup = deduplicar(todos, ler_json(saida / "duplicados.json", []))
    avisos += rel_dup["avisos"]
    (saida / "duplicados-candidatos.json").write_text(json.dumps(rel_dup["candidatos"], ensure_ascii=False, indent=2), encoding="utf-8")
    for a in todos:
        a["prioridade"] = prioridade(a)
        a["segmento_nome"] = NOMES.get(a["segmento"], a["segmento"])
    todos.sort(key=lambda a: (SEV_ORDEM.index(a["severidade"]), {"P": 0, "M": 1, "G": 2}.get(a.get("esforco"), 1),
                              -len(a.get("segmentos_relacionados") or [])))

    # nota geral
    soma, peso_total = 0.0, 0
    notas = {}
    for seg in ORDEM_SEG:
        if seg not in segmentos:
            continue
        d = segmentos[seg]
        cont = {s: 0 for s in SEV_ORDEM}
        for a in todos:
            if a["segmento"] == seg:
                cont[a["severidade"]] += 1
        notas[seg] = {"nome": NOMES[seg], "nota": d.get("nota"), "peso": pesos.get(seg, 0), "resumo": d.get("resumo", ""),
                      "achados_por_severidade": cont, "modo": d.get("modo")}
        if d.get("nota") is not None and pesos.get(seg, 0) > 0:
            soma += d["nota"] * pesos[seg]
            peso_total += pesos[seg]
    nota_geral = round(soma / peso_total) if peso_total else None
    tetos_aplicados = []
    if nota_geral is not None:
        if any(a["severidade"] == "critica" and a["segmento"] in ("seguranca", "privacidade") and a.get("confianca") == "verificado"
               for a in todos):
            teto = pesos_cfg["tetos"]["critico_seguranca_ou_privacidade"]
            if nota_geral > teto:
                tetos_aplicados.append(f"Achado crítico confirmado em Segurança ou Privacidade: nota limitada a {teto}.")
                nota_geral = teto
        rep = ((segmentos.get("negocio") or {}).get("extras") or {}).get("reputacao") or {}
        if rep.get("perigoso") is True:
            teto = pesos_cfg["tetos"]["dominio_marcado_como_perigoso"]
            if nota_geral > teto:
                tetos_aplicados.append(f"Domínio marcado como perigoso: nota limitada a {teto}.")
                nota_geral = teto
    faixa = next((f["rotulo"] for f in pesos_cfg["faixas"] if nota_geral is not None and nota_geral >= f["min"]), "Sem nota")

    pontos_fortes = [{**p, "segmento": seg, "segmento_nome": NOMES.get(seg, seg)}
                     for seg in ORDEM_SEG if seg in segmentos for p in segmentos[seg].get("pontos_fortes", [])]
    cobertura = {seg: segmentos[seg].get("cobertura", {}) for seg in ORDEM_SEG if seg in segmentos}
    extras = {seg: segmentos[seg].get("extras") for seg in ORDEM_SEG if seg in segmentos and segmentos[seg].get("extras")}
    por_sev = {s: sum(1 for a in todos if a["severidade"] == s) for s in SEV_ORDEM}

    out = {
        "meta": {"site": escopo.get("url"), "cliente": escopo.get("cliente"), "data": escopo.get("data"),
                 "tipo_site": tipo, "modo": escopo.get("modo"), "modo_analise": escopo.get("modo_analise"),
                 "paginas": escopo.get("paginas"), "objetivo": escopo.get("objetivo")},
        "nota_geral": nota_geral, "faixa": faixa, "tetos_aplicados": tetos_aplicados,
        "pesos_usados": pesos, "notas_segmento": notas,
        "estatisticas": {"total_achados": len(todos), "por_severidade": por_sev,
                         "por_prioridade": {p: sum(1 for a in todos if a["prioridade"] == p) for p in ("P1", "P2", "P3")},
                         "juntados_por_duplicidade": juntados,
                         "juntados_detalhe": {"manual": rel_dup["manual"], "automatico": rel_dup["automatico"]},
                         "candidatos_a_conferir": len(rel_dup["candidatos"]), "descartados_na_verificacao": len(descartados)},
        "achados": todos, "pontos_fortes": pontos_fortes, "cobertura": cobertura, "extras": extras,
        "descartados": descartados, "avisos_validacao": avisos,
    }
    (saida / "consolidado.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Nota geral: {nota_geral} ({faixa}) | achados: {len(todos)} {por_sev} | juntados: {juntados} | "
          f"descartados: {len(descartados)} | avisos de validação: {len(avisos)}")
    for j in rel_dup["automatico"]:
        print(f"  juntado automaticamente: {j['mantido']} + {j['juntados']} (pontuação {j.get('pontuacao', 'regra exata')})")
    if rel_dup["candidatos"]:
        print(f"  {len(rel_dup['candidatos'])} candidatos a duplicado em duplicados-candidatos.json: confira e grave os confirmados em duplicados.json")
    for a in avisos[:20]:
        print("  aviso:", a)


if __name__ == "__main__":
    main()
