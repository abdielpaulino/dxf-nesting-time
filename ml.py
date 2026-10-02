"""
Estimativa do tempo real de corte a laser (regressão): do dado bruto ao benchmark de modelos.

Pipeline (slide do professor):
    1. Coleta e limpeza mínima      -> carregar_dados(), limpar()
    2. Split inicial (por desenho)  -> dividir()
    3. Features                     -> com_tempo_teorico()
    4. Modelos, um por seção        -> treinar_formula_fixa(), treinar_linear_simples(),
                                       treinar_linear_multipla(), treinar_polinomial_multipla()
    5. Validação cruzada (treino)   -> validar()
    6. Avaliação final (teste)      -> avaliar_no_teste()   (aberta uma única vez)
    7. Gráficos de erro             -> gerar_graficos()     (salvos em figuras/)

A EDA (distribuições, outliers, correlações, leakage, drift) fica em main.ipynb.

Rodar da raiz do projeto:
    backend/.venv/bin/python ml.py              # salva os gráficos em figuras/
    backend/.venv/bin/python ml.py --mostrar    # também abre as janelas dos gráficos
"""

import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, r2_score, root_mean_squared_error
from sklearn.model_selection import GroupKFold, GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, PolynomialFeatures, StandardScaler

SEED = 42
ALVO = 'Tempo Real Minutos'
GRUPO = 'Plano Desenho'
URL_DATASET = 'https://raw.githubusercontent.com/abdielpaulino/dxf-nesting-time/main/files/dataset.xlsx'
CAMINHOS_DATASET = [Path('/content/dataset.xlsx'), Path('files/dataset.xlsx'), Path('dataset.xlsx')]
PASTA_FIGURAS = Path('figuras')

COLS_TEXTO = ['Material', 'Espessura', 'Gás Auxiliar', 'Tipo Bocal', 'Tipo de Acabamento', 'Plano Desenho']
COLS_NUM = [
    'Potência Laser (W)', 'Pressão Gás (bar)', 'Velocidade Corte (m/min)', 'Posição Foco (mm)',
    'Diâmetro Bocal (mm)', 'Distância Bocal (mm)', 'Perimetro (mm)',
    'Tempo Corte Estimado Segundos', 'Tempo Real Segundos',
    'Tempo Corte Estimado Minutos', 'Tempo Real Minutos', 'Diferença de Tempo Minutos',
]

# Features dos modelos. Tipo Bocal e Acabamento são função de Material + Gás (redundantes).
# As colunas de tempo (real em segundos, estimado, diferença) ficam de fora: leakage ou a própria fórmula.
FEATURES_NUM = ['Potência Laser (W)', 'Pressão Gás (bar)', 'Velocidade Corte (m/min)', 'Posição Foco (mm)',
                'Diâmetro Bocal (mm)', 'Distância Bocal (mm)', 'Espessura (mm)', 'Perimetro (mm)', 'tempo_teorico_min']
FEATURES_CAT = ['Material', 'Gás Auxiliar']


# ============================================================================
# 1. COLETA E LIMPEZA MÍNIMA (determinística; nunca imputa nem remove outliers)
# ============================================================================
def carregar_dados() -> pd.DataFrame:
    """Usa o arquivo local se existir; senão baixa do GitHub (repositório público)."""
    caminho = next((p for p in CAMINHOS_DATASET if p.exists()), None)
    if caminho is None:
        caminho = Path('dataset.xlsx')
        print('Baixando dataset do GitHub...')
        urllib.request.urlretrieve(URL_DATASET, caminho)
    df = pd.read_excel(caminho, sheet_name='Matriz_Completa')
    print(f'Lido de {caminho}: {df.shape[0]:,} linhas x {df.shape[1]} colunas')
    return df


