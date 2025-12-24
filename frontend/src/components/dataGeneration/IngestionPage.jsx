import { useState } from 'react'
import { usePipeline } from '../../context/PipelineContext'
import axios from 'axios'
import Card from '../common/Card'
import StatusBadge from '../common/StatusBadge'
import ProgressBar from '../common/ProgressBar'

function IngestionPage() {
  const { datasets, refreshDatasets } = usePipeline()
  const [selectedDataset, setSelectedSplit] = useState('')
  const [file, setFile] = useState(null)
  const [status, setStatus] = useState(null)
  const [progress, setProgress] = useState(0)

  const handleFileChange = (e) => {
    setFile(e.target.files[0])
  }

  const handleUpload = async () => {
    if (!selectedDataset || !file) {
      alert('Please select a dataset and a file')
      return
    }

    const formData = new FormData()
    formData.append('file', file)
    formData.append('dataset_id', selectedDataset)
    formData.append('data_type', 'garmin_csv')

    try {
      setStatus('uploading')
      const response = await axios.post('/api/ingestion/ingest', formData)
      const jobId = response.data.job_id
      setStatus('processing')
      
      // Start polling status
      const poll = setInterval(async () => {
        try {
          const res = await axios.get(`/api/data/generate/${jobId}/status`)
          const job = res.data
          setProgress(job.progress)
          if (job.status === 'completed') {
            clearInterval(poll)
            setStatus('completed')
            refreshDatasets()
          } else if (job.status === 'failed') {
            clearInterval(poll)
            setStatus('failed')
          }
        } catch (e) {
          clearInterval(poll)
          setStatus('failed')
        }
      }, 2000)

    } catch (error) {
      console.error('Upload failed:', error)
      setStatus('failed')
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Data Ingestion</h1>
        <p className="text-gray-600 mt-1">Upload real-world athlete data to enrich your datasets</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Upload Garmin Data">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Target Dataset
              </label>
              <select
                value={selectedDataset}
                onChange={e => setSelectedSplit(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select a dataset...</option>
                {datasets.map(d => (
                  <option key={d.id} value={d.id}>{d.id}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                CSV File (Garmin Export)
              </label>
              <input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
            </div>

            <button
              onClick={handleUpload}
              disabled={!file || !selectedDataset || status === 'processing'}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
            >
              {status === 'processing' ? 'Processing...' : 'Upload & Ingest'}
            </button>
          </div>
        </Card>

        <Card title="Ingestion Progress">
          {status ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="font-medium">Status</span>
                <StatusBadge status={status === 'uploading' ? 'running' : status} />
              </div>
              <ProgressBar progress={progress} status={status === 'failed' ? 'failed' : 'running'} />
              {status === 'completed' && (
                <p className="text-green-600">Data successfully merged into dataset!</p>
              )}
              {status === 'failed' && (
                <p className="text-red-600">Ingestion failed. Check backend logs.</p>
              )}
            </div>
          ) : (
            <p className="text-gray-500">Upload a file to see progress.</p>
          )}
        </Card>
      </div>
    </div>
  )
}

export default IngestionPage
