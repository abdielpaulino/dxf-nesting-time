"""
Treina e compara (benchmark) modelos de regressão para prever o tempo real de
corte a laser:

- Regressão linear simples: uma única feature (Perímetro).
- Regressão linear múltipla: todos os parâmetros de corte + perímetro + furos.
- Regressão polinomial múltipla: as mesmas features, com termos de grau 2
  (quadrados e interações) nas colunas numéricas.

Usa files/dataset.xlsx (406 combinações de parâmetros de corte x 435 desenhos
DXF, com o tempo real medido em cada combinação) como dados de treino, e o
número de furos de cada desenho (extraído via dxf_analyzer) como feature
extra, já que o dataset só traz o perímetro.

Uso:
    cd backend
    .venv/bin/python train_model.py
"""

import json
import time
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, PolynomialFeatures, StandardScaler

from dxf_analyzer import analisar_dxf_bytes

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR.parent / "files" / "dataset.xlsx"
DRAWINGS_DIR = BASE_DIR.parent / "files" / "drawings-dxf"
MODEL_DIR = BASE_DIR / "model"
BENCHMARK_PATH = MODEL_DIR / "benchmark.json"

COLUNAS_CATEGORICAS = ["Material", "Espessura", "Gás Auxiliar", "Tipo Bocal", "Tipo de Acabamento"]
COLUNAS_NUMERICAS = [
    "Potência Laser (W)",
    "Pressão Gás (bar)",
    "Velocidade Corte (m/min)",
    "Posição Foco (mm)",
    "Diâmetro Bocal (mm)",
    "Distância Bocal (mm)",
    "Perimetro (mm)",
    "numFuros",
]
COLUNA_REGRESSAO_SIMPLES = "Perimetro (mm)"
COLUNA_ALVO = "Tempo Real Minutos"
GRAU_POLINOMIAL = 2


def contar_furos_por_desenho(nomes_desenho: list[str]) -> dict[str, int]:
    """Roda o mesmo parser DXF usado na API para extrair numFuros de cada peça."""
    furos_por_desenho = {}
    for nome in nomes_desenho:
        caminho = DRAWINGS_DIR / f"{nome}.dxf"
        conteudo = caminho.read_bytes()
        resultado = analisar_dxf_bytes(conteudo, caminho.name)
        furos_por_desenho[nome] = resultado["numFuros"]
    return furos_por_desenho


def carregar_dataset() -> pd.DataFrame:
    df = pd.read_excel(DATASET_PATH, sheet_name="Matriz_Completa")

    nomes_desenho = sorted(df["Plano Desenho"].unique())
    print(f"Extraindo numFuros de {len(nomes_desenho)} desenhos DXF...")
    furos_por_desenho = contar_furos_por_desenho(nomes_desenho)
    df["numFuros"] = df["Plano Desenho"].map(furos_por_desenho)

    return df


def criar_modelos() -> dict[str, dict]:
    """Cada modelo recebe o DataFrame completo de features e seleciona as colunas que usa."""
    regressao_simples = Pipeline(
        steps=[
            (
                "pre_processador",
                ColumnTransformer([("simples", "passthrough", [COLUNA_REGRESSAO_SIMPLES])]),
            ),
            ("regressao", LinearRegression()),
        ]
    )

    regressao_multipla = Pipeline(
        steps=[
            (
                "pre_processador",
                ColumnTransformer(
                    [
                        ("categoricas", OneHotEncoder(handle_unknown="ignore"), COLUNAS_CATEGORICAS),
                        ("numericas", "passthrough", COLUNAS_NUMERICAS),
                    ]
                ),
            ),
            ("regressao", LinearRegression()),
        ]
    )

    regressao_polinomial_multipla = Pipeline(
        steps=[
            (
                "pre_processador",
                ColumnTransformer(
                    [
                        ("categoricas", OneHotEncoder(handle_unknown="ignore"), COLUNAS_CATEGORICAS),
                        (
                            "numericas",
                            Pipeline(
                                steps=[
                                    ("escala", StandardScaler()),
                                    ("polinomio", PolynomialFeatures(degree=GRAU_POLINOMIAL, include_bias=False)),
                                ]
                            ),
                            COLUNAS_NUMERICAS,
                        ),
                    ]
                ),
            ),
            ("regressao", LinearRegression()),
        ]
    )

    return {
        "regressao_simples": {
            "nome": f"Regressão Linear Simples ({COLUNA_REGRESSAO_SIMPLES})",
            "modelo": regressao_simples,
        },
        "regressao_multipla": {
            "nome": "Regressão Linear Múltipla",
            "modelo": regressao_multipla,
        },
        "regressao_polinomial_multipla": {
            "nome": f"Regressão Polinomial Múltipla (grau {GRAU_POLINOMIAL})",
            "modelo": regressao_polinomial_multipla,
        },
    }


def calcular_metricas(y_true, y_pred) -> dict[str, float]:
    return {
        "mae": mean_absolute_error(y_true, y_pred),
        "rmse": root_mean_squared_error(y_true, y_pred),
        "r2": r2_score(y_true, y_pred),
    }


def imprimir_tabela(resultados: list[dict]):
    largura_nome = max(len(r["nome"]) for r in resultados)
    cabecalho = f"{'Modelo':<{largura_nome}}  {'MAE (min)':>10}  {'RMSE (min)':>10}  {'R²':>8}  {'Treino (s)':>10}"
    print("\n=== Benchmark (conjunto de teste, alvo: Tempo Real Minutos) ===")
    print(cabecalho)
    print("-" * len(cabecalho))
    for r in sorted(resultados, key=lambda r: r["rmse"]):
        tempo = f"{r['tempoTreinoS']:.2f}" if r["tempoTreinoS"] is not None else "-"
        print(
            f"{r['nome']:<{largura_nome}}  {r['mae']:>10.4f}  {r['rmse']:>10.4f}  {r['r2']:>8.4f}  {tempo:>10}"
        )


def treinar():
    df = carregar_dataset()

    X = df[COLUNAS_CATEGORICAS + COLUNAS_NUMERICAS]
    y = df[COLUNA_ALVO]

    X_train, X_test, y_train, y_test, df_train, df_test = train_test_split(
        X, y, df, test_size=0.2, random_state=42
    )
    print(f"Treinando com {len(X_train)} amostras, testando com {len(X_test)}...")

    MODEL_DIR.mkdir(exist_ok=True)
    resultados = []

    for chave, info in criar_modelos().items():
        modelo = info["modelo"]
        inicio = time.time()
        modelo.fit(X_train, y_train)
        tempo_treino = time.time() - inicio

        metricas = calcular_metricas(y_test, modelo.predict(X_test))
        resultados.append({"id": chave, "nome": info["nome"], **metricas, "tempoTreinoS": tempo_treino})

        joblib.dump(modelo, MODEL_DIR / f"{chave}.joblib")
        print(f"- {info['nome']}: treinado em {tempo_treino:.2f}s, salvo em model/{chave}.joblib")

    baseline = calcular_metricas(y_test, df_test["Tempo Corte Estimado Minutos"])
    resultados.append(
        {
            "id": "formula_fixa",
            "nome": "Baseline: fórmula fixa (comprimento/velocidade)",
            **baseline,
            "tempoTreinoS": None,
        }
    )

    imprimir_tabela(resultados)

    BENCHMARK_PATH.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nBenchmark salvo em {BENCHMARK_PATH}")


if __name__ == "__main__":
    treinar()
