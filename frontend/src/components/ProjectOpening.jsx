import { useState, useRef } from 'react'
import { useApp } from '../context/AppContext'
import { AGENTS, DOC_CHECKLIST } from '../data/mockData'
import { CheckCircle, Clock, XCircle, Upload, ChevronDown, AlertTriangle, FolderOpen, File, Plus } from 'lucide-react'

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

function StepChecklist({ form, uploadedDocs, setUploadedDocs }) {
  const { toast } = useApp()
  const [uploading, setUploading] = useState(null)
  const fileRefs = useRef({})

  const handleUpload = async (idx, file) => {
    const doc = DOC_CHECKLIST[idx]
    if (!file || !doc) return
    const currentFiles = uploadedDocs[idx]?.files || []
    if (currentFiles.length >= doc.maxFiles) return
    const company = form.company || 'empresa'
    setUploading(idx)
    try {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('company', company)
      const res = await fetch(`${API}/api/upload`, { method: 'POST', body: fd })
      const data = await res.json()
      if (data.ok) {
        setUploadedDocs(prev => ({
          ...prev,
          [idx]: { ...doc, files: [...(prev[idx]?.files || []), { name: data.file, size_kb: data.size_kb }] }
        }))
        toast(`${doc.label} — arquivo salvo`, 'success')
      }
    } catch {
      toast('Erro ao fazer upload', 'error')
    } finally {
      setUploading(null)
      if (fileRefs.current[idx]) fileRefs.current[idx].value = ''
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs text-gray-400">
          Ate <span className="text-gold">5 arquivos</span> por item · Pendentes nao bloqueiam o fluxo
        </p>
        {form.company && (
          <div className="flex items-center gap-1.5 text-[10px] text-gray-500 bg-surface-100 px-2.5 py-1 rounded-lg">
            <FolderOpen size={11} className="text-gold" />
            uploads/{form.company.toLowerCase().replace(/\s+/g, '_')}/
          </div>
        )}
      </div>
      {DOC_CHECKLIST.map((doc, idx) => {
        const files = uploadedDocs[idx]?.files || []
        const atLimit = files.length >= doc.maxFiles
        const hasFiles = files.length > 0
        return (
          <div key={doc.id} className="card-hover p-3">
            <div className="flex items-center gap-3">
              {hasFiles
                ? <CheckCircle size={18} className="text-accent-green flex-shrink-0" />
                : <Clock size={18} className={`flex-shrink-0 ${doc.required ? 'text-gold' : 'text-gray-500'}`} />
              }
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-200">{doc.label}</span>
                  {!doc.required && <span className="text-[9px] text-gray-500 bg-surface-200 px-1.5 py-0.5 rounded">Opcional</span>}
                  {doc.hint && doc.required && <span className="text-[9px] text-gray-500">{doc.hint}</span>}
                </div>
              </div>
              <span className="text-[10px] text-gray-500 font-medium">{files.length}/{doc.maxFiles}</span>
              <input
                type="file"
                ref={el => fileRefs.current[idx] = el}
                className="hidden"
                onChange={e => handleUpload(idx, e.target.files[0])}
              />
              <button
                className={`btn-ghost p-1 flex items-center gap-1 text-[10px] ${uploading === idx ? 'animate-pulse text-gold' : atLimit ? 'opacity-30 cursor-not-allowed' : ''}`}
                title={atLimit ? 'Limite de 5 arquivos atingido' : 'Adicionar arquivo'}
                onClick={() => !atLimit && fileRefs.current[idx]?.click()}
                disabled={uploading !== null || atLimit}
              >
                <Plus size={13} /><Upload size={13} />
              </button>
            </div>
            {hasFiles && (
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

const ECM_TYPES = ['IPO', 'Follow-on', 'Block Trade']

const OUTPUT_DOCS_MAP = {
  shared: [
    { id: 'research',  label: 'Research Report',        format: 'PDF' },
    { id: 'modelo',    label: 'Modelagem Financeira',    format: 'XLSX' },
  ],
  DCM: [
    { id: 'viab_dcm',    label: 'Relatorio de Viabilidade DCM', format: 'XLSX+PPTX' },
    { id: 'book_credito', label: 'Book de Credito',             format: 'PPTX' },
    { id: 'teaser_dcm',  label: 'Teaser',                       format: 'PPTX' },
  ],
  ECM: [
    { id: 'viab_ecm', label: 'Relatorio de Viabilidade ECM', format: 'XLSX+PPTX' },
    { id: 'cim',      label: 'CIM',                           format: 'PPTX' },
    { id: 'teaser_ecm', label: 'Teaser',                      format: 'PPTX' },
  ],
}

function StepAgents({ form, setForm }) {
  const isECM = ECM_TYPES.includes(form.opType)
  const docList = [...OUTPUT_DOCS_MAP.shared, ...(isECM ? OUTPUT_DOCS_MAP.ECM : OUTPUT_DOCS_MAP.DCM)]

  // Default: all docs selected if not yet set for this opType
  const defaultSelected = docList.map(d => d.id)
  const selectedDocs = form.selectedDocs?.length > 0 ? form.selectedDocs : defaultSelected

  const toggleDoc = (id) => {
    const next = selectedDocs.includes(id) ? selectedDocs.filter(x => x !== id) : [...selectedDocs, id]
    setForm({ ...form, selectedDocs: next })
  }

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
        <label className="text-xs text-gray-400 mb-2 block">
          Documentos a Produzir
          <span className="ml-2 text-[10px] text-gray-600 normal-case">Pre-selecionados para {isECM ? 'ECM' : 'DCM'} — desmarque os que nao deseja</span>
        </label>
        <div className="space-y-1.5">
          {docList.map(doc => {
            const checked = selectedDocs.includes(doc.id)
            return (
              <label key={doc.id} className={`flex items-center gap-3 p-2.5 rounded-lg border cursor-pointer transition-all ${checked ? 'border-gold/30 bg-gold/5' : 'border-surface-200 opacity-50'}`}>
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => toggleDoc(doc.id)}
                  className="accent-yellow-500"
                />
                <span className="text-xs text-gray-200 flex-1">{doc.label}</span>
                <span className="text-[10px] text-gray-500 font-mono">{doc.format}</span>
              </label>
            )
          })}
        </div>
      </div>

      <div>
        <label className="text-xs text-gray-400 mb-1 block">Solicitacao Adicional ao Sistema</label>
        <textarea
          className="input-field h-16 resize-none"
          value={form.additionalRequest || ''}
          onChange={e => setForm({ ...form, additionalRequest: e.target.value })}
          placeholder="Ex: incluir analise de sensibilidade de taxa, comparativo com peers setoriais..."
        />
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
  const { state } = useApp()
  const [expanded, setExpanded] = useState(null)
  const userOps = state.operations.filter(op => op.pendingDocs)

  if (userOps.length === 0) return null

  return (
    <div className="mt-8">
      <p className="section-title">Documentos Pendentes por Projeto</p>
      <div className="space-y-3">
        {userOps.map(op => (
          <div key={op.id} className="card overflow-hidden">
            <div
              className="p-4 flex items-center justify-between cursor-pointer hover:bg-surface-100 transition-colors"
              onClick={() => setExpanded(expanded === op.id ? null : op.id)}
            >
              <div className="flex items-center gap-3">
                <span className={`badge ${op.type === 'DCM' ? 'badge-blue' : 'badge-green'}`}>{op.type}</span>
                <h4 className="text-sm font-medium text-white">{op.name}</h4>
                {op.pendingDocs.length > 0
                  ? <span className="flex items-center gap-1 text-[10px] text-gold"><AlertTriangle size={10} />{op.pendingDocs.length} pendentes</span>
                  : <span className="text-[10px] text-accent-green">Documentacao completa</span>
                }
              </div>
              <ChevronDown size={16} className={`text-gray-500 transition-transform ${expanded === op.id ? 'rotate-180' : ''}`} />
            </div>
            {expanded === op.id && (
              <div className="border-t border-surface-200 px-4 pb-3">
                {op.pendingDocs.length === 0
                  ? <p className="text-xs text-gray-500 py-3">Todos os documentos foram recebidos.</p>
                  : op.pendingDocs.map((doc, i) => (
                    <div key={i} className="flex items-center gap-3 py-2.5 border-b border-surface-200/50 last:border-0">
                      <Clock size={13} className="text-gold flex-shrink-0" />
                      <p className="text-xs text-gray-200 flex-1">{doc}</p>
                      <span className="text-[10px] text-gold">Aguardando envio</span>
                    </div>
                  ))
                }
                {op.notes && (
                  <div className="mt-2 p-2 bg-surface-100 rounded text-[11px] text-gray-400">
                    <span className="text-gray-500">Observacoes: </span>{op.notes}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

const EMPTY_FORM = { company: '', cnpj: '', sector: '', opType: 'Debentures', value: '', deadline: '', rating: '', guarantee: '', agents: ['md_orchestrator'], priority: 'Alta', notes: '', selectedDocs: [], additionalRequest: '' }

export default function ProjectOpening() {
  const { dispatch, toast } = useApp()
  const [step, setStep] = useState(0)
  const [form, setForm] = useState({ ...EMPTY_FORM })
  const [uploadedDocs, setUploadedDocs] = useState({})

  const submit = () => {
    if (!form.company.trim()) { toast('Informe o nome da empresa', 'error'); return }
    const docs = DOC_CHECKLIST.map((doc, idx) => ({ ...doc, files: uploadedDocs[idx]?.files || [] }))
    dispatch({ type: 'OPEN_PROJECT', payload: { form, docs } })
    toast(`Projeto ${form.company} aberto! Agentes acionados.`, 'info')
    setStep(0)
    setForm({ ...EMPTY_FORM })
    setUploadedDocs({})
  }

  return (
    <div>
      <h2 className="text-xl font-bold text-white font-editorial mb-1">Abertura de Projetos</h2>
      <p className="text-xs text-gray-500 mb-6">Configure e abra novas operacoes no pipeline</p>

      <div className="card p-6">
        <Stepper step={step} setStep={setStep} />
        {step === 0 && <StepIdentification form={form} setForm={setForm} />}
        {step === 1 && <StepChecklist form={form} uploadedDocs={uploadedDocs} setUploadedDocs={setUploadedDocs} />}
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
