import { useApi, apiGet, apiDelete } from '../hooks/useApi'

function formatBytes(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

function formatDate(isoString) {
  return new Date(isoString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

export default function Loras() {
  const { data: loras, loading, refetch } = useApi('/loras')

  const downloadLora = async (name) => {
    try {
      const { url } = await apiGet(`/loras/${name}/url`)
      window.open(url, '_blank')
    } catch (e) {
      alert(`Failed to get download link: ${e.message}`)
    }
  }

  const deleteLora = async (name) => {
    if (!confirm(`Delete LoRA "${name}"? This cannot be undone.`)) return
    await apiDelete(`/loras/${name}`)
    refetch()
  }

  if (loading) return <div className="flex justify-center p-8"><div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full"></div></div>

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Trained LoRAs</h1>

      {loras?.length === 0 ? (
        <div className="bg-gray-800 p-8 rounded text-center text-gray-400">
          <p>No LoRAs yet</p>
          <p className="text-sm mt-2">Train a LoRA from the Training page</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {loras?.map(lora => (
            <div key={lora.name} className="bg-gray-800 p-4 rounded">
              <div className="flex justify-between items-center">
                <div>
                  <p className="font-medium">{lora.name}</p>
                  <p className="text-sm text-gray-400">
                    {formatBytes(lora.size)} • Updated {formatDate(lora.updated)}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => downloadLora(lora.name)}
                    className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm"
                  >
                    Download
                  </button>
                  <button
                    onClick={() => deleteLora(lora.name)}
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

      <div className="mt-8 bg-gray-800 p-4 rounded">
        <h3 className="font-semibold mb-2">Using LoRAs in ComfyUI</h3>
        <p className="text-sm text-gray-400">
          Download your LoRA and place it in the <code className="bg-gray-700 px-1 rounded">models/loras/</code> folder
          of your ComfyUI installation. Then use a "Load LoRA" node in your workflow.
        </p>
      </div>
    </div>
  )
}
