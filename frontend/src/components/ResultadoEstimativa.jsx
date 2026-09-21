export default function ResultadoEstimativa({ resultado, carregando }) {
  if (carregando) {
    return (
      <div className="card card--muted">
        <h2>3. Estimativa</h2>
        <p className="text-dim">Calculando...</p>
      </div>
    )
  }

  if (!resultado) {
    return (
      <div className="card card--muted">
        <h2>3. Estimativa</h2>
        <p className="text-dim">Selecione material, espessura, potência, gás e envie um DXF para calcular.</p>
      </div>
    )
  }

  const { tempoTotalFormatado } = resultado

  return (
    <div className="card">
      <h2>3. Estimativa</h2>

      <div>
        <div className="result-label">Tempo total</div>
        <div className="result-value result-value--accent">{tempoTotalFormatado}</div>
      </div>
    </div>
  )
}
