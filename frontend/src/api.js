const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function tratarResposta(resp) {
  if (!resp.ok) {
    const corpo = await resp.json().catch(() => null)
    throw new Error(corpo?.detail || `Erro na requisição (${resp.status})`)
  }
  return resp.json()
}

export async function analisarDxf(arquivo) {
  const formData = new FormData()
  formData.append('arquivo', arquivo)

  const resp = await fetch(`${API_URL}/api/dxf/analisar`, {
    method: 'POST',
    body: formData,
  })
  return tratarResposta(resp)
}

export async function calcularEstimativa({ material, espessuraDisplay, potencia, gas, geometria }) {
  const resp = await fetch(`${API_URL}/api/estimativa`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ material, espessuraDisplay, potencia, gas, geometria }),
  })
  return tratarResposta(resp)
}

export async function calcularEstimativaMl({ material, espessuraDisplay, potencia, gas, geometria }) {
  const resp = await fetch(`${API_URL}/api/estimativa/ml`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ material, espessuraDisplay, potencia, gas, geometria }),
  })
  return tratarResposta(resp)
}
