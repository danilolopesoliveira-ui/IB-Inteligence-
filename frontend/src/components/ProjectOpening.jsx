import { useState, useRef } from 'react'
import { useApp } from '../context/AppContext'
import { AGENTS, DOC_CHECKLISTS, OPERATIONS, PENDING_ITEMS, BRL_COMPACT } from '../data/mockData'
import { ChevronRight, CheckCircle, Clock, XCircle, Download, Upload, Bell, ChevronDown, AlertTriangle, FolderOpen, File } from 'lucide-react'

const API = import.meta.env.VITE_API_URL || ''

const STEPS = ['Identificacao', 'Checklist de Documentos', 'Configuracao dos Agentes']

function Stepper({ step, setStep }) {
  return (
    <div className="flex items-center gap-2 mb-6">
      {STEPS.map((s, i) => (
        <div key={i} className="flex items-center gap-2">
          <button
            onClick={() => setStep(i)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
              i === step ? 'bg-gold/15 text-gold' : i < step ? 'bg-accent-green/10 text-accent-green' : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
              i === step ? 'bg-gold text-black' : i < step ? 'bg-accent-green text-black' : 'bg-surface-200 text-gray-500'
            }`}>{i < step ? '✓' : i + 1}</span>
            {s}
          </button>
          {i < STEPS.length - 1 && <div className="w-8 h-px bg-surface-200" />}
        </div>
      ))}
    </div>
  )
}

function StepIdentification({ form, setForm }) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div><label className="text-xs text-gray-400 mb-1 block">Empresa Emissora</label><input className="input-field" value={form.company} onChange={e => setForm({ ...form, company: e.target.value })} placeholder="Ex: Eneva S.A." /></div>
        <div><label className="text-xs text-gray-400 mb-1 block">CNPJ</label><input className="input-field" value={form.cnpj} onChange={e => setForm({ ...form, cnpj: e.target.value })} placeholder="00.000.000/0001-00" /></div>
      </div>
      <div className="grid grid-cols-3 gap-4">
        <div><label className="text-xs text-gray-400 mb-1 block">Setor</label><input className="input-field" value={form.sector} onChange={e => setForm({ ...form, sector: e.target.value })} placeholder="Energia Eletrica" /></div>
        <div><label className="text-xs text-gray-400 mb-1 block">Tipo de Operacao</label>
          <select className="input-field" value={form.opType} onChange={e => setForm({ ...form, opType: e.target.value })}>
            <optgroup label="DCM"><option>Debentures</option><option>CRI</option><option>CRA</option><option>CCB</option><option>Loan Offshore</option><option>Bilateral</option></optgroup>
            <optgroup label="ECM"><option>IPO</option><option>Follow-on</option><option>Block Trade</option></optgroup>
          </select>
        </div>
        <div><label className="text-xs text-gray-400 mb-1 block">Valor Estimado (R$)</label><input className="input-field" value={form.value} onChange={e => setForm({ ...form, value: e.target.value })} placeholder="800000000" /></div>
      </div>
      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Prazo Desejado (meses)</label>
          <select className="input-field" value={form.deadline} onChange={e => setForm({ ...form, deadline: e.target.value })}>
            <option value="">Selecione...</option>
            {[3,6,9,12,18,24,36,48,60,84,120].map(m => (
              <option key={m} value={m}>{m} meses{m >= 12 ? ` (${m/12} ${m/12===1?'ano':'anos'})` : ''}</option>
            ))}
          </select>
        </div>
        <div><label className="text-xs text-gray-400 mb-1 block">Rating Atual</label><input className="input-field" value={form.rating} onChange={e => setForm({ ...form, rating: e.target.value })} placeholder="AA+ (Fitch)" /></div>
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Tipo de Garantia</label>
          <select className="input-field" value={form.guarantee} onChange={e => setForm({ ...form, guarantee: e.target.value })}>
            <option value="">Selecione...</option>
            <option>Quirografaria (sem garantia)</option>
            <option>Real — Imoveis</option>
            <option>Real — Recebiveis</option>
            <option>Real — Equipamentos</option>
            <option>Fidejussoria — Aval/Fianca</option>
            <option>Fidejussoria — Fianca Bancaria</option>
            <option>Cessao Fiduciaria de Recebiveis</option>
            <option>Alienacao Fiduciaria de Imovel</option>
            <option>Alienacao Fiduciaria de Acoes</option>
            <option>Penhor de Acoes</option>
            <option>Fundo de Reserva</option>
            <option>Subordinacao Estrutural</option>
            <option>Garantia Corporativa (Holding)</option>
            <option>Multipla (combinada)</option>
          </select>
        </div>
      </div>
    </div>
  )
}

function StepChecklist({ form }) {
  const { toast } = useApp()
  const docs = DOC_CHECKLISTS[form.opType] || DOC_CHECKLISTS['Debentures']
  const [statuses, setStatuses] = useState(docs.map(() => 'pendente'))
  const [uploaded, setUploaded] = useState({}) // { docIndex: [{name, size_kb}] }
  const [uploading, setUploading] = useState(null)
  const fileRefs = useRef({})

  const cycle = (i) => {
    const next = { pendente: 'recebido', recebido: 'na', na: 'pendente' }
    setStatuses(prev => prev.map((s, idx) => idx === i ? next[s] : s))
  }

  const handleUpload = async (i, file) => {
    if (!file) return
    const company = form.company || 'empresa'
    setUploading(i)
    try {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('company', company)
      const res = await fetch(`${API}/api/upload`, { method: 'POST', body: fd })
      const data = await res.json()
      if (data.ok) {
        setUploaded(prev => ({ ...prev, [i]: [...(prev[i] || []), { name: data.file, size_kb: data.size_kb }] }))
        setStatuses(prev => prev.map((s, idx) => idx === i ? 'recebido' : s))
        toast(`Salvo em uploads/${company.toLowerCase().replace(/\s+/g, '_')}/`, 'success')
      }
    } catch {
      toast('Erro ao fazer upload — verifique se o servidor esta rodando', 'error')
    } finally {
      setUploading(null)
    }
  }

  const icons = { recebido: CheckCircle, pendente: Clock, na: XCircle }
  const colors = { recebido: 'text-accent-green', pendente: 'text-gold', na: 'text-gray-500' }
  const labels = { recebido: 'Recebido', pendente: 'Pendente', na: 'N/A' }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs text-gray-400">Clique no status para alternar · Documentos para: <span className="text-gold">{form.opType}</span></p>
        {form.company && (
          <div className="flex items-center gap-1.5 text-[10px] text-gray-500 bg-surface-100 px-2.5 py-1 rounded-lg">
            <FolderOpen size={11} className="text-gold" />
            uploads/{form.company.toLowerCase().replace(/\s+/g, '_')}/
          </div>
        )}
      </div>
      {docs.map((doc, i) => {
        const Icon = icons[statuses[i]]
        const files = uploaded[i] || []
        return (
          <div key={i} className="card-hover p-3">
            <div className="flex items-center gap-3">
              <button onClick={() => cycle(i)} className={`${colors[statuses[i]]} flex-shrink-0`}><Icon size={18} /></button>
              <span className="text-sm text-gray-200 flex-1">{doc}</span>
              <span className={`text-[10px] font-medium ${colors[statuses[i]]}`}>{labels[statuses[i]]}</span>
              <button className="btn-ghost p-1" title="Download template"><Download size={14} /></button>
              <input
                type="file"
                ref={el => fileRefs.current[i] = el}
                className="hidden"
                onChange={e => handleUpload(i, e.target.files[0])}
              />
              <button
                className={`btn-ghost p-1 ${uploading === i ? 'animate-pulse text-gold' : ''}`}
                title="Upload documento"
                onClick={() => fileRefs.current[i]?.click()}
                disabled={uploading !== null}
              >
                <Upload size={14} />
              </button>
            </div>
            {files.length > 0 && (
              <div className="mt-2 ml-7 flex flex-wrap gap-1.5">
                {files.map((f, j) => (
                  <span key={j} className="flex items-center gap-1 text-[10px] text-accent-green bg-accent-green/10 px-2 py-0.5 rounded">
                    <File size={9} /> {f.name} <span className="text-gray-500">({f.size_kb}kb)</span>
                  </span>
                ))}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

function StepAgents({ form, setForm }) {
  return (
    <div className="space-y-4">
      <div>
        <label className="text-xs text-gray-400 mb-2 block">Agentes a Acionar</label>
        <div className="flex flex-wrap gap-2">
          {AGENTS.map(a => (
            <button
              key={a.id}
              onClick={() => setForm({
                ...form,
                agents: form.agents.includes(a.id) ? form.agents.filter(x => x !== a.id) : [...form.agents, a.id]
              })}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-xs font-medium transition-all ${
                form.agents.includes(a.id) ? 'border-gold text-gold bg-gold/10' : 'border-surface-200 text-gray-400 hover:text-gray-200'
              }`}
            >
              <div className="w-5 h-5 rounded-full flex items-center justify-center text-[8px] font-bold text-white" style={{ background: a.color }}>{a.avatar}</div>
              {a.name}
            </button>
          ))}
        </div>
      </div>
      <div>
        <label className="text-xs text-gray-400 mb-1 block">Prioridade</label>
        <div className="flex gap-2">
          {['Alta', 'Media', 'Baixa'].map(p => (
            <button
              key={p}
              onClick={() => setForm({ ...form, priority: p })}
              className={`px-4 py-2 rounded-lg text-xs font-medium border transition-all ${
                form.priority === p ? 'border-gold text-gold bg-gold/10' : 'border-surface-200 text-gray-400'
              }`}
            >{p}</button>
          ))}
        </div>
      </div>
      <div>
        <label className="text-xs text-gray-400 mb-1 block">Observacoes para o MD</label>
        <textarea className="input-field h-20 resize-none" value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} placeholder="Instrucoes especiais, contexto do deal..." />
      </div>
    </div>
  )
}

