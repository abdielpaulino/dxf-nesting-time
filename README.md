# ✂️ Estimador de Tempo de Corte a Laser

App **React + Vite (front-end)** com **FastAPI (back-end)** para estimar o tempo de corte a laser com base em parâmetros de máquina (material, espessura, potência, gás) e em um desenho técnico **DXF**.

> Estágio atual: front-end e back-end integrados. O back-end lê o `.dxf` de verdade (via `ezdxf`), calcula o tempo com a fórmula fixa e também com **modelos de regressão** treinados em `files/dataset.xlsx`. O benchmark dos modelos (fórmula fixa, linear simples, linear múltipla e polinomial múltipla) está em `main.ipynb` e `ml.py`.

---

## 🧩 Como funciona

O app tem três etapas, uma abaixo da outra:

| #   | Etapa                                                           | Componente                |
| --- | --------------------------------------------------------------- | ------------------------- |
| 1   | Seleção em cascata de **Material → Espessura → Potência → Gás** | `ParametrosSelector.jsx`  |
| 2   | Upload do desenho **`.dxf`** (arrastar ou clicar)               | `DxfUpload.jsx`           |
| 3   | Exibição do **tempo total estimado**                            | `ResultadoEstimativa.jsx` |

---

## 🤖 Como a estimativa é calculada

A tabela de parâmetros (`frontend/src/data/parametros_corte.json`) **não é a fonte do tempo estimado** — ela serve apenas para popular os dropdowns da etapa 1 (quais materiais, espessuras, potências e gases existem) e é lida pelo back-end como base de consulta.

O cálculo roda inteiramente no **back-end (Python)**, não no navegador:

1. O front envia o `.dxf` para `POST /api/dxf/analisar`, que usa `ezdxf` para extrair o perímetro total (mm) e o número de furos (círculos), percorrendo inclusive blocos (`INSERT`) aninhados.
2. O front envia os parâmetros selecionados + a geometria extraída para `POST /api/estimativa`, que busca a linha correspondente em `parametros_corte.json` e calcula o tempo de corte + perfuração com uma fórmula fixa (`comprimento / velocidade_corte` + `furos × tempo_de_perfuração`).
3. Existe também `POST /api/estimativa/ml`, com o mesmo payload de entrada, que roda três modelos de regressão treinados em `files/dataset.xlsx` (176 mil linhas: 406 combinações de parâmetros × 435 desenhos DXF reais, com tempo de corte medido) e devolve a previsão de cada um em `modelos[]`, para comparação lado a lado:
   - **Regressão Linear Simples**: só o perímetro como feature.
   - **Regressão Linear Múltipla**: parâmetros de corte (one-hot nas categóricas) + perímetro + número de furos.
   - **Regressão Polinomial Múltipla (grau 2)**: as mesmas features, com quadrados e interações nas colunas numéricas.

### Treinando os modelos (benchmark)

```bash
cd backend
.venv/bin/pip install -r requirements.txt
.venv/bin/python train_model.py
```

O script lê `files/dataset.xlsx`, extrai o número de furos de cada desenho em `files/drawings-dxf/` (via `dxf_analyzer.py`), treina os três modelos sobre `Tempo Real Minutos` com o mesmo split treino/teste (80/20), imprime uma tabela de benchmark (MAE, RMSE, R², tempo de treino) comparando com a fórmula fixa atual, e salva cada modelo em `backend/model/<id>.joblib` e as métricas em `backend/model/benchmark.json` (não versionados — precisam ser gerados localmente). Sem os modelos, `/api/estimativa/ml` responde `503`.

---

## 📓 Análise e modelagem: qual arquivo usar

| Arquivo | O que é | Papel |
| --- | --- | --- |
| `main.ipynb` | Notebook completo: limpeza, split, EDA inteira (missing, outliers, correlações, leakage, drift), os 4 modelos, gráficos de correlação e de erro | **Fonte principal** |
| `ml.py` | Script do pipeline sem a EDA: limpeza, split, os 4 modelos (uma função de treino por modelo), validação cruzada, teste e 4 gráficos de erro em `figuras/` | Rodar tudo de uma vez e ver o consolidado |

O `ml.py` foi escrito a partir do `main.ipynb` e **não é sincronizado automaticamente**: se o notebook mudar, o script precisa ser atualizado.

### Pipeline (segue as Aulas 3 e 6 do Dr. Rodrigo Ramos Silva)

