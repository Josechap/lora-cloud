import { useState } from 'react'
import { useApi, apiPost, apiDelete } from '../hooks/useApi'

const LORA_TYPES = ['character', 'style', 'concept']

export default function Training() {
  const { data: datasets } = useApi('/datasets')
  const { data: instances } = useApi('/instances')
  const { data: jobs, refetch } = useApi('/training', { pollInterval: 5000 })

  const [config, setConfig] = useState({
    dataset_name: '',
    lora_name: '',
    lora_type: 'character',
    steps: 1000,
    learning_rate: 0.0001,
    batch_size: 1,
    resolution: 512,
    network_dim: 32,
    network_alpha: 16
  })

  const createJob = async () => {
    if (!config.dataset_name || !config.lora_name) {
      alert('Please select a dataset and enter a LoRA name')
      return
    }
    const runningInstances = instances?.filter(i => i.cur_state === 'running') || []
    if (runningInstances.length === 0) {
      alert('No running instances. Please launch one from the Dashboard first.')
      return
    }
    await apiPost('/training', {
      ...config,
      instance_id: runningInstances[0].id
    })
    refetch()
  }

  const deleteJob = async (id) => {
    await apiDelete(`/training/${id}`)
    refetch()
  }

  const statusColors = {
    pending: 'bg-yellow-500',
    running: 'bg-blue-500',
    completed: 'bg-green-500',
    failed: 'bg-red-500'
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Training</h1>

      <div className="bg-gray-800 p-6 rounded mb-8">
        <h2 className="text-lg font-semibold mb-4">New Training Job</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Dataset</label>
            <select
              value={config.dataset_name}
              onChange={(e) => setConfig({...config, dataset_name: e.target.value})}
              className="w-full bg-gray-700 px-3 py-2 rounded"
            >
              <option value="">Select dataset...</option>
              {datasets?.map(ds => (
                <option key={ds.name} value={ds.name}>{ds.name} ({ds.file_count} images)</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">LoRA Name</label>
            <input
              type="text"
              value={config.lora_name}
              onChange={(e) => setConfig({...config, lora_name: e.target.value})}
              placeholder="my-lora"
              className="w-full bg-gray-700 px-3 py-2 rounded"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Type</label>
            <select
              value={config.lora_type}
              onChange={(e) => setConfig({...config, lora_type: e.target.value})}
              className="w-full bg-gray-700 px-3 py-2 rounded"
            >
              {LORA_TYPES.map(t => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Steps</label>
            <input
              type="number"
              value={config.steps}
              onChange={(e) => setConfig({...config, steps: parseInt(e.target.value)})}
              className="w-full bg-gray-700 px-3 py-2 rounded"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Learning Rate</label>
            <input
              type="number"
              step="0.00001"
              value={config.learning_rate}
              onChange={(e) => setConfig({...config, learning_rate: parseFloat(e.target.value)})}
              className="w-full bg-gray-700 px-3 py-2 rounded"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Resolution</label>
            <select
              value={config.resolution}
              onChange={(e) => setConfig({...config, resolution: parseInt(e.target.value)})}
              className="w-full bg-gray-700 px-3 py-2 rounded"
            >
              <option value={512}>512</option>
              <option value={768}>768</option>
              <option value={1024}>1024</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Network Dim</label>
            <input
              type="number"
              value={config.network_dim}
              onChange={(e) => setConfig({...config, network_dim: parseInt(e.target.value)})}
              className="w-full bg-gray-700 px-3 py-2 rounded"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Network Alpha</label>
            <input
              type="number"
              value={config.network_alpha}
              onChange={(e) => setConfig({...config, network_alpha: parseInt(e.target.value)})}
              className="w-full bg-gray-700 px-3 py-2 rounded"
            />
          </div>
        </div>
        <button
          onClick={createJob}
          className="mt-4 bg-green-600 hover:bg-green-700 px-6 py-2 rounded"
        >
          Start Training
        </button>
      </div>

      <h2 className="text-xl font-semibold mb-4">Training Jobs</h2>
      {jobs?.length === 0 ? (
        <div className="bg-gray-800 p-8 rounded text-center text-gray-400">
          <p>No training jobs yet</p>
          <p className="text-sm mt-2">Configure and start a training job above</p>
        </div>
      ) : (
        <div className="space-y-4">
          {jobs?.map(job => (
            <div key={job.id} className="bg-gray-800 p-4 rounded">
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${statusColors[job.status]}`}></span>
                    <p className="font-medium">{job.lora_name}</p>
                    <span className="text-sm text-gray-400">({job.lora_type})</span>
                  </div>
                  <p className="text-sm text-gray-400 mt-1">
                    Dataset: {job.dataset_name} • {job.steps} steps • {job.resolution}px
                  </p>
                  {job.status === 'running' && (
                    <div className="mt-2">
                      <div className="h-2 bg-gray-700 rounded overflow-hidden">
                        <div
                          className="h-full bg-blue-500 transition-all"
                          style={{ width: `${(job.current_step / job.steps) * 100}%` }}
                        ></div>
                      </div>
                      <p className="text-xs text-gray-400 mt-1">
                        Step {job.current_step} / {job.steps}
                      </p>
                    </div>
                  )}
                  {job.error && (
                    <p className="text-sm text-red-400 mt-1">{job.error}</p>
                  )}
                </div>
                <button
                  onClick={() => deleteJob(job.id)}
                  className="bg-red-600 hover:bg-red-700 px-3 py-1 rounded text-sm"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
