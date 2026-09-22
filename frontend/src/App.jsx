import { useEffect, useMemo, useState } from 'react'
import dados from './data/parametros_corte.json'
import ParametrosSelector from './components/ParametrosSelector.jsx'
import DxfUpload from './components/DxfUpload.jsx'
import ResultadoEstimativa from './components/ResultadoEstimativa.jsx'
import { analisarDxf, calcularEstimativa, calcularEstimativaMl } from './api.js'
import './App.css'

export default function App() {
  const [selecao, setSelecao] = useState({
    material: '',
    espessuraDisplay: '',
    potencia: '',
    gas: '',
  })

  const [geometria, setGeometria] = useState(null)
  const [resultado, setResultado] = useState(null)
  const [resultadoMl, setResultadoMl] = useState(null)
  const [erroMl, setErroMl] = useState(null)
  const [carregandoMl, setCarregandoMl] = useState(false)
  const [carregando, setCarregando] = useState(false)
  const [erro, setErro] = useState(null)

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

  async function handleDxfSelecionado(file) {
    setErro(null)
    setCarregando(true)
    try {
      const analise = await analisarDxf(file)
      setGeometria(analise)
    } catch (e) {
      setErro(e.message)
      setGeometria(null)
    } finally {
      setCarregando(false)
    }
  }

  useEffect(() => {
    const { material, espessuraDisplay, potencia, gas } = selecao
    if (!material || !espessuraDisplay || !potencia || !gas || !geometria) {
      setResultado(null)
      setResultadoMl(null)
      setErroMl(null)
      setCarregandoMl(false)
      return
    }

    let cancelado = false
    setErro(null)
    setErroMl(null)
    setCarregando(true)
    setCarregandoMl(true)

    calcularEstimativa({ ...selecao, geometria })
      .then((res) => {
        if (!cancelado) setResultado(res)
      })
      .catch((e) => {
        if (!cancelado) {
          setErro(e.message)
          setResultado(null)
        }
      })
      .finally(() => {
        if (!cancelado) setCarregando(false)
      })

    calcularEstimativaMl({ ...selecao, geometria })
      .then((res) => {
        if (!cancelado) setResultadoMl(res)
      })
      .catch((e) => {
        if (!cancelado) {
          setErroMl(e.message)
          setResultadoMl(null)
        }
      })
      .finally(() => {
        if (!cancelado) setCarregandoMl(false)
      })

    return () => {
      cancelado = true
    }
  }, [selecao, geometria])

  return (
    <div className="app">
      <header className="app-header">
        <h1>Estimador de Tempo de Corte a Laser</h1>
      </header>

      <main className="app-main">
        <ParametrosSelector dados={dados} selecao={selecao} setSelecao={setSelecao} parametro={parametro} />
        <DxfUpload onFileSelected={handleDxfSelecionado} geometria={geometria} />
        {erro && <div className="card card--erro">{erro}</div>}
        <ResultadoEstimativa
          resultado={resultado}
          resultadoMl={resultadoMl}
          erroMl={erroMl}
          carregando={carregando}
          carregandoMl={carregandoMl}
        />
      </main>
    </div>
  )
}
