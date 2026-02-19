import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { DemoResult, Project } from '../types'

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const [demoResult, setDemoResult] = useState<DemoResult | null>(null)
  const [demoLoading, setDemoLoading] = useState(false)
  const navigate = useNavigate()

  const fetchProjects = async () => {
    try {
      const data = await api.listProjects()
      setProjects(data.projects)
    } catch {
      // DB might not be available
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchProjects() }, [])

  const handleCreate = async () => {
    if (!newName.trim()) return
    try {
      const project = await api.createProject({ name: newName.trim() })
      navigate(`/projects/${project.id}`)
    } catch (e) {
      alert(`Failed to create project: ${e}`)
    }
  }

  const handleDemo = async () => {
    setDemoLoading(true)
    try {
      const result = await api.runDemo()
      setDemoResult(result)
    } catch (e) {
      alert(`Demo failed: ${e}`)
    } finally {
      setDemoLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Projects</h1>
        <div className="flex gap-3">
          <button
            onClick={handleDemo}
            disabled={demoLoading}
            className="px-4 py-2 bg-accent-500 text-white rounded-lg hover:bg-accent-600 disabled:opacity-50 text-sm font-medium"
          >
            {demoLoading ? 'Running Demo...' : 'Demo Mode'}
          </button>
          <button
            onClick={() => setShowCreate(true)}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm font-medium"
          >
            New Project
          </button>
        </div>
      </div>

      {/* Demo Result */}
      {demoResult && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <h3 className="font-semibold text-green-800 mb-2">Demo Complete: {demoResult.project_name}</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm mb-3">
            <div><span className="text-gray-500">Rooms:</span> {demoResult.rooms}</div>
            <div><span className="text-gray-500">Walls:</span> {demoResult.walls}</div>
            <div><span className="text-gray-500">Doors:</span> {demoResult.doors}</div>
            <div><span className="text-gray-500">Windows:</span> {demoResult.windows}</div>
            <div><span className="text-gray-500">Sheets:</span> {demoResult.sheets}</div>
            <div><span className="text-gray-500">Files:</span> {demoResult.files.length}</div>
          </div>
          <div className="mb-2">
            <span className="text-sm text-gray-500">Generated files:</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {demoResult.files.map((f) => (
                <span key={f} className="px-2 py-0.5 bg-white border rounded text-xs">{f}</span>
              ))}
            </div>
          </div>
          {demoResult.qc_issues.length > 0 && (
            <div>
              <span className="text-sm text-yellow-700">QC Issues:</span>
              <ul className="text-xs text-yellow-600 mt-1">
                {demoResult.qc_issues.map((q, i) => <li key={i}>{q}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Create Dialog */}
      {showCreate && (
        <div className="mb-6 p-4 bg-white border rounded-lg shadow-sm">
          <h3 className="font-medium mb-3">Create New Project</h3>
          <div className="flex gap-3">
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Project name..."
              className="flex-1 px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
              autoFocus
            />
            <button onClick={handleCreate} className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm">
              Create
            </button>
            <button onClick={() => setShowCreate(false)} className="px-4 py-2 border rounded-lg text-sm">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Project List */}
      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading projects...</div>
      ) : projects.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-400 mb-4">No projects yet</p>
          <p className="text-sm text-gray-400">Create a new project or try Demo Mode</p>
        </div>
      ) : (
        <div className="space-y-2">
          {projects.map((p) => (
            <div
              key={p.id}
              onClick={() => navigate(`/projects/${p.id}`)}
              className="p-4 bg-white border rounded-lg hover:border-primary-300 hover:shadow-sm cursor-pointer transition-all"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">{p.name}</h3>
                  <p className="text-sm text-gray-400">
                    {p.number && `#${p.number} · `}
                    {p.client && `${p.client} · `}
                    {new Date(p.created_at).toLocaleDateString()}
                  </p>
                </div>
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                  p.status === 'completed' ? 'bg-green-100 text-green-700' :
                  p.status === 'running' ? 'bg-blue-100 text-blue-700' :
                  'bg-gray-100 text-gray-600'
                }`}>
                  {p.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
