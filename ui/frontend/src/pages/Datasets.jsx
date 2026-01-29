import { useState, useRef } from 'react'
import { useApi, apiGet, apiDelete } from '../hooks/useApi'

function formatBytes(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

export default function Datasets() {
  const { data: datasets, loading, refetch } = useApi('/datasets')
  const [uploading, setUploading] = useState(false)
  const [newDatasetName, setNewDatasetName] = useState('')
  const [selectedDataset, setSelectedDataset] = useState(null)
  const [datasetFiles, setDatasetFiles] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef(null)

  const uploadFiles = async (files, datasetName) => {
    if (!datasetName) {
      alert('Please enter a dataset name')
      return
    }
    setUploading(true)
    try {
      const formData = new FormData()
      for (const file of files) {
        formData.append('files', file)
      }
      const res = await fetch(`/api/datasets/${datasetName}/upload`, {
        method: 'POST',
        body: formData
      })
      if (!res.ok) throw new Error('Upload failed')
      refetch()
      setNewDatasetName('')
    } catch (e) {
      alert(`Upload failed: ${e.message}`)
    }
    setUploading(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const files = Array.from(e.dataTransfer.files).filter(f =>
      f.type.startsWith('image/')
    )
    if (files.length > 0) {
      uploadFiles(files, newDatasetName || 'new-dataset')
    }
  }

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files)
    if (files.length > 0) {
      uploadFiles(files, newDatasetName || 'new-dataset')
    }
  }

  const viewDataset = async (name) => {
    setSelectedDataset(name)
    const data = await apiGet(`/datasets/${name}`)
    setDatasetFiles(data.files)
  }

  const deleteDataset = async (name) => {
    if (!confirm(`Delete dataset "${name}" and all its files?`)) return
    await apiDelete(`/datasets/${name}`)
    refetch()
  }

  const deleteFile = async (datasetName, filename) => {
    await apiDelete(`/datasets/${datasetName}/files/${filename}`)
    viewDataset(datasetName)
    refetch()
  }

  if (loading) return <div className="flex justify-center p-8"><div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full"></div></div>

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Datasets</h1>

      <div className="bg-gray-800 p-6 rounded mb-8">
        <div className="flex gap-4 mb-4">
          <input
            type="text"
            placeholder="Dataset name"
            value={newDatasetName}
            onChange={(e) => setNewDatasetName(e.target.value)}
            className="bg-gray-700 px-3 py-2 rounded flex-1"
          />
        </div>
        <div
          className={`p-8 rounded border-2 border-dashed text-center cursor-pointer transition-colors ${
            dragOver ? 'border-blue-500 bg-blue-500/10' : 'border-gray-600 hover:border-gray-500'
          }`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="image/*"
            className="hidden"
            onChange={handleFileSelect}
          />
          {uploading ? (
            <p>Uploading...</p>
          ) : (
            <>
              <p className="text-lg mb-2">Drop images here or click to upload</p>
              <p className="text-sm text-gray-400">Supports JPG, PNG, WebP</p>
            </>
          )}
        </div>
      </div>

      <h2 className="text-xl font-semibold mb-4">Your Datasets ({datasets?.length || 0})</h2>
      {datasets?.length === 0 ? (
        <div className="bg-gray-800 p-8 rounded text-center text-gray-400">
          <p>No datasets yet</p>
          <p className="text-sm mt-2">Upload some images above to create your first dataset</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {datasets?.map(ds => (
            <div key={ds.name} className="bg-gray-800 p-4 rounded">
              <div className="flex justify-between items-center">
                <div>
                  <p className="font-medium">{ds.name}</p>
                  <p className="text-sm text-gray-400">
                    {ds.file_count} images • {formatBytes(ds.total_size)}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => viewDataset(ds.name)}
                    className="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded text-sm"
                  >
                    View
                  </button>
                  <button
                    onClick={() => deleteDataset(ds.name)}
                    className="bg-red-600 hover:bg-red-700 px-3 py-1 rounded text-sm"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedDataset && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setSelectedDataset(null)}>
          <div className="bg-gray-800 p-6 rounded-lg max-w-2xl w-full mx-4 max-h-[80vh] overflow-auto" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold mb-4">{selectedDataset}</h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {datasetFiles?.map(file => (
                <div key={file.name} className="bg-gray-900 rounded overflow-hidden group relative">
                  <div className="aspect-square bg-gray-700 flex items-center justify-center text-gray-500 text-xs">
                    {file.name}
                  </div>
                  <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <button
                      onClick={() => deleteFile(selectedDataset, file.name)}
                      className="bg-red-600 px-2 py-1 rounded text-xs"
                    >
                      Delete
                    </button>
                  </div>
                  <p className="p-2 text-xs truncate">{formatBytes(file.size)}</p>
                </div>
              ))}
            </div>
            <button onClick={() => setSelectedDataset(null)} className="mt-4 w-full bg-gray-700 hover:bg-gray-600 py-2 rounded">Close</button>
          </div>
        </div>
      )}
    </div>
  )
}