def limpar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    log = {'linhas_iniciais': len(df)}

    # duplicatas exatas
    log['duplicatas_removidas'] = int(df.duplicated().sum())
    df = df.drop_duplicates().reset_index(drop=True)

    # strings: trim e espaços duplicados
    for c in COLS_TEXTO:
        df[c] = df[c].astype('string').str.strip().str.replace(r'\s+', ' ', regex=True).replace('', pd.NA)

    # números: vírgula decimal -> ponto, tudo float
    for c in COLS_NUM:
        if not pd.api.types.is_numeric_dtype(df[c]):
            df[c] = df[c].astype('string').str.strip().str.replace(',', '.', regex=False)
        df[c] = pd.to_numeric(df[c], errors='coerce').astype('float64')

    # espessura em mm: '3,18 mm (1/8")' -> 3.18
    df['Espessura (mm)'] = pd.to_numeric(
        df['Espessura'].str.extract(r'^\s*([\d]+(?:[.,]\d+)?)\s*mm', expand=False).str.replace(',', '.'),
        errors='coerce',
    ).astype('float64')
    df[COLS_TEXTO] = df[COLS_TEXTO].astype('category')

    # valores impossíveis -> NaN (limites físicos, não estatísticos)
    numericas = COLS_NUM + ['Espessura (mm)']
    df[numericas] = df[numericas].replace([np.inf, -np.inf], np.nan)
    positivo_estrito = ['Potência Laser (W)', 'Velocidade Corte (m/min)', 'Perimetro (mm)', 'Diâmetro Bocal (mm)', 'Espessura (mm)',
                        'Tempo Corte Estimado Segundos', 'Tempo Real Segundos', 'Tempo Corte Estimado Minutos', 'Tempo Real Minutos']
    nao_negativo = ['Pressão Gás (bar)', 'Distância Bocal (mm)']   # 'Diferença de Tempo' pode ser negativa
    impossiveis = 0
    for c in positivo_estrito:
        m = df[c] <= 0
        impossiveis += int(m.sum()); df.loc[m, c] = np.nan
    for c in nao_negativo:
        m = df[c] < 0
        impossiveis += int(m.sum()); df.loc[m, c] = np.nan
    log['valores_impossiveis_viraram_nan'] = impossiveis

    # linhas totalmente ruins: sem alvo, sem desenho nem perímetro, ou todas as numéricas faltando
    ruins = df[ALVO].isna() | (df[GRUPO].isna() & df['Perimetro (mm)'].isna()) | df[COLS_NUM].isna().all(axis=1)
    log['linhas_ruins_descartadas'] = int(ruins.sum())
    df = df.loc[~ruins].reset_index(drop=True)

    log['linhas_finais'] = len(df)
    print('Limpeza:', log)
    return df


# ============================================================================
# 2. SPLIT INICIAL (por desenho: o mesmo desenho nunca está no treino e no teste)
# ============================================================================
def dividir(df: pd.DataFrame, tam_teste: float = 0.2):
    grupos = df[GRUPO].astype(str)
    i_treino, i_teste = next(GroupShuffleSplit(n_splits=1, test_size=tam_teste, random_state=SEED).split(df, groups=grupos))
    assert not set(grupos.iloc[i_treino]) & set(grupos.iloc[i_teste]), 'desenho repetido entre treino e teste'
    treino, teste = df.iloc[i_treino].copy(), df.iloc[i_teste].copy()
    for nome, d in [('treino', treino), ('teste', teste)]:
        print(f'{nome:6s} linhas={len(d):>7,}  desenhos={d[GRUPO].nunique():>4}  ({len(d) / len(df):.0%})')
    return treino, teste


# ============================================================================
# 3. FEATURES
# ============================================================================
def com_tempo_teorico(d: pd.DataFrame) -> pd.DataFrame:
    """tempo teórico (min) = perímetro (mm) / (velocidade (m/min) * 1000)"""
    d = d.copy()
    d['tempo_teorico_min'] = d['Perimetro (mm)'] / (d['Velocidade Corte (m/min)'] * 1000)
    return d


def pre_processador(grau: int | None = None) -> ColumnTransformer:
    """Numéricas padronizadas (com termos polinomiais se `grau`) + one-hot de Material e Gás. Ajustado só no treino."""
    if grau is None:
        numericas = StandardScaler()
    else:
        numericas = Pipeline([('escala', StandardScaler()),
                              ('polinomio', PolynomialFeatures(degree=grau, include_bias=False))])
    return ColumnTransformer([
        ('num', numericas, FEATURES_NUM),
        ('cat', OneHotEncoder(drop='first', handle_unknown='ignore'), FEATURES_CAT),
    ])