function PendingPanel() {
  const { toast } = useApp()
  const [expanded, setExpanded] = useState(null)

  const byOp = OPERATIONS.map(op => ({
    ...op,
    pendencies: PENDING_ITEMS.filter(p => p.operation === op.id),
  }))

  const statusColors = { atrasado: 'text-accent-red', pendente: 'text-gold', em_andamento: 'text-accent-blue' }
  const statusLabels = { atrasado: 'Atrasado', pendente: 'Pendente', em_andamento: 'Em Andamento' }

  return (
    <div className="mt-8">
      <p className="section-title">Pendencias por Operacao</p>
      <div className="space-y-3">
        {byOp.map(op => {
          const atrasadas = op.pendencies.filter(p => p.status === 'atrasado').length
          return (
            <div key={op.id} className="card overflow-hidden">
              <div
                className="p-4 flex items-center justify-between cursor-pointer hover:bg-surface-100 transition-colors"
                onClick={() => setExpanded(expanded === op.id ? null : op.id)}
              >
                <div className="flex items-center gap-3">
                  <span className={`badge ${op.type === 'DCM' ? 'badge-blue' : 'badge-green'}`}>{op.type}</span>
                  <h4 className="text-sm font-medium text-white">{op.name}</h4>
                  <span className="text-xs text-gray-500">{op.pendencies.length} itens</span>
                  {atrasadas > 0 && <span className="badge-red flex items-center gap-1"><AlertTriangle size={10} />{atrasadas} atrasados</span>}
                </div>
                <ChevronDown size={16} className={`text-gray-500 transition-transform ${expanded === op.id ? 'rotate-180' : ''}`} />
              </div>
              {expanded === op.id && (
                <div className="border-t border-surface-200 px-4 pb-3">
                  {op.pendencies.map(p => (
                    <div key={p.id} className="flex items-center gap-3 py-2.5 border-b border-surface-200/50 last:border-0">
                      <div className="flex-1">
                        <p className="text-xs text-gray-200">{p.item}</p>
                        <p className="text-[10px] text-gray-500">Responsavel: {p.responsible === 'cliente' ? 'Cliente' : 'Equipe Interna'} · Prazo: {p.deadline}</p>
                      </div>
                      <span className={`text-[10px] font-medium ${statusColors[p.status]}`}>{statusLabels[p.status]}</span>
                      <button onClick={() => toast('Lembrete enviado', 'info')} className="btn-ghost p-1" title="Enviar lembrete"><Bell size={13} /></button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default function ProjectOpening() {
  const { toast } = useApp()
  const [step, setStep] = useState(0)
  const [form, setForm] = useState({
    company: '', cnpj: '', sector: '', opType: 'Debentures', value: '', deadline: '', rating: '', guarantee: '',
    agents: ['md_orchestrator'], priority: 'Alta', notes: '',
  })

  const submit = () => {
    toast('Projeto aberto com sucesso! Agentes acionados.', 'info')
    setStep(0)
    setForm({ company: '', cnpj: '', sector: '', opType: 'Debentures', value: '', deadline: '', rating: '', guarantee: '', agents: ['md_orchestrator'], priority: 'Alta', notes: '' })
  }

  return (
    <div>
      <h2 className="text-xl font-bold text-white font-editorial mb-1">Abertura de Projetos</h2>
      <p className="text-xs text-gray-500 mb-6">Configure e abra novas operacoes no pipeline</p>

      <div className="card p-6">
        <Stepper step={step} setStep={setStep} />
        {step === 0 && <StepIdentification form={form} setForm={setForm} />}
        {step === 1 && <StepChecklist form={form} />}
        {step === 2 && <StepAgents form={form} setForm={setForm} />}

        <div className="flex justify-between mt-6 pt-4 border-t border-surface-200">
          <button onClick={() => setStep(Math.max(0, step - 1))} className="btn-ghost" disabled={step === 0}>Anterior</button>
          {step < 2 ? (
            <button onClick={() => setStep(step + 1)} className="btn-primary">Proximo</button>
          ) : (
            <button onClick={submit} className="btn-primary">Abrir Projeto</button>
          )}
        </div>
      </div>

      <PendingPanel />
    </div>
  )
}
