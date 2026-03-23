import { useState } from 'react'
import { useApp } from '../context/AppContext'
import { AGENTS, PLANNED_AGENTS } from '../data/mockData'
import { Edit3, X, Check, Wrench, FileCode, Cpu, Shield, Zap, ChevronDown, GitBranch, ArrowDown } from 'lucide-react'

// ── Compact Agent Card for Organogram ─────────────────────────────────────────

function OrgCard({ agent, onEdit, compact }) {
  const statusDot = { ativo: '#10b981', standby: '#f59e0b', em_revisao: '#ef4444' }

  return (
    <div
      onClick={() => onEdit(agent)}
      className="card-hover p-3 cursor-pointer relative"
      style={{ minWidth: compact ? 180 : 220 }}
    >
      {/* Status dot */}
      <div className="absolute top-2 right-2 w-2 h-2 rounded-full" style={{ background: statusDot[agent.status] || '#666' }} />

      <div className="flex items-center gap-2.5 mb-2">
        <div className="w-9 h-9 rounded-lg flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
          style={{ background: agent.color }}>{agent.avatar}</div>
        <div className="min-w-0">
          <h4 className="text-xs font-bold text-white truncate">{agent.name}</h4>
          <p className="text-[9px] text-gold truncate">{agent.role?.split('—')[0]?.trim()}</p>
        </div>
      </div>

      {/* Model badge */}
      <div className="flex items-center gap-1.5 flex-wrap">
        <span className="flex items-center gap-0.5 text-[8px] text-gray-500 bg-surface-200 px-1.5 py-0.5 rounded">
          <Cpu size={8} /> {agent.model}
        </span>
        {agent.conditional && (
          <span className="text-[8px] text-accent-amber bg-accent-amber/10 px-1.5 py-0.5 rounded font-medium">Condicional</span>
        )}
        {agent.parallelGroup && (
          <span className="flex items-center gap-0.5 text-[8px] text-accent-blue bg-accent-blue/10 px-1.5 py-0.5 rounded">
            <GitBranch size={8} /> Paralelo
          </span>
        )}
      </div>

      {/* Capacity bar */}
      <div className="mt-2">
        <div className="flex justify-between text-[8px] text-gray-500 mb-0.5">
          <span>Carga</span><span>{agent.capacity}%</span>
        </div>
        <div className="h-1 bg-surface-200 rounded-full overflow-hidden">
          <div className="h-full rounded-full" style={{
            width: `${agent.capacity}%`,
            background: agent.capacity > 80 ? '#ef4444' : agent.capacity > 60 ? '#f59e0b' : '#10b981',
          }} />
        </div>
      </div>

      {/* Tools */}
      {agent.tools?.length > 0 && (
        <div className="flex flex-wrap gap-0.5 mt-1.5">
          {agent.tools.slice(0, 3).map(t => (
            <span key={t} className="text-[7px] text-gray-500 bg-surface px-1 py-0.5 rounded font-mono">{t}</span>
          ))}
          {agent.tools.length > 3 && <span className="text-[7px] text-gray-600">+{agent.tools.length - 3}</span>}
        </div>
      )}
    </div>
  )
}

// ── Connector Lines ───────────────────────────────────────────────────────────

function VertLine({ h = 24 }) {
  return <div className="flex justify-center"><div className="w-px bg-surface-300" style={{ height: h }} /></div>
}

function ArrowLine() {
  return (
    <div className="flex justify-center py-0.5">
      <ArrowDown size={14} className="text-surface-300" />
    </div>
  )
}

function ForkTop({ count }) {
  return (
    <div className="relative flex justify-center" style={{ height: 20 }}>
      <div className="absolute top-0 left-1/2 w-px h-2.5 bg-surface-300" />
      <div className="absolute top-2.5 bg-surface-300" style={{
        height: 1,
        left: `${50 - (count - 1) * 25}%`,
        right: `${50 - (count - 1) * 25}%`,
      }} />
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="absolute w-px h-2 bg-surface-300" style={{
          top: 10,
          left: `${50 + (i - (count - 1) / 2) * 50}%`,
        }} />
      ))}
    </div>
  )
}

