# ✂️ Estimador de Tempo de Corte a Laser

App **React + Vite (front-end)** com **FastAPI (back-end)** para estimar o tempo de corte a laser com base em parâmetros de máquina (material, espessura, potência, gás) e em um desenho técnico **DXF**.

> Estágio atual: front-end e back-end integrados. O back-end lê o `.dxf` de verdade (via `ezdxf`) e calcula o tempo com uma fórmula a partir do perímetro e do número de furos. A troca dessa fórmula por um **modelo de Machine Learning** treinado com dados reais de corte é o próximo passo.

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
3. Existe também `POST /api/estimativa/ml`, com o mesmo payload de entrada, que usa um modelo **Random Forest** treinado em `files/dataset.xlsx` (176 mil linhas: 406 combinações de parâmetros × 435 desenhos DXF reais, com tempo de corte medido) para prever o tempo total diretamente a partir dos parâmetros de corte + perímetro + número de furos.

### Treinando o modelo de Random Forest

```bash
cd backend
.venv/bin/pip install -r requirements.txt
.venv/bin/python train_model.py
```

O script lê `files/dataset.xlsx`, extrai o número de furos de cada desenho em `files/drawings-dxf/` (via `dxf_analyzer.py`), treina um `RandomForestRegressor` sobre `Tempo Real Minutos`, imprime as métricas (MAE, RMSE, R²) comparando com a fórmula fixa atual, e salva o modelo em `backend/model/random_forest_tempo.joblib` (não versionado — precisa ser gerado localmente). Sem esse arquivo, `/api/estimativa/ml` responde `503`.

---

## 📁 Estrutura do projeto

```
backend/
├── main.py                        # API FastAPI (rotas /api/parametros, /api/dxf/analisar, /api/estimativa, /api/estimativa/ml)
├── dxf_analyzer.py                # leitura do .dxf com ezdxf (perímetro, furos, layers, peças)
├── train_model.py                 # treina o Random Forest a partir de files/dataset.xlsx
├── model/                         # modelo treinado (gerado localmente, não versionado)
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
- [scikit-learn](https://scikit-learn.org/) — Random Forest para estimativa de tempo de corte
- [pandas](https://pandas.pydata.org/) + [openpyxl](https://openpyxl.readthedocs.io/) — leitura de `files/dataset.xlsx` para treino

---
