import { useApi } from '../hooks/useApi'

export default function Loras() {
  const { data: loras, loading } = useApi('/loras')

  if (loading) return <div>Loading...</div>

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Trained LoRAs</h1>
      <div className="grid gap-4">
        {loras?.map(lora => (
          <div key={lora.name} className="bg-gray-800 p-4 rounded flex justify-between">
            <div>
              <p className="font-medium">{lora.name}</p>
              <p className="text-sm text-gray-400">
                {(lora.size / 1024 / 1024).toFixed(1)} MB
              </p>
            </div>
            <button className="bg-blue-600 px-3 py-1 rounded text-sm">
              Download
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
