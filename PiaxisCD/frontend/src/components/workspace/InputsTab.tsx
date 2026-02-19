import { useState } from 'react'
import { api } from '../../api/client'
import type { RoomRequirement } from '../../types'

const DEFAULT_ROOMS: RoomRequirement[] = [
  { name: 'Living Room', function: 'living', area: 25, count: 1, adjacencies: [], must_have_window: null },
  { name: 'Kitchen', function: 'kitchen', area: 15, count: 1, adjacencies: [], must_have_window: null },
  { name: 'Bedroom', function: 'bedroom', area: 16, count: 2, adjacencies: [], must_have_window: null },
  { name: 'Bathroom', function: 'bathroom', area: 6, count: 1, adjacencies: [], must_have_window: null },
]

export default function InputsTab({ projectId }: { projectId: string }) {
  const [mode, setMode] = useState<'json' | 'text'>('json')
  const [rooms, setRooms] = useState<RoomRequirement[]>(DEFAULT_ROOMS)
  const [textReqs, setTextReqs] = useState('')
  const [saved, setSaved] = useState(false)

  const updateRoom = (idx: number, field: keyof RoomRequirement, value: string | number) => {
    setRooms(prev => prev.map((r, i) => i === idx ? { ...r, [field]: value } : r))
  }

  const addRoom = () => {
    setRooms(prev => [...prev, { name: '', function: 'custom', area: 10, count: 1, adjacencies: [], must_have_window: null }])
  }

  const removeRoom = (idx: number) => {
    setRooms(prev => prev.filter((_, i) => i !== idx))
  }

  const handleSave = async () => {
    try {
      if (mode === 'json') {
        await api.submitRequirements(projectId, { rooms })
      } else {
        await api.submitRequirementsText(projectId, textReqs)
      }
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (e) {
      alert(`Failed to save: ${e}`)
    }
  }

  return (
    <div>
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setMode('json')}
          className={`px-3 py-1.5 rounded text-sm ${mode === 'json' ? 'bg-primary-600 text-white' : 'bg-gray-100'}`}
        >
          Room Editor
        </button>
        <button
          onClick={() => setMode('text')}
          className={`px-3 py-1.5 rounded text-sm ${mode === 'text' ? 'bg-primary-600 text-white' : 'bg-gray-100'}`}
        >
          Text Input
        </button>
      </div>

      {mode === 'json' ? (
        <div className="space-y-3">
          {rooms.map((room, idx) => (
            <div key={idx} className="flex gap-2 items-center bg-white p-3 rounded border">
              <input
                type="text"
                value={room.name}
                onChange={(e) => updateRoom(idx, 'name', e.target.value)}
                placeholder="Room name"
                className="flex-1 px-2 py-1 border rounded text-sm"
              />
              <select
                value={room.function}
                onChange={(e) => updateRoom(idx, 'function', e.target.value)}
                className="px-2 py-1 border rounded text-sm"
              >
                {['living', 'kitchen', 'bedroom', 'bathroom', 'dining', 'office', 'storage', 'corridor', 'lobby', 'utility', 'custom'].map(f => (
                  <option key={f} value={f}>{f}</option>
                ))}
              </select>
              <input
                type="number"
                value={room.area}
                onChange={(e) => updateRoom(idx, 'area', parseFloat(e.target.value) || 0)}
                className="w-20 px-2 py-1 border rounded text-sm"
                min={1}
              />
              <span className="text-xs text-gray-400">m2</span>
              <input
                type="number"
                value={room.count}
                onChange={(e) => updateRoom(idx, 'count', parseInt(e.target.value) || 1)}
                className="w-16 px-2 py-1 border rounded text-sm"
                min={1}
              />
              <span className="text-xs text-gray-400">qty</span>
              <button onClick={() => removeRoom(idx)} className="text-red-400 hover:text-red-600 text-sm px-1">X</button>
            </div>
          ))}
          <button onClick={addRoom} className="text-sm text-primary-600 hover:text-primary-700">+ Add Room</button>
        </div>
      ) : (
        <textarea
          value={textReqs}
          onChange={(e) => setTextReqs(e.target.value)}
          placeholder={"# My Project\nLiving Room: 25 sqm\nKitchen: 15 sqm\n2x Bedrooms: 16 sqm\nBathroom: 6 sqm"}
          className="w-full h-64 p-3 border rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      )}

      <div className="mt-4 flex items-center gap-3">
        <button
          onClick={handleSave}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700"
        >
          Save Requirements
        </button>
        {saved && <span className="text-sm text-green-600">Saved!</span>}
      </div>
    </div>
  )
}
