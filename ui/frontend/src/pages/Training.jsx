import { useState } from 'react'
import { useApi, apiPost, apiDelete } from '../hooks/useApi'

const LORA_TYPES = ['character', 'style', 'concept']

function TrainingProgressBar({ job }) {
  const progress = job.steps > 0 ? (job.current_step / job.steps) * 100 : 0
  const isRunning = job.status === 'running'
  const isCompleted = job.status === 'completed'
  const isFailed = job.status === 'failed'

  // Estimate time remaining (rough estimate: ~1 step per second on average)
  const stepsRemaining = job.steps - job.current_step
  const secondsRemaining = stepsRemaining
  const formatTime = (seconds) => {
    if (seconds < 60) return `${seconds}s`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`
  }

  const barColor = isCompleted ? 'bg-green-500' : isFailed ? 'bg-red-500' : 'bg-blue-500'
  const barBg = isCompleted ? 'bg-green-900' : isFailed ? 'bg-red-900' : 'bg-gray-700'

  return (
    <div className="mt-3">
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-300">
          {isCompleted ? '✓ Completed' : isFailed ? '✗ Failed' : `Step ${job.current_step.toLocaleString()} / ${job.steps.toLocaleString()}`}
        </span>
        <span className="text-gray-400">
          {isRunning && stepsRemaining > 0 && `~${formatTime(secondsRemaining)} remaining`}
          {isCompleted && 'Done!'}
          {isFailed && job.error}
        </span>
      </div>
      <div className={`h-3 ${barBg} rounded-full overflow-hidden`}>
        <div
          className={`h-full ${barColor} rounded-full transition-all duration-500 ${isRunning ? 'animate-pulse' : ''}`}
          style={{ width: `${isCompleted ? 100 : progress}%` }}
        />
      </div>
      <div className="flex justify-between text-xs text-gray-500 mt-1">
        <span>{progress.toFixed(1)}%</span>
        {isRunning && job.current_step > 0 && (
          <span>
            {((job.current_step / Math.max(1, (Date.now() - new Date(job.started_at).getTime()) / 1000)) || 0).toFixed(1)} steps/sec
          </span>
        )}
      </div>
    </div>
  )
}

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
            <div key={job.id} className={`bg-gray-800 p-4 rounded border-l-4 ${
              job.status === 'running' ? 'border-blue-500' :
              job.status === 'completed' ? 'border-green-500' :
              job.status === 'failed' ? 'border-red-500' :
              'border-yellow-500'
            }`}>
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${statusColors[job.status]} ${job.status === 'running' ? 'animate-pulse' : ''}`}></span>
                    <p className="font-medium text-lg">{job.lora_name}</p>
                    <span className="text-sm px-2 py-0.5 bg-gray-700 rounded">{job.lora_type}</span>
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      job.status === 'running' ? 'bg-blue-600' :
                      job.status === 'completed' ? 'bg-green-600' :
                      job.status === 'failed' ? 'bg-red-600' :
                      'bg-yellow-600'
                    }`}>
                      {job.status.toUpperCase()}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-4 text-sm text-gray-400 mt-2">
                    <span>📁 {job.dataset_name}</span>
                    <span>🔄 {job.steps.toLocaleString()} steps</span>
                    <span>📐 {job.resolution}px</span>
                    <span>🧮 dim={job.network_dim}</span>
                    <span>📊 lr={job.learning_rate}</span>
                  </div>
                  <TrainingProgressBar job={job} />
                </div>
                <div className="flex flex-col gap-2 ml-4">
                  {job.status === 'running' && (
                    <button
                      onClick={() => deleteJob(job.id)}
                      className="bg-yellow-600 hover:bg-yellow-700 px-3 py-1 rounded text-sm"
                    >
                      Cancel
                    </button>
                  )}
                  <button
                    onClick={() => deleteJob(job.id)}
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
    </div>
  )
}
