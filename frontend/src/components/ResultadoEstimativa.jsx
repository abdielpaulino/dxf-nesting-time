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

  const { parametro, tempoTotalFormatado } = resultado

  return (
    <div className="card">
      <h2>3. Estimativa</h2>

      <div>
        <div className="result-label">Tempo total</div>
        <div className="result-value result-value--accent">{tempoTotalFormatado}</div>
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
