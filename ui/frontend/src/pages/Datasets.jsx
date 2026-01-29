import { useApi } from '../hooks/useApi'

export default function Datasets() {
  const { data: datasets, loading } = useApi('/datasets')

  if (loading) return <div>Loading...</div>

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Datasets</h1>
      <div className="mb-6">
        <label className="block bg-gray-800 p-8 rounded border-2 border-dashed border-gray-600 text-center cursor-pointer hover:border-gray-500">
          <input type="file" multiple className="hidden" />
          Drop images here or click to upload
        </label>
      </div>
      <div className="grid gap-4">
        {datasets?.map(ds => (
          <div key={ds.name} className="bg-gray-800 p-4 rounded">
            <p className="font-medium">{ds.name}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
