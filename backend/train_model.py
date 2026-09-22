"""
Treina um Random Forest para prever o tempo real de corte a laser.

Usa files/dataset.xlsx (406 combinações de parâmetros de corte x 435 desenhos
DXF, com o tempo real medido em cada combinação) como dados de treino, e o
número de furos de cada desenho (extraído via dxf_analyzer) como feature
extra, já que o dataset só traz o perímetro.

Uso:
    cd backend
    .venv/bin/python train_model.py
"""

import time
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from dxf_analyzer import analisar_dxf_bytes

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR.parent / "files" / "dataset.xlsx"
DRAWINGS_DIR = BASE_DIR.parent / "files" / "drawings-dxf"
MODEL_DIR = BASE_DIR / "model"
MODEL_PATH = MODEL_DIR / "random_forest_tempo.joblib"

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
COLUNA_ALVO = "Tempo Real Minutos"


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


def treinar():
    df = carregar_dataset()

    X = df[COLUNAS_CATEGORICAS + COLUNAS_NUMERICAS]
    y = df[COLUNA_ALVO]

    X_train, X_test, y_train, y_test, df_train, df_test = train_test_split(
        X, y, df, test_size=0.2, random_state=42
    )

    pre_processador = ColumnTransformer(
        transformers=[
            ("categoricas", OneHotEncoder(handle_unknown="ignore"), COLUNAS_CATEGORICAS),
        ],
        remainder="passthrough",
    )

    modelo = Pipeline(
        steps=[
            ("pre_processador", pre_processador),
            (
                "random_forest",
                RandomForestRegressor(n_estimators=300, max_depth=None, random_state=42, n_jobs=-1),
            ),
        ]
    )

    print(f"Treinando com {len(X_train)} amostras, testando com {len(X_test)}...")
    inicio = time.time()
    modelo.fit(X_train, y_train)
    print(f"Treino concluído em {time.time() - inicio:.1f}s")

    y_pred = modelo.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = root_mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    baseline_pred = df_test["Tempo Corte Estimado Minutos"]
    mae_baseline = mean_absolute_error(y_test, baseline_pred)
    rmse_baseline = root_mean_squared_error(y_test, baseline_pred)
    r2_baseline = r2_score(y_test, baseline_pred)

    print("\n=== Random Forest (Tempo Real Minutos) ===")
    print(f"MAE:  {mae:.4f} min")
    print(f"RMSE: {rmse:.4f} min")
    print(f"R²:   {r2:.4f}")

    print("\n=== Baseline: fórmula fixa atual (comprimento/velocidade + furos) ===")
    print(f"MAE:  {mae_baseline:.4f} min")
    print(f"RMSE: {rmse_baseline:.4f} min")
    print(f"R²:   {r2_baseline:.4f}")

    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump(modelo, MODEL_PATH)
    print(f"\nModelo salvo em {MODEL_PATH}")


if __name__ == "__main__":
    treinar()
