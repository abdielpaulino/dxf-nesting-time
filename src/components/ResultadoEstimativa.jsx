const TEMPO_PERFURACAO_S = 1.5

export default function ResultadoEstimativa({ parametro, geometria }) {
  if (!parametro) {
    return (
      <div className="card card--muted">
        <h2>3. Estimativa</h2>
        <p className="text-dim">Selecione material, espessura, potência e gás para calcular.</p>
      </div>
    )
  }

  const { comprimentoMm, numFuros, quantidade } = geometria
  const velocidadeMmMin = parametro.velocidade_corte_m_min * 1000

  const tempoCorteMin = velocidadeMmMin > 0 ? comprimentoMm / velocidadeMmMin : 0
  const tempoPerfuracaoMin = (numFuros * TEMPO_PERFURACAO_S) / 60
  const tempoTotalMin = (tempoCorteMin + tempoPerfuracaoMin) * quantidade

  function formatarMin(min) {
    const totalSeg = Math.round(min * 60)
    const m = Math.floor(totalSeg / 60)
    const s = totalSeg % 60
    return `${m}min ${s.toString().padStart(2, '0')}s`
  }

  return (
    <div className="card">
      <h2>3. Estimativa</h2>

      <div>
        <div className="result-label">Tempo total</div>
        <div className="result-value result-value--accent">{formatarMin(tempoTotalMin)}</div>
      </div>

      <table className="params-table">
        <tbody>
          <tr>
            <td>Velocidade de corte</td>
            <td>{parametro.velocidade_corte_m_min} m/min</td>
          </tr>
          <tr>
            <td>Pressão do gás</td>
            <td>{parametro.pressao_gas_bar} bar</td>
          </tr>
          <tr>
            <td>Posição do foco</td>
            <td>{parametro.posicao_foco_mm} mm</td>
          </tr>
          <tr>
            <td>Bocal</td>
            <td>
              {parametro.tipo_bocal} · Ø{parametro.diametro_bocal_mm} mm · distância {parametro.distancia_bocal_mm} mm
            </td>
          </tr>
          <tr>
            <td>Largura do kerf</td>
            <td>{parametro.largura_kerf_mm} mm</td>
          </tr>
          <tr>
            <td>Acabamento esperado</td>
            <td>{parametro.tipo_acabamento}</td>
          </tr>
        </tbody>
      </table>
    </div>
  )
}