# ============================================================================
# 4. MODELOS: cada um com a sua função de treino.
#    Contrato: treinar_X(X_treino, y_treino) -> prever(X) -> np.ndarray
# ============================================================================
def treinar_formula_fixa(X, y):
    """Referência, sem treino: tempo = perímetro / velocidade."""
    return lambda X_novo: X_novo['tempo_teorico_min'].to_numpy()


def treinar_linear_simples(X, y):
    """Regressão linear simples: uma única variável, o tempo teórico."""
    modelo = Pipeline([
        ('colunas', ColumnTransformer([('x', 'passthrough', ['tempo_teorico_min'])])),
        ('regressao', LinearRegression()),
    ])
    return modelo.fit(X, y).predict


def treinar_linear_multipla(X, y):
    """Regressão linear múltipla: parâmetros de corte + perímetro + tempo teórico + Material/Gás."""
    modelo = Pipeline([('pre', pre_processador()), ('regressao', LinearRegression())])
    return modelo.fit(X, y).predict


def treinar_polinomial_multipla(X, y, grau: int = 2):
    """Regressão polinomial múltipla: as mesmas variáveis, com quadrados e interações entre as numéricas."""
    modelo = Pipeline([('pre', pre_processador(grau=grau)), ('regressao', LinearRegression())])
    return modelo.fit(X, y).predict


MODELOS = {
    '1. Fórmula fixa': treinar_formula_fixa,
    '2. Linear simples': treinar_linear_simples,
    '3. Linear múltipla': treinar_linear_multipla,
    '4. Polinomial múltipla (grau 2)': treinar_polinomial_multipla,
}
NOMES_CURTOS = {'1. Fórmula fixa': 'Fórmula fixa', '2. Linear simples': 'Linear simples',
                '3. Linear múltipla': 'Linear múltipla', '4. Polinomial múltipla (grau 2)': 'Polinomial múltipla'}


# ============================================================================
# 5. VALIDAÇÃO CRUZADA POR DESENHO (só no treino; o teste fica fechado)
# ============================================================================
def metricas(y, pred) -> dict:
    return {'MAE': mean_absolute_error(y, pred), 'RMSE': root_mean_squared_error(y, pred),
            'MAPE_%': mean_absolute_percentage_error(y, pred) * 100, 'R2': r2_score(y, pred)}


def validar(treino: pd.DataFrame, n_folds: int = 5):
    """Treina cada modelo em cada fold. Devolve a tabela de métricas e as previsões fora-da-amostra (oof)."""
    X, y, grupos = treino[FEATURES_NUM + FEATURES_CAT], treino[ALVO], treino[GRUPO].astype(str)
    resultados, oof = {}, {}
    for nome, treinar in MODELOS.items():
        folds, pred_oof = [], np.full(len(y), np.nan)
        for i_tr, i_va in GroupKFold(n_splits=n_folds).split(X, y, groups=grupos):
            prever = treinar(X.iloc[i_tr], y.iloc[i_tr])
            pred = np.asarray(prever(X.iloc[i_va]))
            pred_oof[i_va] = pred
            folds.append(metricas(y.iloc[i_va], pred))
        resultados[nome] = pd.DataFrame(folds).mean().to_dict()
        oof[nome] = pd.Series(pred_oof, index=y.index)
    return pd.DataFrame(resultados).T, oof


# ============================================================================
# 6. AVALIAÇÃO FINAL NO TESTE (aberta uma única vez, com cada modelo treinado no treino inteiro)
# ============================================================================
def avaliar_no_teste(treino: pd.DataFrame, teste: pd.DataFrame) -> pd.DataFrame:
    X_tr, y_tr = treino[FEATURES_NUM + FEATURES_CAT], treino[ALVO]
    X_te, y_te = teste[FEATURES_NUM + FEATURES_CAT], teste[ALVO]
    return pd.DataFrame({nome: metricas(y_te, treinar(X_tr, y_tr)(X_te)) for nome, treinar in MODELOS.items()}).T


