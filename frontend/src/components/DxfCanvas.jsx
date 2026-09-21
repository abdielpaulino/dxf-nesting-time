import { useEffect, useMemo, useRef, useState } from 'react'

function distanciaPontoSegmento(px, py, x1, y1, x2, y2) {
  const dx = x2 - x1
  const dy = y2 - y1
  const lenSq = dx * dx + dy * dy
  let t = lenSq === 0 ? 0 : ((px - x1) * dx + (py - y1) * dy) / lenSq
  t = Math.max(0, Math.min(1, t))
  const cx = x1 + t * dx
  const cy = y1 + t * dy
  return Math.hypot(px - cx, py - cy)
}

const LIMIAR_HOVER_PX = 8

export default function DxfCanvas({ desenho, altura = 280 }) {
  const canvasRef = useRef(null)
  const containerRef = useRef(null)
  const transformRef = useRef(null)
  const [hover, setHover] = useState(null)

  const comprimentos = useMemo(() => {
    const segmentos = desenho?.segmentos || []
    return segmentos.map((seg) => {
      let total = 0
      for (let i = 1; i < seg.length; i++) {
        total += Math.hypot(seg[i][0] - seg[i - 1][0], seg[i][1] - seg[i - 1][1])
      }
      return total
    })
  }, [desenho])

  function desenhar(hoverIndex) {
    const canvas = canvasRef.current
    const transform = transformRef.current
    if (!canvas || !transform) return
    const { largura, altura: alturaCanvas, bbox, escala, offsetX, offsetY } = transform
    const ctx = canvas.getContext('2d')
    ctx.clearRect(0, 0, largura, alturaCanvas)

    const segmentos = desenho?.segmentos || []
    const estilo = getComputedStyle(document.documentElement)
    const corBase = estilo.getPropertyValue('--accent').trim() || '#ff5a1f'
    const corDestaque = estilo.getPropertyValue('--ok').trim() || '#35d488'

    function projetar([x, y]) {
      const px = offsetX + (x - bbox.minX) * escala
      const py = alturaCanvas - (offsetY + (y - bbox.minY) * escala)
      return [px, py]
    }

    ctx.lineJoin = 'round'
    segmentos.forEach((seg, i) => {
      if (seg.length < 2) return
      const destacado = i === hoverIndex
      ctx.strokeStyle = destacado ? corDestaque : corBase
      ctx.lineWidth = destacado ? 2.4 : 1.2
      ctx.beginPath()
      const [x0, y0] = projetar(seg[0])
      ctx.moveTo(x0, y0)
      for (let j = 1; j < seg.length; j++) {
        const [x, y] = projetar(seg[j])
        ctx.lineTo(x, y)
      }
      ctx.stroke()
    })
  }

  useEffect(() => {
    const canvas = canvasRef.current
    const container = containerRef.current
    if (!canvas || !container) return

    const largura = container.clientWidth
    const dpr = window.devicePixelRatio || 1
    canvas.width = largura * dpr
    canvas.height = altura * dpr
    canvas.style.width = `${largura}px`
    canvas.style.height = `${altura}px`

    const ctx = canvas.getContext('2d')
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    ctx.clearRect(0, 0, largura, altura)

    const segmentos = desenho?.segmentos
    const bbox = desenho?.bbox
    setHover(null)

    if (!segmentos?.length || !bbox) {
      transformRef.current = null
      return
    }

    const padding = 20
    const larguraDesenho = bbox.maxX - bbox.minX || 1
    const alturaDesenho = bbox.maxY - bbox.minY || 1
    const escala = Math.min(
      (largura - padding * 2) / larguraDesenho,
      (altura - padding * 2) / alturaDesenho
    )

    const offsetX = padding + (largura - padding * 2 - larguraDesenho * escala) / 2
    const offsetY = padding + (altura - padding * 2 - alturaDesenho * escala) / 2

    transformRef.current = { largura, altura, bbox, escala, offsetX, offsetY }
    desenhar(null)
  }, [desenho, altura])

  function aoMoverMouse(e) {
    const transform = transformRef.current
    if (!transform) return
    const rect = canvasRef.current.getBoundingClientRect()
    const mx = e.clientX - rect.left
    const my = e.clientY - rect.top

    const { bbox, escala, offsetX, offsetY, altura: alturaCanvas } = transform
    function projetar([x, y]) {
      const px = offsetX + (x - bbox.minX) * escala
      const py = alturaCanvas - (offsetY + (y - bbox.minY) * escala)
      return [px, py]
    }

    const segmentos = desenho?.segmentos || []
    let melhorIdx = -1
    let melhorDist = LIMIAR_HOVER_PX
    for (let i = 0; i < segmentos.length; i++) {
      const seg = segmentos[i]
      for (let j = 1; j < seg.length; j++) {
        const [x1, y1] = projetar(seg[j - 1])
        const [x2, y2] = projetar(seg[j])
        const d = distanciaPontoSegmento(mx, my, x1, y1, x2, y2)
        if (d < melhorDist) {
          melhorDist = d
          melhorIdx = i
        }
      }
    }

    if (melhorIdx >= 0) {
      setHover({ index: melhorIdx, x: mx, y: my, comprimentoMm: comprimentos[melhorIdx] })
      desenhar(melhorIdx)
    } else if (hover) {
      setHover(null)
      desenhar(null)
    }
  }

  function aoSairMouse() {
    setHover(null)
    desenhar(null)
  }

  return (
    <div ref={containerRef} className="dxf-canvas-wrap">
      <canvas
        ref={canvasRef}
        className="dxf-canvas"
        onMouseMove={aoMoverMouse}
        onMouseLeave={aoSairMouse}
      />
      {hover && (
        <div className="dxf-tooltip" style={{ left: hover.x + 14, top: hover.y + 14 }}>
          {hover.comprimentoMm.toFixed(2)} mm
        </div>
      )}
    </div>
  )
}
