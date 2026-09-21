import json
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dxf_analyzer import analisar_dxf_bytes

BASE_DIR = Path(__file__).resolve().parent
PARAMETROS_PATH = BASE_DIR.parent / "frontend" / "src" / "data" / "parametros_corte.json"

TEMPO_PERFURACAO_S = 1.5

app = FastAPI(title="Estimador de Tempo de Corte a Laser - API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def carregar_parametros() -> list[dict]:
    with open(PARAMETROS_PATH, encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/parametros")
def listar_parametros():
    return carregar_parametros()


@app.post("/api/dxf/analisar")
async def analisar_dxf(arquivo: UploadFile = File(...)):
    if not arquivo.filename.lower().endswith(".dxf"):
        raise HTTPException(status_code=400, detail="Envie um arquivo .dxf")

    conteudo = await arquivo.read()
    try:
        return analisar_dxf_bytes(conteudo, arquivo.filename)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Erro ao processar DXF: {exc}") from exc


class GeometriaIn(BaseModel):
    comprimentoMm: float
    numFuros: int
    quantidade: int = 1


class EstimativaIn(BaseModel):
    material: str
    espessuraDisplay: str
    potencia: float
    gas: str
    geometria: GeometriaIn


def formatar_min(minutos: float) -> str:
    total_seg = round(minutos * 60)
    m, s = divmod(total_seg, 60)
    return f"{m}min {s:02d}s"


@app.post("/api/estimativa")
def calcular_estimativa(payload: EstimativaIn):
    parametro = next(
        (
            p
            for p in carregar_parametros()
            if p["material"] == payload.material
            and p["espessura_display"] == payload.espessuraDisplay
            and p["potencia_w"] == payload.potencia
            and p["gas_auxiliar"] == payload.gas
        ),
        None,
    )
    if parametro is None:
        raise HTTPException(status_code=404, detail="Parâmetro não encontrado para a combinação selecionada")

    velocidade_mm_min = parametro["velocidade_corte_m_min"] * 1000
    geometria = payload.geometria

    tempo_corte_min = geometria.comprimentoMm / velocidade_mm_min if velocidade_mm_min > 0 else 0
    tempo_perfuracao_min = (geometria.numFuros * TEMPO_PERFURACAO_S) / 60
    tempo_total_min = (tempo_corte_min + tempo_perfuracao_min) * geometria.quantidade

    return {
        "parametro": parametro,
        "geometria": geometria.model_dump(),
        "tempoCorteMin": round(tempo_corte_min, 4),
        "tempoPerfuracaoMin": round(tempo_perfuracao_min, 4),
        "tempoTotalMin": round(tempo_total_min, 4),
        "tempoTotalFormatado": formatar_min(tempo_total_min),
    }
