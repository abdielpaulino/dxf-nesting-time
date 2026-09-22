export default function ResultadoEstimativa({ resultado, resultadoMl, erroMl, carregando, carregandoMl }) {
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

  const diffMin = resultadoMl ? resultadoMl.tempoTotalMin - resultado.tempoTotalMin : null

  return (
    <div className="card">
      <h2>3. Estimativa</h2>

      <div className="grid-2">
        <div>
          <div className="result-label">Fórmula atual</div>
          <div className="result-value">{resultado.tempoTotalFormatado}</div>
        </div>

        <div>
          <div className="result-label">Random Forest (IA)</div>
          {carregandoMl && <div className="result-value text-dim">Calculando...</div>}
          {!carregandoMl && resultadoMl && (
            <div className="result-value result-value--accent">{resultadoMl.tempoTotalFormatado}</div>
          )}
          {!carregandoMl && !resultadoMl && (
            <p className="text-dim">
              {erroMl || 'Indisponível.'}
            </p>
          )}
        </div>
      </div>

      {resultadoMl && (
        <p className="hint">
          Diferença IA − fórmula: {diffMin >= 0 ? '+' : ''}
          {diffMin.toFixed(2)} min
        </p>
      )}
    </div>
  )
}
