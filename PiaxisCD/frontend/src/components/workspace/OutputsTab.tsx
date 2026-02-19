import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import type { Artifact, QCIssue } from '../../types'

export default function OutputsTab({
  projectId,
  revisionId,
}: {
  projectId: string
  revisionId: string | null
}) {
  const [artifacts, setArtifacts] = useState<Artifact[]>([])
  const [qcIssues, setQcIssues] = useState<QCIssue[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!revisionId) return
    setLoading(true)
    Promise.all([
      api.listArtifacts(projectId, revisionId),
      api.listQCIssues(projectId, revisionId),
    ]).then(([artData, qcData]) => {
      setArtifacts(artData.artifacts)
      setQcIssues(qcData.qc_issues)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [projectId, revisionId])

  if (!revisionId) {
    return <div className="text-gray-400 py-8 text-center">No generation results yet. Go to Generate tab to create a CD set.</div>
  }

  if (loading) {
    return <div className="text-gray-400 py-8 text-center">Loading artifacts...</div>
  }

  const formatIcon = (type: string) => {
    const icons: Record<string, string> = { dxf: 'DXF', ifc: 'IFC', pdf: 'PDF', png: 'PNG', zip: 'ZIP' }
    return icons[type] || type.toUpperCase()
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div>
      {/* Download All */}
      <div className="mb-6">
        <a
          href={api.downloadUrl(projectId, revisionId)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700"
        >
          Download Complete Package (ZIP)
        </a>
      </div>

      {/* Artifact Grid */}
      <h3 className="font-medium mb-3">Generated Files ({artifacts.length})</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
        {artifacts.map((a) => (
          <a
            key={a.id}
            href={api.artifactDownloadUrl(projectId, revisionId, a.id)}
            className="p-3 bg-white border rounded-lg hover:border-primary-300 hover:shadow-sm transition-all block"
          >
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded flex items-center justify-center text-xs font-bold ${
                a.artifact_type === 'pdf' ? 'bg-red-100 text-red-700' :
                a.artifact_type === 'dxf' ? 'bg-blue-100 text-blue-700' :
                a.artifact_type === 'png' ? 'bg-green-100 text-green-700' :
                a.artifact_type === 'ifc' ? 'bg-purple-100 text-purple-700' :
                'bg-gray-100 text-gray-700'
              }`}>
                {formatIcon(a.artifact_type)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{a.filename}</p>
                <p className="text-xs text-gray-400">{a.description} - {formatSize(a.file_size)}</p>
              </div>
            </div>
          </a>
        ))}
      </div>

      {/* QC Issues */}
      {qcIssues.length > 0 && (
        <div>
          <h3 className="font-medium mb-3">QC Issues ({qcIssues.length})</h3>
          <div className="space-y-2">
            {qcIssues.map((issue) => (
              <div
                key={issue.id}
                className={`p-3 rounded border text-sm ${
                  issue.severity === 'error' ? 'bg-red-50 border-red-200 text-red-700' :
                  issue.severity === 'warning' ? 'bg-yellow-50 border-yellow-200 text-yellow-700' :
                  'bg-blue-50 border-blue-200 text-blue-700'
                }`}
              >
                <span className="font-medium uppercase text-xs">{issue.severity}</span>: {issue.message}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