# ============================================================================
# 7. GRÁFICOS DE ERRO (previsões fora-da-amostra do treino; salvos em figuras/)
# ============================================================================
COR = {'azul': '#2a78d6', 'laranja': '#eb6834', 'verde': '#1baf7a', 'cinza': '#8a8984',
       'texto': '#0b0b0b', 'texto2': '#52514e', 'grade': '#e6e5e1'}


def gerar_graficos(treino: pd.DataFrame, tabela: pd.DataFrame, oof: dict, mostrar: bool = False):
    import matplotlib
    if not mostrar:
        matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from cycler import cycler
    from matplotlib.ticker import NullFormatter

    plt.rcParams.update({
        'figure.dpi': 100, 'savefig.dpi': 150, 'savefig.bbox': 'tight', 'figure.facecolor': 'white',
        'axes.prop_cycle': cycler(color=[COR['azul'], COR['laranja'], COR['verde']]),
        'axes.grid': True, 'grid.color': COR['grade'], 'axes.axisbelow': True,
        'axes.spines.top': False, 'axes.spines.right': False, 'axes.edgecolor': COR['cinza'],
        'axes.labelcolor': COR['texto2'], 'xtick.color': COR['texto2'], 'ytick.color': COR['texto2'],
        'axes.titlesize': 11, 'axes.titleweight': 'bold', 'axes.titlelocation': 'left',
    })
    PASTA_FIGURAS.mkdir(exist_ok=True)
    y = treino[ALVO]
    piso = 1e-3   # previsões lineares podem ficar <= 0 em peças minúsculas; só para exibir em escala log

    def finalizar(fig, nome, titulo):
        fig.suptitle(titulo, x=0.01, ha='left', fontsize=13, fontweight='bold', y=1.03)
        plt.tight_layout(); fig.savefig(PASTA_FIGURAS / f'{nome}.png')
        if mostrar: plt.show()
        plt.close(fig)

    # (a) comparação das métricas
    fig, axs = plt.subplots(1, 3, figsize=(14, 4))
    for ax, (met, titulo, fmt) in zip(axs, [('MAE', 'Erro médio absoluto (minutos)', '{:.2f}'), ('RMSE', 'RMSE (minutos)', '{:.2f}'),
                                            ('MAPE_%', 'Erro percentual médio (%)', '{:.0f}%')]):
        nomes = [NOMES_CURTOS[n] for n in tabela.index]
        barras = ax.bar(nomes, tabela[met].values, width=0.62, color=[COR['cinza']] + [COR['azul']] * (len(nomes) - 1))
        for b, v in zip(barras, tabela[met].values):
            ax.text(b.get_x() + b.get_width() / 2, v, fmt.format(v), ha='center', va='bottom', fontsize=10)
        ax.set_title(titulo); ax.tick_params(axis='x', rotation=22); ax.grid(axis='x', visible=False)
        ax.set_ylim(0, tabela[met].max() * 1.15)
    finalizar(fig, 'erro_comparacao_modelos', 'Calibrar o tempo teórico corta o erro em ~80%; modelos mais complexos quase não melhoram')

    # (b) real x previsto
    amostra = y.sample(25000, random_state=0).index
    lim = [0.002, 400]
    fig, axs = plt.subplots(1, 4, figsize=(17, 4.4), sharex=True, sharey=True)
    for ax, (nome, pred) in zip(axs, oof.items()):
        ax.scatter(y.loc[amostra], pred.loc[amostra].clip(lower=piso), s=2, alpha=0.15, rasterized=True,
                   color=COR['cinza'] if nome == '1. Fórmula fixa' else COR['azul'])
        ax.plot(lim, lim, color=COR['texto'], lw=1, ls='--')
        ax.set_xscale('log'); ax.set_yscale('log'); ax.set_xlim(lim); ax.set_ylim(lim)
        ax.set_title(NOMES_CURTOS[nome]); ax.set_xlabel('Tempo real (min)')
    axs[0].set_ylabel('Tempo previsto (min)')
    finalizar(fig, 'erro_real_vs_previsto', 'Real x previsto: os modelos colam na diagonal, mas não preveem menos que ~0,17 min (peças muito pequenas ficam acima)')

    # (c) distribuição do erro em "vezes" (previsto / real)
    bins = np.linspace(-1.2, 1.2, 80)
    fig, axs = plt.subplots(1, 4, figsize=(17, 4), sharex=True, sharey=True)
    for ax, (nome, pred) in zip(axs, oof.items()):
        r = np.log10(pred.clip(lower=piso) / y)
        ax.hist(r.clip(-1.2, 1.2), bins=bins, color=COR['cinza'] if nome == '1. Fórmula fixa' else COR['azul'])
        ax.axvline(0, color=COR['texto'], lw=1, ls='--')
        ax.text(0.97, 0.93, f'mediana: {10 ** r.median():.2f}× o real', transform=ax.transAxes, ha='right', va='top', fontsize=10)
        ax.set_title(NOMES_CURTOS[nome]); ax.set_yticks([])
        ax.set_xticks([-1, -np.log10(2), 0, np.log10(2), 1])
        ax.set_xticklabels(['10× menor', '2× menor', 'acerto', '2× maior', '10× maior'], rotation=30)
    finalizar(fig, 'erro_distribuicao_razao', 'A fórmula fixa subestima o tempo na quase totalidade das linhas; os modelos treinados ficam perto do acerto')

    # (d) erro por tamanho da peça (faixas de perímetro com o mesmo nº de linhas)
    faixa = pd.qcut(treino['Perimetro (mm)'], 5)
    rotulos = [f'{iv.left / 1000:.1f}–{iv.right / 1000:.1f} m' for iv in faixa.cat.categories]
    por_faixa = {'MAE': {}, 'MAPE': {}}
    for nome, pred in oof.items():
        d = pd.DataFrame({'real': y, 'pred': pred, 'faixa': faixa})
        d['abs'] = (d['pred'] - d['real']).abs()
        g = d.groupby('faixa', observed=True)
        por_faixa['MAE'][nome] = g['abs'].mean().values
        por_faixa['MAPE'][nome] = (g.apply(lambda x: (x['abs'] / x['real']).mean()) * 100).values
    estilos = {'1. Fórmula fixa': (COR['cinza'], '--'), '2. Linear simples': (COR['azul'], '-'),
               '3. Linear múltipla': (COR['laranja'], '-'), '4. Polinomial múltipla (grau 2)': (COR['verde'], '-')}
    fig, axs = plt.subplots(1, 2, figsize=(14, 4.8))
    for ax, (met, titulo) in zip(axs, [('MAE', 'Erro médio absoluto (minutos, escala log)'), ('MAPE', 'Erro percentual médio (%)')]):
        for nome, valores in por_faixa[met].items():
            cor, ls = estilos[nome]
            ax.plot(rotulos, valores, color=cor, ls=ls, lw=2, marker='o', ms=7, mfc=cor, mec='white', mew=1.5, label=NOMES_CURTOS[nome])
        ax.set_title(titulo); ax.tick_params(axis='x', rotation=15)
        ax.set_xlabel('Perímetro da peça (faixas de mesmo tamanho: menores → maiores)')
    axs[0].set_yscale('log'); axs[0].set_yticks([0.1, 0.2, 0.5, 1, 2, 3])
    axs[0].set_yticklabels(['0,1', '0,2', '0,5', '1', '2', '3']); axs[0].yaxis.set_minor_formatter(NullFormatter())
    axs[1].legend(frameon=False, loc='upper right')
    finalizar(fig, 'erro_por_tamanho', 'Em valor absoluto o erro cresce com a peça; em percentual, o problema são as peças pequenas')
    print(f'Gráficos salvos em {PASTA_FIGURAS}/')


# ============================================================================
def main():
    pd.set_option('display.float_format', lambda x: f'{x:,.4f}')

    df = limpar(carregar_dados())
    treino, teste = dividir(df)
    treino, teste = com_tempo_teorico(treino), com_tempo_teorico(teste)

    print('\n=== Validação cruzada por desenho (5 folds, só no treino) ===')
    tabela, oof = validar(treino)
    print(tabela)

    print('\n=== Avaliação final no teste (aberta uma única vez) ===')
    print(avaliar_no_teste(treino, teste))

    gerar_graficos(treino, tabela, oof, mostrar='--mostrar' in sys.argv)


if __name__ == '__main__':
    main()
