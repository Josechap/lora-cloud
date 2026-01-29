import { useState } from 'react'
import { useApi, apiPost, apiDelete, apiGet } from '../hooks/useApi'

const GPU_PRESETS = [
  { name: 'RTX 4090', maxPrice: 0.6, minRam: 24 },
  { name: 'RTX 3090', maxPrice: 0.4, minRam: 24 },
  { name: 'A100', maxPrice: 1.5, minRam: 40 },
]

const STATUS_COLORS = {
  running: 'bg-green-500',
  loading: 'bg-yellow-500',
  exited: 'bg-red-500',
}

export default function Dashboard() {
  const { data: instances, loading, refetch } = useApi('/instances', { pollInterval: 10000 })
  const [launching, setLaunching] = useState(false)
  const [selectedGpu, setSelectedGpu] = useState(GPU_PRESETS[0])
  const [sshInfo, setSshInfo] = useState(null)

  const launchInstance = async (image, name) => {
    const confirmed = confirm(
      `Launch ${name} instance?\n\n` +
      `GPU: ${selectedGpu.name}\n` +
      `Max price: $${selectedGpu.maxPrice}/hr\n` +
      `Disk: 50GB\n\n` +
      `You will be charged for as long as it runs.`
    )
    if (!confirmed) return

    setLaunching(true)
    try {
      await apiPost('/instances/launch', {
        gpu_type: selectedGpu.name,
        image,
        max_price: selectedGpu.maxPrice,
        disk_gb: 50
      })
      refetch()
    } catch (e) {
      alert(`Failed to launch: ${e.message}`)
    }
    setLaunching(false)
  }

  const stopInstance = async (id) => {
    if (!confirm('Stop this instance?')) return
    await apiDelete(`/instances/${id}`)
    refetch()
  }

  const showSshInfo = async (id) => {
    const info = await apiGet(`/instances/${id}/ssh`)
    setSshInfo(info)
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
  }

  if (loading) return <div className="flex justify-center p-8"><div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full"></div></div>

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

      <div className="bg-gray-800 p-4 rounded mb-8">
        <h2 className="text-lg font-semibold mb-4">Launch New Instance</h2>
        <div className="flex flex-wrap gap-4 items-end">
          <div>
            <label className="block text-sm text-gray-400 mb-1">GPU Type</label>
            <select
              value={selectedGpu.name}
              onChange={(e) => setSelectedGpu(GPU_PRESETS.find(g => g.name === e.target.value))}
              className="bg-gray-700 px-3 py-2 rounded"
            >
              {GPU_PRESETS.map(gpu => (
                <option key={gpu.name} value={gpu.name}>
                  {gpu.name} (≤${gpu.maxPrice}/hr)
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={() => launchInstance('pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime', 'trainer')}
            disabled={launching}
            className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 px-4 py-2 rounded"
          >
            {launching ? 'Launching...' : 'Launch Training Instance'}
          </button>
          <button
            onClick={() => launchInstance('pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime', 'comfyui')}
            disabled={launching}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 px-4 py-2 rounded"
          >
            {launching ? 'Launching...' : 'Launch ComfyUI'}
          </button>
        </div>
      </div>

      {instances?.length > 0 && (
        <div className="bg-yellow-900/30 border border-yellow-600 p-4 rounded mb-4">
          <p className="text-yellow-300">
            💰 Estimated running cost: <strong>${instances.reduce((sum, i) => sum + (i.dph_total || 0), 0).toFixed(2)}/hr</strong>
            {' '}(${(instances.reduce((sum, i) => sum + (i.dph_total || 0), 0) * 24).toFixed(2)}/day)
          </p>
        </div>
      )}

      <h2 className="text-xl font-semibold mb-4">Active Instances ({instances?.length || 0})</h2>
      {instances?.length === 0 ? (
        <div className="bg-gray-800 p-8 rounded text-center text-gray-400">
          <p>No running instances</p>
          <p className="text-sm mt-2">Launch an instance above to get started</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {instances?.map(inst => (
            <div key={inst.id} className="bg-gray-800 p-4 rounded">
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${STATUS_COLORS[inst.cur_state] || 'bg-gray-500'}`}></span>
                    <p className="font-medium">{inst.gpu_name}</p>
                  </div>
                  <p className="text-sm text-gray-400 mt-1">
                    ${inst.dph_total?.toFixed(3)}/hr • {inst.cur_state} • {inst.geolocation}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    ID: {inst.id} • {inst.num_gpus} GPU • {inst.gpu_ram}GB VRAM • {inst.disk_space}GB disk
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => showSshInfo(inst.id)}
                    className="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded text-sm"
                  >
                    SSH Info
                  </button>
                  <button
                    onClick={() => stopInstance(inst.id)}
                    className="bg-red-600 hover:bg-red-700 px-3 py-1 rounded text-sm"
                  >
                    Stop
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {sshInfo && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setSshInfo(null)}>
          <div className="bg-gray-800 p-6 rounded-lg max-w-lg w-full mx-4" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold mb-4">SSH Connection</h3>
            <div className="space-y-3">
              <div>
                <label className="text-sm text-gray-400">Command</label>
                <div className="flex gap-2">
                  <code className="bg-gray-900 px-3 py-2 rounded flex-1 text-sm">{sshInfo.command}</code>
                  <button onClick={() => copyToClipboard(sshInfo.command)} className="bg-blue-600 px-3 rounded">Copy</button>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-gray-400">Host</label>
                  <p className="bg-gray-900 px-3 py-2 rounded">{sshInfo.host}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-400">Port</label>
                  <p className="bg-gray-900 px-3 py-2 rounded">{sshInfo.port}</p>
                </div>
              </div>
              {sshInfo.jupyter_token && (
                <div>
                  <label className="text-sm text-gray-400">Jupyter Token</label>
                  <code className="bg-gray-900 px-3 py-2 rounded block text-xs break-all">{sshInfo.jupyter_token}</code>
                </div>
              )}
            </div>
            <button onClick={() => setSshInfo(null)} className="mt-4 w-full bg-gray-700 hover:bg-gray-600 py-2 rounded">Close</button>
          </div>
        </div>
      )}
    </div>
  )
}
