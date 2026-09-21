import { useRef, useState } from 'react'

export default function DxfUpload({ onFileSelected }) {
  const inputRef = useRef(null)
  const [arquivo, setArquivo] = useState(null)
  const [arrastando, setArrastando] = useState(false)

  function handleFile(file) {
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.dxf')) {
      alert('Envie um arquivo .dxf')
      return
    }
    setArquivo(file)
    onFileSelected?.(file)
  }

  function onDrop(e) {
    e.preventDefault()
    setArrastando(false)
    handleFile(e.dataTransfer.files?.[0])
  }

  return (
    <div className="card">
      <h2>2. Desenho (DXF)</h2>

      <div
        className={`dropzone ${arrastando ? 'dropzone--active' : ''}`}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault()
          setArrastando(true)
        }}
        onDragLeave={() => setArrastando(false)}
        onDrop={onDrop}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".dxf"
          hidden
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
        {arquivo ? (
          <div>
            <strong>{arquivo.name}</strong>
            <div className="text-dim">{(arquivo.size / 1024).toFixed(1)} KB</div>
          </div>
        ) : (
          <div>
            <div>Arraste o arquivo .dxf aqui ou clique para selecionar</div>
          </div>
        )}
      </div>
    </div>
  )
}
