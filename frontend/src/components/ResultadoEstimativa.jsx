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

  return (
    <div className="card">
      <h2>3. Estimativa</h2>

      <div className="grid-4">
        <div>
          <div className="result-label">Fórmula atual</div>
          <div className="result-value">{resultado.tempoTotalFormatado}</div>
        </div>

        {carregandoMl && <div className="result-value text-dim">Calculando...</div>}

        {!carregandoMl && !resultadoMl && <p className="text-dim">{erroMl || 'Modelos de IA indisponíveis.'}</p>}

        {!carregandoMl &&
          resultadoMl?.modelos.map((modelo) => {
            const diffMin = modelo.tempoTotalMin - resultado.tempoTotalMin
            return (
              <div key={modelo.id}>
                <div className="result-label">{modelo.nome}</div>
                <div className="result-value result-value--accent">{modelo.tempoTotalFormatado}</div>
                <p className="hint">
                  vs. fórmula: {diffMin >= 0 ? '+' : ''}
                  {diffMin.toFixed(2)} min
                </p>
              </div>
            )
          })}
      </div>
    </div>
  )
}
