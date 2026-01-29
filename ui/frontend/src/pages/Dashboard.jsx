import { useApi, apiPost, apiDelete } from '../hooks/useApi'

export default function Dashboard() {
  const { data: instances, loading, refetch } = useApi('/instances')

  const launchTrainer = async () => {
    await apiPost('/instances/launch', {
      gpu_type: 'A100',
      image: 'your-dockerhub/flux-lora-trainer:latest',
      max_price: 1.5
    })
    refetch()
  }

  const launchComfy = async () => {
    await apiPost('/instances/launch', {
      gpu_type: 'RTX 4090',
      image: 'your-dockerhub/flux-comfyui:latest',
      max_price: 0.5
    })
    refetch()
  }

  const stopInstance = async (id) => {
    await apiDelete(`/instances/${id}`)
    refetch()
  }

  if (loading) return <div>Loading...</div>

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

      <div className="flex gap-4 mb-8">
        <button
          onClick={launchTrainer}
          className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded"
        >
          Launch Training Instance
        </button>
        <button
          onClick={launchComfy}
          className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded"
        >
          Launch ComfyUI
        </button>
      </div>

      <h2 className="text-xl font-semibold mb-4">Active Instances</h2>
      {instances?.length === 0 ? (
        <p className="text-gray-400">No running instances</p>
      ) : (
        <div className="grid gap-4">
          {instances?.map(inst => (
            <div key={inst.id} className="bg-gray-800 p-4 rounded flex justify-between items-center">
              <div>
                <p className="font-medium">{inst.gpu_name}</p>
                <p className="text-sm text-gray-400">
                  ${inst.dph_total?.toFixed(2)}/hr | {inst.status}
                </p>
              </div>
              <div className="flex gap-2">
                <button className="bg-blue-600 px-3 py-1 rounded text-sm">
                  Connect
                </button>
                <button
                  onClick={() => stopInstance(inst.id)}
                  className="bg-red-600 px-3 py-1 rounded text-sm"
                >
                  Stop
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
