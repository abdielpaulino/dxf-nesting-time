import { useMemo, useState } from 'react'
import dados from './data/parametros_corte.json'
import ParametrosSelector from './components/ParametrosSelector.jsx'
import DxfUpload from './components/DxfUpload.jsx'
import ResultadoEstimativa from './components/ResultadoEstimativa.jsx'
import './App.css'

export default function App() {
  const [selecao, setSelecao] = useState({
    material: '',
    espessuraDisplay: '',
    potencia: '',
    gas: '',
  })

  const [geometria, setGeometria] = useState({
    comprimentoMm: 0,
    numFuros: 0,
    quantidade: 1,
  })

  function handleDxfSelecionado(file) {
    setGeometria({ comprimentoMm: 1200, numFuros: 4, quantidade: 1 })
  }

  const parametro = useMemo(() => {
    const { material, espessuraDisplay, potencia, gas } = selecao
    if (!material || !espessuraDisplay || !potencia || !gas) return null
    return (
      dados.find(
        (d) =>
          d.material === material &&
          d.espessura_display === espessuraDisplay &&
          d.potencia_w === potencia &&
          d.gas_auxiliar === gas
      ) || null
    )
  }, [selecao])

  return (
    <div className="app">
      <header className="app-header">
        <h1>Estimador de Tempo de Corte a Laser</h1>
      </header>

      <main className="app-main">
        <ParametrosSelector dados={dados} selecao={selecao} setSelecao={setSelecao} />
        <DxfUpload onFileSelected={handleDxfSelecionado} />
        <ResultadoEstimativa parametro={parametro} geometria={geometria} />
      </main>
    </div>
  )
}
