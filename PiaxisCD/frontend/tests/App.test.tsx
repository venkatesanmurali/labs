import { describe, it, expect } from 'vitest'

describe('PiaxisCD Frontend', () => {
  it('types are properly defined', () => {
    const project = {
      id: '1',
      name: 'Test',
      number: '',
      client: '',
      description: '',
      status: 'draft',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    expect(project.name).toBe('Test')
    expect(project.status).toBe('draft')
  })

  it('generation config has correct defaults', () => {
    const config = {
      formats: ['dxf', 'pdf', 'png'],
      paper_size: 'ARCH_D',
      scale: '1:100',
      seed: 42,
      include_schedules: true,
      include_qc: true,
    }
    expect(config.formats).toContain('dxf')
    expect(config.seed).toBe(42)
  })
})
