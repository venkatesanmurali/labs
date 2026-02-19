import { useState } from 'react'
import { api } from '../../api/client'
import type { GenerationConfig, GenerationStatus } from '../../types'

const DEFAULT_CONFIG: GenerationConfig = {
  formats: ['dxf', 'pdf', 'png'],
  paper_size: 'ARCH_D',
  scale: '1:100',
  seed: 42,
  include_schedules: true,
  include_qc: true,
}

export default function GenerateTab({
  projectId,
  onGenerated,
}: {
  projectId: string
  onGenerated: (status: GenerationStatus) => void
}) {
  const [config, setConfig] = useState<GenerationConfig>(DEFAULT_CONFIG)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')

  const toggleFormat = (fmt: string) => {
    setConfig(prev => ({
      ...prev,
      formats: prev.formats.includes(fmt)
        ? prev.formats.filter(f => f !== fmt)
        : [...prev.formats, fmt],
    }))
  }

  const handleGenerate = async () => {
    setRunning(true)
    setError('')
    try {
      const status = await api.generate(projectId, config)
      onGenerated(status)
    } catch (e) {
      setError(`Generation failed: ${e}`)
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="max-w-lg">
      <h3 className="font-medium mb-4">Generation Configuration</h3>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Export Formats</label>
          <div className="flex gap-2">
            {['dxf', 'ifc', 'pdf', 'png'].map(fmt => (
              <button
                key={fmt}
                onClick={() => toggleFormat(fmt)}
                className={`px-3 py-1.5 rounded text-sm uppercase ${
                  config.formats.includes(fmt)
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-600'
                }`}
              >
                {fmt}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Paper Size</label>
          <select
            value={config.paper_size}
            onChange={(e) => setConfig(prev => ({ ...prev, paper_size: e.target.value }))}
            className="w-full px-3 py-2 border rounded-lg text-sm"
          >
            {['ARCH_D', 'ARCH_E', 'A1', 'A2', 'A3'].map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Scale</label>
          <select
            value={config.scale}
            onChange={(e) => setConfig(prev => ({ ...prev, scale: e.target.value }))}
            className="w-full px-3 py-2 border rounded-lg text-sm"
          >
            {['1:50', '1:100', '1:200'].map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Random Seed</label>
          <input
            type="number"
            value={config.seed}
            onChange={(e) => setConfig(prev => ({ ...prev, seed: parseInt(e.target.value) || 42 }))}
            className="w-full px-3 py-2 border rounded-lg text-sm"
          />
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
            {error}
          </div>
        )}

        <button
          onClick={handleGenerate}
          disabled={running || config.formats.length === 0}
          className="w-full px-4 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50"
        >
          {running ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
              Generating CD Set...
            </span>
          ) : (
            'Generate CD Set'
          )}
        </button>
      </div>
    </div>
  )
}
