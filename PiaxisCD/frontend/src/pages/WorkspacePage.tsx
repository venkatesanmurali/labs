import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '../api/client'
import type { GenerationStatus, Project } from '../types'
import InputsTab from '../components/workspace/InputsTab'
import GenerateTab from '../components/workspace/GenerateTab'
import OutputsTab from '../components/workspace/OutputsTab'

type Tab = 'inputs' | 'generate' | 'outputs'

export default function WorkspacePage() {
  const { projectId } = useParams<{ projectId: string }>()
  const [project, setProject] = useState<Project | null>(null)
  const [tab, setTab] = useState<Tab>('inputs')
  const [latestRevisionId, setLatestRevisionId] = useState<string | null>(null)

  useEffect(() => {
    if (!projectId) return
    api.getProject(projectId).then(setProject).catch(() => {})
    api.listRevisions(projectId).then(data => {
      if (data.revisions.length > 0) {
        setLatestRevisionId(data.revisions[0].id)
      }
    }).catch(() => {})
  }, [projectId])

  const handleGenerated = (status: GenerationStatus) => {
    setLatestRevisionId(status.revision_id)
    setTab('outputs')
  }

  if (!projectId) return <div>No project ID</div>

  const tabs: { key: Tab; label: string }[] = [
    { key: 'inputs', label: 'Inputs' },
    { key: 'generate', label: 'Generate' },
    { key: 'outputs', label: 'Outputs' },
  ]

  return (
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <Link to="/" className="text-gray-400 hover:text-gray-600">&larr;</Link>
        <div>
          <h1 className="text-xl font-bold">{project?.name || 'Loading...'}</h1>
          {project && (
            <p className="text-sm text-gray-400">
              {project.number && `#${project.number} · `}
              {project.client && `${project.client} · `}
              {project.status}
            </p>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 border-b">
        {tabs.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
              tab === t.key
                ? 'border-primary-600 text-primary-700'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div>
        {tab === 'inputs' && <InputsTab projectId={projectId} />}
        {tab === 'generate' && <GenerateTab projectId={projectId} onGenerated={handleGenerated} />}
        {tab === 'outputs' && <OutputsTab projectId={projectId} revisionId={latestRevisionId} />}
      </div>
    </div>
  )
}
