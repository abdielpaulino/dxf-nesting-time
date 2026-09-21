# ✂️ Estimador de Tempo de Corte a Laser

Front-end em **React + Vite** para estimar o tempo de corte a laser com base em parâmetros de máquina (material, espessura, potência, gás) e em um desenho técnico **DXF**.

> Estágio atual: **front-end funcional com dados de exemplo**. A estimativa de tempo será feita por um **modelo de Machine Learning** (ainda em desenvolvimento).

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

A tabela de parâmetros (`src/data/parametros_corte.json`) **não é a fonte do tempo estimado** — ela serve apenas para popular os dropdowns da etapa 1 (quais materiais, espessuras, potências e gases existem).

O tempo em si será calculado por um **modelo de Machine Learning**, treinado a partir de dados reais de corte (parâmetros de máquina + geometria das peças), e não por uma fórmula fixa ou por busca direta na tabela. Isso significa que:

- O modelo roda no back-end (Python), não no navegador.
- O front envia os parâmetros selecionados + a geometria extraída do DXF, e recebe de volta o tempo estimado pela predição do modelo.

---

## 📁 Estrutura do projeto

```
src/
├── data/
│   └── parametros_corte.json      # popula os dropdowns (aba "Corte_Laser_Parametros" do .xlsx, 406 linhas)
├── components/
│   ├── ParametrosSelector.jsx     # dropdowns em cascata
│   ├── DxfUpload.jsx              # drag & drop do .dxf
│   └── ResultadoEstimativa.jsx    # exibição do tempo total estimado
├── App.jsx                        # componente raiz, guarda o estado global
├── App.css                        # estilos dos componentes
├── index.css                      # reset + variáveis de cor
└── main.jsx                       # ponto de entrada do React
```

---

## 🛠️ Stack

- [React 18](https://react.dev/)
- [Vite 5](https://vite.dev/) — dev server e build
- CSS puro (sem framework)

---
