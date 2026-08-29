import { useMemo } from 'react'

function unique(arr) {
  return [...new Set(arr)]
}

export default function ParametrosSelector({ dados, selecao, setSelecao }) {
  const { material, espessuraDisplay, potencia, gas } = selecao

  const materiais = useMemo(() => unique(dados.map((d) => d.material)).sort(), [dados])

  const espessuras = useMemo(() => {
    if (!material) return []
    const filtradas = dados.filter((d) => d.material === material)
    const vistos = new Map()
    filtradas.forEach((d) => {
      if (!vistos.has(d.espessura_display)) vistos.set(d.espessura_display, d.espessura_mm)
    })
    return [...vistos.entries()].sort((a, b) => a[1] - b[1])
  }, [dados, material])

  const potencias = useMemo(() => {
    if (!material || !espessuraDisplay) return []
    return unique(
      dados
        .filter((d) => d.material === material && d.espessura_display === espessuraDisplay)
        .map((d) => d.potencia_w)
    ).sort((a, b) => a - b)
  }, [dados, material, espessuraDisplay])

  const gases = useMemo(() => {
    if (!material || !espessuraDisplay || !potencia) return []
    return unique(
      dados
        .filter(
          (d) =>
            d.material === material &&
            d.espessura_display === espessuraDisplay &&
            d.potencia_w === potencia
        )
        .map((d) => d.gas_auxiliar)
    )
  }, [dados, material, espessuraDisplay, potencia])

  function onMaterial(e) {
    setSelecao({ material: e.target.value, espessuraDisplay: '', potencia: '', gas: '' })
  }
  function onEspessura(e) {
    setSelecao({ ...selecao, espessuraDisplay: e.target.value, potencia: '', gas: '' })
  }
  function onPotencia(e) {
    setSelecao({ ...selecao, potencia: Number(e.target.value), gas: '' })
  }
  function onGas(e) {
    setSelecao({ ...selecao, gas: e.target.value })
  }

  return (
    <div className="card">
      <h2>1. Parâmetros de corte</h2>
      <div className="grid-4">
        <div className="field">
          <label>Material</label>
          <select value={material} onChange={onMaterial}>
            <option value="">Selecione...</option>
            {materiais.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label>Espessura</label>
          <select value={espessuraDisplay} onChange={onEspessura} disabled={!material}>
            <option value="">Selecione...</option>
            {espessuras.map(([display, mm]) => (
              <option key={display} value={display}>
                {display}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label>Potência do laser</label>
          <select value={potencia} onChange={onPotencia} disabled={!espessuraDisplay}>
            <option value="">Selecione...</option>
            {potencias.map((p) => (
              <option key={p} value={p}>
                {(p / 1000).toLocaleString('pt-BR')} kW
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label>Gás auxiliar</label>
          <select value={gas} onChange={onGas} disabled={!potencia}>
            <option value="">Selecione...</option>
            {gases.map((g) => (
              <option key={g} value={g}>
                {g}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  )
}
