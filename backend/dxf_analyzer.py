import math
import tempfile
from collections import defaultdict
from pathlib import Path

import ezdxf
from ezdxf import path as ezdxf_path


def _pontos_via_path(entidade, tolerancia=0.01):
    try:
        p = ezdxf_path.make_path(entidade)
    except Exception:
        return []
    return [(pt.x, pt.y) for pt in p.flattening(tolerancia)]


def _comprimento(pontos):
    if len(pontos) < 2:
        return 0.0
    return sum(math.dist(pontos[i], pontos[i + 1]) for i in range(len(pontos) - 1))


def _processar_entidades(entidades, nome_peca, dados_layer, dados_peca, contador_furos, segmentos, profundidade=0):
    total = 0.0
    for e in entidades:
        tipo = e.dxftype()
        if tipo == "INSERT":
            sub_nome = nome_peca if profundidade > 0 else e.dxf.name
            try:
                filhos = e.virtual_entities()
                total += _processar_entidades(
                    filhos, sub_nome, dados_layer, dados_peca, contador_furos, segmentos, profundidade + 1
                )
            except Exception:
                pass
        else:
            if tipo == "CIRCLE":
                contador_furos[0] += 1
            pontos = _pontos_via_path(e)
            comp = _comprimento(pontos)
            if comp > 0.0:
                camada = getattr(e.dxf, "layer", "0")
                dados_layer[camada] += comp
                dados_peca[nome_peca] += comp
                total += comp
                segmentos.append(pontos)
    return total


def analisar_dxf_bytes(conteudo: bytes, nome_arquivo: str) -> dict:
    sufixo = Path(nome_arquivo).suffix or ".dxf"
    with tempfile.NamedTemporaryFile(suffix=sufixo, delete=False) as tmp:
        tmp.write(conteudo)
        caminho_tmp = tmp.name

    try:
        doc = ezdxf.readfile(caminho_tmp)
    finally:
        Path(caminho_tmp).unlink(missing_ok=True)

    msp = doc.modelspace()
    nome_base = Path(nome_arquivo).stem

    dados_layer = defaultdict(float)
    dados_peca = defaultdict(float)
    contador_furos = [0]
    segmentos = []

    perimetro_total = _processar_entidades(
        msp, nome_base, dados_layer, dados_peca, contador_furos, segmentos
    )

    todos_pontos = [pt for seg in segmentos for pt in seg]
    if todos_pontos:
        xs = [pt[0] for pt in todos_pontos]
        ys = [pt[1] for pt in todos_pontos]
        bbox = {"minX": min(xs), "minY": min(ys), "maxX": max(xs), "maxY": max(ys)}
    else:
        bbox = None

    return {
        "arquivo": nome_arquivo,
        "comprimentoMm": round(perimetro_total, 2),
        "numFuros": contador_furos[0],
        "quantidade": 1,
        "porLayer": {k: round(v, 2) for k, v in dados_layer.items()},
        "porPeca": {
            ("Bloco raiz" if k == nome_base else k): round(v, 2) for k, v in dados_peca.items()
        },
        "desenho": {
            "segmentos": [[[round(x, 3), round(y, 3)] for x, y in seg] for seg in segmentos],
            "bbox": bbox,
        },
    }