1. **Coleta e limpeza mínima:** duplicatas exatas, tipos e unidades, valores impossíveis → `NaN`; sem imputar nem remover outliers.
2. **Split por desenho** (`Plano Desenho`): 80% treino e 20% teste, sem repetir desenho entre os dois. O teste só é aberto no final.
3. **EDA somente no treino:** distribuições, valores faltando, outliers, correlações, leakage e drift.
4. **Modelagem:** validação cruzada por desenho (5 folds) no treino e teste aberto uma única vez.

### Modelos do benchmark

| Modelo | Variáveis |
| --- | --- |
| Fórmula fixa (referência) | `perímetro ÷ velocidade`, sem treino |
| Regressão linear simples | `tempo_teorico_min` |
| Regressão linear múltipla | 9 numéricas padronizadas + Material e Gás (one-hot) |
| Regressão polinomial múltipla (grau 2) | as mesmas, com quadrados e interações |

Principais resultados (erro médio absoluto, em minutos): a fórmula fixa erra **0,81** na validação cruzada (0,77 no teste) e os modelos treinados **~0,17** (0,166 no teste), uma redução de cerca de 79%. Os três modelos treinados ficam praticamente iguais entre si; o ganho vem do tempo teórico calibrado. O erro que sobra está nas peças pequenas.

> Nota: o notebook e o `ml.py` usam só os parâmetros de corte e o perímetro. O back-end (`train_model.py` e `/api/estimativa/ml`) ainda inclui o **número de furos** como feature.

```bash
backend/.venv/bin/python ml.py              # salva os gráficos em figuras/
backend/.venv/bin/python ml.py --mostrar    # também abre as janelas dos gráficos
```

Os gráficos usam `matplotlib` (instale no `.venv`: `uv pip install --python backend/.venv/bin/python matplotlib`).

---

## 📁 Estrutura do projeto

```
main.ipynb                         # análise completa: limpeza, split, EDA e modelos (fonte principal)
ml.py                              # script do pipeline e do benchmark (sem EDA)
figuras/                           # gráficos de correlação e de erro gerados pelo notebook e pelo ml.py
Nesting_Time_Estimator.pptx        # apresentação do trabalho
documentacao-aula/                 # material do professor (Aulas 3 e 6 e guias)
files/                             # dataset.xlsx, tabela de parâmetros, desenhos DXF e relatórios de perímetro

backend/
├── main.py                        # API FastAPI (rotas /api/parametros, /api/dxf/analisar, /api/estimativa, /api/estimativa/ml)
├── dxf_analyzer.py                # leitura do .dxf com ezdxf (perímetro, furos, layers, peças)
├── train_model.py                 # treina e compara os modelos de regressão (benchmark)
├── model/                         # modelos treinados + benchmark.json (gerados localmente, não versionados)
└── requirements.txt

frontend/
├── src/
│   ├── api.js                     # chamadas fetch para o back-end
│   ├── data/
│   │   └── parametros_corte.json  # popula os dropdowns (aba "Corte_Laser_Parametros" do .xlsx, 406 linhas)
│   ├── components/
│   │   ├── ParametrosSelector.jsx # dropdowns em cascata
│   │   ├── DxfUpload.jsx          # drag & drop do .dxf
│   │   └── ResultadoEstimativa.jsx# exibição do tempo total estimado
│   ├── App.jsx                    # componente raiz, guarda o estado global
│   ├── App.css                    # estilos dos componentes
│   ├── index.css                  # reset + variáveis de cor
│   └── main.jsx                   # ponto de entrada do React
└── vite.config.js
```

---

## ▶️ Como rodar

**Back-end**

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn main:app --reload --port 8000
```

**Front-end**

```bash
cd frontend
npm install
npm run dev
```

O front assume o back-end em `http://localhost:8000` (configurável via `VITE_API_URL`).

---

## 🛠️ Stack

- [React 18](https://react.dev/) + [Vite 5](https://vite.dev/) — front-end
- CSS puro (sem framework)
- [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) — back-end
- [ezdxf](https://ezdxf.readthedocs.io/) — leitura e processamento dos arquivos `.dxf`
- [scikit-learn](https://scikit-learn.org/) — regressão linear simples, múltipla e polinomial para estimativa de tempo de corte
- [matplotlib](https://matplotlib.org/) + [SciPy](https://scipy.org/) — gráficos e testes estatísticos (EDA) em `main.ipynb` e `ml.py`
- [pandas](https://pandas.pydata.org/) + [openpyxl](https://openpyxl.readthedocs.io/) — leitura de `files/dataset.xlsx` para treino

---