function ForkBottom({ count }) {
  return (
    <div className="relative flex justify-center" style={{ height: 20 }}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="absolute w-px h-2 bg-surface-300" style={{
          top: 0,
          left: `${50 + (i - (count - 1) / 2) * 50}%`,
        }} />
      ))}
      <div className="absolute top-2 bg-surface-300" style={{
        height: 1,
        left: `${50 - (count - 1) * 25}%`,
        right: `${50 - (count - 1) * 25}%`,
      }} />
      <div className="absolute bottom-0 left-1/2 w-px h-2.5 bg-surface-300" />
    </div>
  )
}

// ── Edit Modal ────────────────────────────────────────────────────────────────

function EditAgentModal({ agent, onClose }) {
  const { dispatch, toast } = useApp()
  const [form, setForm] = useState({
    name: agent.name, specialty: agent.specialty,
    promptBase: agent.promptBase, autonomy: agent.autonomy,
  })
  const save = () => {
    dispatch({ type: 'UPDATE_AGENT', payload: { id: agent.id, updates: form } })
    toast('Agente atualizado', 'info'); onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100] flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-surface-50 border border-surface-200 rounded-xl w-full max-w-lg p-6 max-h-[85vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold text-white" style={{ background: agent.color }}>{agent.avatar}</div>
            <h3 className="text-lg font-bold text-white">{agent.name}</h3>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white"><X size={18} /></button>
        </div>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div><label className="text-xs text-gray-400 mb-1 block">Nome</label><input className="input-field" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></div>
            <div><label className="text-xs text-gray-400 mb-1 block">Modelo LLM</label><input className="input-field bg-surface-200 text-gray-500" value={agent.model || '—'} readOnly /></div>
          </div>
          <div><label className="text-xs text-gray-400 mb-1 block">Especializacao</label><textarea className="input-field h-20 resize-none" value={form.specialty} onChange={e => setForm({ ...form, specialty: e.target.value })} /></div>
          <div><label className="text-xs text-gray-400 mb-1 block">Prompt Base</label><textarea className="input-field h-24 resize-none text-xs font-mono" value={form.promptBase} onChange={e => setForm({ ...form, promptBase: e.target.value })} /></div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Autonomia: {form.autonomy}%</label>
            <input type="range" min="0" max="100" value={form.autonomy} onChange={e => setForm({ ...form, autonomy: +e.target.value })} className="w-full accent-gold" />
          </div>
          {agent.conditional && (
            <div className="p-3 bg-accent-amber/5 border border-accent-amber/20 rounded-lg">
              <p className="text-[10px] text-accent-amber flex items-center gap-1.5"><Zap size={11} /> {agent.conditional}</p>
            </div>
          )}
          <div className="text-[10px] text-gray-500 space-y-1">
            <p><FileCode size={10} className="inline mr-1" />{agent.file}</p>
            {agent.tools?.length > 0 && <p><Wrench size={10} className="inline mr-1" />Tools: {agent.tools.join(', ')}</p>}
            <p><Shield size={10} className="inline mr-1" />{agent.allowDelegation ? 'Pode delegar' : 'Sem delegacao'}</p>
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-5">
          <button onClick={onClose} className="btn-ghost">Cancelar</button>
          <button onClick={save} className="btn-primary">Salvar</button>
        </div>
      </div>
    </div>
  )
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function AgentStructure() {
  const { state } = useApp()
  const [editAgent, setEditAgent] = useState(null)
  const [viewMode, setViewMode] = useState('org') // 'org' | 'grid'

  const sorted = [...state.agents].sort((a, b) => (a.pipelineOrder || 99) - (b.pipelineOrder || 99))

  // Group by pipeline step
  const step1 = sorted.filter(a => a.pipelineOrder === 1)  // MD
  const step2 = sorted.filter(a => a.pipelineOrder === 2)  // Accountant
  const step3 = sorted.filter(a => a.pipelineOrder === 3)  // Research
  const step4 = sorted.filter(a => a.pipelineOrder === 4)  // Financial Modeler
  const step5 = sorted.filter(a => a.pipelineOrder === 5)  // DCM || ECM (parallel conditional)
  const step6 = sorted.filter(a => a.pipelineOrder === 6)  // Quant || Risk (parallel)
  const step7 = sorted.filter(a => a.pipelineOrder === 7)  // Deck Builder

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-xl font-bold text-white font-editorial">Estrutura de Agentes</h2>
        <div className="flex gap-1">
          {['org', 'grid'].map(m => (
            <button key={m} onClick={() => setViewMode(m)}
              className={`px-3 py-1 rounded text-[10px] font-medium ${viewMode === m ? 'bg-gold/15 text-gold' : 'text-gray-500 hover:text-gray-300'}`}>
              {m === 'org' ? 'Organograma' : 'Grid'}
            </button>
          ))}
        </div>
      </div>
      <p className="text-xs text-gray-500 mb-6">
        9 agentes · Clique em um card para editar · <GitBranch size={10} className="inline" /> indica execucao paralela
      </p>

      {viewMode === 'org' ? (
        <div className="overflow-x-auto pb-4">
          <div className="min-w-[700px] flex flex-col items-center">

            {/* Input */}
            <div className="card px-4 py-2 text-center">
              <span className="text-[9px] text-gray-500 uppercase tracking-wider font-bold">Input</span>
              <p className="text-[10px] text-gray-400">Excel / PDF</p>
            </div>
            <ArrowLine />

            {/* Step 1: MD Orchestrator */}
            {step1.map(a => <OrgCard key={a.id} agent={a} onEdit={setEditAgent} />)}
            <ArrowLine />

            {/* Step 2: Accountant (reviews first) */}
            {step2.map(a => <OrgCard key={a.id} agent={a} onEdit={setEditAgent} />)}
            <ArrowLine />

            {/* Step 3: Research Analyst */}
            {step3.map(a => <OrgCard key={a.id} agent={a} onEdit={setEditAgent} />)}
            <ArrowLine />

            {/* Step 3.5: Accountant again (adjustments post-parsing) */}
            <div className="card px-3 py-1.5 text-center border-dashed border-[#059669]/30 bg-[#059669]/5">
              <span className="text-[9px] text-[#059669] font-bold">Accountant — Ajustes Pos-Parsing</span>
              <p className="text-[9px] text-gray-500">IFRS 16, EBITDA, provisoes (mesmo agente, segunda passada)</p>
            </div>
            <ArrowLine />

            {/* Step 4: Financial Modeler */}
            {step4.map(a => <OrgCard key={a.id} agent={a} onEdit={setEditAgent} />)}

            {/* Step 5: Fork — DCM || ECM (parallel conditional) */}
            {step5.length > 0 && (
              <>
                <ForkTop count={step5.length} />
                <div className="flex items-center gap-4 mb-0">
                  <div className="card px-2 py-1 text-[8px] text-accent-amber font-bold border-accent-amber/20 bg-accent-amber/5">
                    Condicional ∥
                  </div>
                </div>
                <div className="flex gap-4 justify-center">
                  {step5.map(a => <OrgCard key={a.id} agent={a} onEdit={setEditAgent} compact />)}
                </div>
                <ForkBottom count={step5.length} />
              </>
            )}
            {step5.length === 0 && <ArrowLine />}

            {/* Step 6: Fork — Quant || Risk (parallel) */}
            <ForkTop count={step6.length} />
            <div className="flex items-center gap-4 mb-0">
              <div className="card px-2 py-1 text-[8px] text-accent-blue font-bold border-accent-blue/20 bg-accent-blue/5 flex items-center gap-1">
                <GitBranch size={9} /> Execucao Paralela
              </div>
            </div>
            <div className="flex gap-4 justify-center">
              {step6.map(a => <OrgCard key={a.id} agent={a} onEdit={setEditAgent} compact />)}
            </div>
            <ForkBottom count={step6.length} />

            {/* Step 7: Deck Builder */}
            {step7.map(a => <OrgCard key={a.id} agent={a} onEdit={setEditAgent} />)}
            <ArrowLine />

            {/* Output */}
            <div className="card px-4 py-2 text-center">
              <span className="text-[9px] text-gray-500 uppercase tracking-wider font-bold">Output</span>
              <p className="text-[10px] text-gray-400">PPTX + XLSX + PDF</p>
            </div>
          </div>
        </div>
      ) : (
        /* Grid view */
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {sorted.map(a => <OrgCard key={a.id} agent={a} onEdit={setEditAgent} />)}
        </div>
      )}

      {editAgent && <EditAgentModal agent={editAgent} onClose={() => setEditAgent(null)} />}
    </div>
  )
}
