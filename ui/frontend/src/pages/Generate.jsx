import { useState } from 'react'
import { useApi, apiPost, apiGet } from '../hooks/useApi'

export default function Generate() {
  const { data: instances } = useApi('/instances')
  const { data: loras } = useApi('/loras')
  const [tunnelPort, setTunnelPort] = useState(null)
  const [creating, setCreating] = useState(false)

  const runningInstances = instances?.filter(i => i.cur_state === 'running') || []

  const createTunnel = async (instanceId) => {
    setCreating(true)
    try {
      const result = await apiPost(`/instances/${instanceId}/tunnel`, {
        remote_port: 8188,
        local_port: 8188,
        ssh_key_path: '~/.ssh/id_rsa'
      })
      setTunnelPort(result.local_port)
    } catch (e) {
      alert(`Failed to create tunnel: ${e.message}`)
    }
    setCreating(false)
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Generate Images</h1>

      <div className="bg-gray-800 p-6 rounded mb-8">
        <h2 className="text-lg font-semibold mb-4">ComfyUI Connection</h2>

        {runningInstances.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-400 mb-4">No running instances</p>
            <p className="text-sm text-gray-500">Launch a ComfyUI instance from the Dashboard first</p>
          </div>
        ) : (
          <div className="space-y-4">
            {runningInstances.map(inst => (
              <div key={inst.id} className="flex items-center justify-between bg-gray-700 p-4 rounded">
                <div>
                  <p className="font-medium">{inst.gpu_name}</p>
                  <p className="text-sm text-gray-400">Instance ID: {inst.id}</p>
                </div>
                <button
                  onClick={() => createTunnel(inst.id)}
                  disabled={creating}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 px-4 py-2 rounded"
                >
                  {creating ? 'Connecting...' : 'Connect ComfyUI'}
                </button>
              </div>
            ))}
          </div>
        )}

        {tunnelPort && (
          <div className="mt-6 p-4 bg-green-900/30 border border-green-600 rounded">
            <p className="font-semibold text-green-400">Tunnel Active</p>
            <p className="mt-2">
              ComfyUI is available at:{' '}
              <a
                href={`http://localhost:${tunnelPort}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:underline"
              >
                http://localhost:{tunnelPort}
              </a>
            </p>
          </div>
        )}
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-gray-800 p-6 rounded">
          <h3 className="font-semibold mb-4">Available LoRAs</h3>
          {loras?.length === 0 ? (
            <p className="text-gray-400 text-sm">No LoRAs available. Train one first!</p>
          ) : (
            <ul className="space-y-2">
              {loras?.map(lora => (
                <li key={lora.name} className="text-sm flex justify-between">
                  <span>{lora.name}</span>
                  <span className="text-gray-400">{(lora.size / 1024 / 1024).toFixed(1)} MB</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="bg-gray-800 p-6 rounded">
          <h3 className="font-semibold mb-4">Quick Start</h3>
          <ol className="space-y-3 text-sm text-gray-300">
            <li className="flex gap-3">
              <span className="bg-blue-600 w-6 h-6 rounded-full flex items-center justify-center text-xs flex-shrink-0">1</span>
              Launch a ComfyUI instance from Dashboard
            </li>
            <li className="flex gap-3">
              <span className="bg-blue-600 w-6 h-6 rounded-full flex items-center justify-center text-xs flex-shrink-0">2</span>
              Click "Connect ComfyUI" to create SSH tunnel
            </li>
            <li className="flex gap-3">
              <span className="bg-blue-600 w-6 h-6 rounded-full flex items-center justify-center text-xs flex-shrink-0">3</span>
              Open ComfyUI in your browser
            </li>
            <li className="flex gap-3">
              <span className="bg-blue-600 w-6 h-6 rounded-full flex items-center justify-center text-xs flex-shrink-0">4</span>
              Load a workflow and add your trained LoRA
            </li>
          </ol>
        </div>
      </div>

      <div className="mt-6 bg-gray-800 p-6 rounded">
        <h3 className="font-semibold mb-4">Workflow Tips</h3>
        <div className="grid md:grid-cols-3 gap-4 text-sm">
          <div className="bg-gray-700 p-4 rounded">
            <p className="font-medium text-blue-400">Character LoRA</p>
            <p className="text-gray-400 mt-1">Use trigger word in prompt. Weight 0.7-1.0 recommended.</p>
          </div>
          <div className="bg-gray-700 p-4 rounded">
            <p className="font-medium text-purple-400">Style LoRA</p>
            <p className="text-gray-400 mt-1">Apply to CLIP and UNET. Weight 0.5-0.8 for subtle effects.</p>
          </div>
          <div className="bg-gray-700 p-4 rounded">
            <p className="font-medium text-green-400">Concept LoRA</p>
            <p className="text-gray-400 mt-1">Use specific trigger phrase. Weight 0.8-1.0 typically.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
