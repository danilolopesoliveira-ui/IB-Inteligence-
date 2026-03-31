import { useState, useRef } from 'react'
import { useApp } from '../context/AppContext'
import { AGENTS, DOC_CHECKLIST } from '../data/mockData'
import { CheckCircle, Clock, XCircle, Upload, ChevronDown, AlertTriangle, FolderOpen, File, Plus, Ban } from 'lucide-react'

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
      <div className="grid grid-cols-2 gap-4">
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
      </div>
      <div>
        <label className="text-xs text-gray-400 mb-2 block">Garantias <span className="text-gray-600">(selecao multipla)</span></label>
        <div className="flex flex-wrap gap-1.5">
          {[
            'Quirografaria (sem garantia)',
            'Real — Imoveis',
            'Real — Recebiveis',
            'Real — Equipamentos',
            'Fidejussoria — Aval/Fianca',
            'Fidejussoria — Fianca Bancaria',
            'Cessao Fiduciaria de Recebiveis',
            'Alienacao Fiduciaria de Imovel',
            'Alienacao Fiduciaria de Acoes',
            'Penhor de Acoes',
            'Fundo de Reserva',
            'Subordinacao Estrutural',
            'Garantia Corporativa (Holding)',
          ].map(g => {
            const selected = (form.guarantees || []).includes(g)
            return (
              <button
                key={g}
                type="button"
                onClick={() => {
                  const cur = form.guarantees || []
                  setForm({ ...form, guarantees: selected ? cur.filter(x => x !== g) : [...cur, g] })
                }}
                className={`px-2.5 py-1 rounded-lg text-[11px] border transition-all ${selected ? 'border-gold text-gold bg-gold/10' : 'border-surface-200 text-gray-400 hover:text-gray-200'}`}
              >{g}</button>
            )
          })}
        </div>
      </div>
    </div>
  )
}

function StepChecklist({ form, uploadedDocs, setUploadedDocs, disabledDocs, setDisabledDocs }) {
  const { toast } = useApp()
  const [uploading, setUploading] = useState(null)
  const fileRefs = useRef({})

  const toggleDisabled = (idx) => {
    setDisabledDocs(prev => prev.includes(idx) ? prev.filter(i => i !== idx) : [...prev, idx])
  }

  const handleUpload = async (idx, file) => {
    const doc = DOC_CHECKLIST[idx]
    if (!file || !doc) return
    const currentFiles = uploadedDocs[idx]?.files || []
    if (currentFiles.length >= doc.maxFiles) {
      toast(`Limite de ${doc.maxFiles} arquivos atingido`, 'error')
      return
    }
    if (!form.company.trim()) {
      toast('Preencha o nome da empresa antes de fazer upload', 'error')
      return
    }
    const company = form.company.trim()
    setUploading(idx)
    try {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('company', company)
      const res = await fetch(`${API}/api/upload`, { method: 'POST', body: fd })
      if (!res.ok) {
        const err = await res.text()
        throw new Error(`Servidor retornou ${res.status}: ${err}`)
      }
      const data = await res.json()
      if (data.ok) {
        setUploadedDocs(prev => ({
          ...prev,
          [idx]: { ...doc, files: [...(prev[idx]?.files || []), { name: data.file, size_kb: data.size_kb }] }
        }))
        toast(`${doc.label} — arquivo salvo`, 'success')
      } else {
        toast(`Erro ao salvar arquivo: ${data.error || 'resposta inesperada'}`, 'error')
      }
    } catch (err) {
      toast(`Erro no upload: ${err.message}`, 'error')
    } finally {
      setUploading(null)
      if (fileRefs.current[idx]) fileRefs.current[idx].value = ''
    }
  }

  return (
    <div className="space-y-2">
      {!form.company.trim() && (
        <div className="flex items-center gap-2 px-3 py-2 mb-3 rounded-lg border border-amber-400/30 bg-amber-400/5">
          <AlertTriangle size={13} className="text-amber-400 flex-shrink-0" />
          <p className="text-xs text-amber-300">Volte ao passo 1 e informe o nome da empresa antes de fazer upload.</p>
        </div>
      )}
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs text-gray-400">
          Ate <span className="text-gold">5 arquivos</span> por item · Clique na linha ou em "Anexar" · Pendentes nao bloqueiam o fluxo
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
        const isDisabled = disabledDocs.includes(idx)
        return (
          <div
            key={doc.id}
            className={`card p-3 transition-colors ${isDisabled ? 'opacity-40 border-dashed' : (!atLimit && uploading === null ? 'hover:border-gold/30 cursor-pointer' : '')}`}
            onClick={() => !isDisabled && !atLimit && uploading === null && fileRefs.current[idx]?.click()}
          >
            <div className="flex items-center gap-3">
              {isDisabled
                ? <Ban size={18} className="text-gray-600 flex-shrink-0" />
                : uploading === idx
                  ? <Upload size={18} className="text-gold animate-bounce flex-shrink-0" />
                  : hasFiles
                    ? <CheckCircle size={18} className="text-accent-green flex-shrink-0" />
                    : <Clock size={18} className={`flex-shrink-0 ${doc.required ? 'text-gold' : 'text-gray-500'}`} />
              }
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={`text-sm ${isDisabled ? 'line-through text-gray-500' : 'text-gray-200'}`}>{doc.label}</span>
                  {!doc.required && !isDisabled && <span className="text-[9px] text-gray-500 bg-surface-200 px-1.5 py-0.5 rounded">Opcional</span>}
                  {isDisabled && <span className="text-[9px] text-gray-500 bg-surface-200 px-1.5 py-0.5 rounded">Não aplicável</span>}
                </div>
                {!isDisabled && !atLimit && uploading !== idx && (
                  <p className="text-[10px] text-gray-500 mt-0.5">Clique para selecionar arquivo</p>
                )}
              </div>
              {!isDisabled && <span className="text-[10px] text-gray-500 font-medium">{files.length}/{doc.maxFiles}</span>}
              <input
                type="file"
                ref={el => fileRefs.current[idx] = el}
                className="hidden"
                accept=".pdf,.xlsx,.xls,.docx,.doc,.png,.jpg,.jpeg"
                onChange={e => { e.stopPropagation(); handleUpload(idx, e.target.files[0]) }}
              />
              {!isDisabled && (
                <button
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] border transition-colors flex-shrink-0 ${
                    uploading === idx ? 'border-gold/40 text-gold animate-pulse' :
                    atLimit ? 'border-surface-200 text-gray-600 cursor-not-allowed opacity-40' :
                    'border-gold/40 text-gold hover:bg-gold/10'
                  }`}
                  title={atLimit ? `Limite de ${doc.maxFiles} arquivos atingido` : 'Enviar arquivo'}
                  onClick={e => { e.stopPropagation(); !atLimit && uploading === null && fileRefs.current[idx]?.click() }}
                  disabled={uploading !== null || atLimit}
                >
                  {uploading === idx ? <><Upload size={11} /> Enviando...</> : <><Plus size={11} /> Anexar</>}
                </button>
              )}
              <button
                onClick={e => { e.stopPropagation(); toggleDisabled(idx) }}
                title={isDisabled ? 'Reativar documento' : 'Marcar como não aplicável'}
                className={`p-1.5 rounded transition-colors flex-shrink-0 ${isDisabled ? 'text-accent-green hover:bg-accent-green/10' : 'text-gray-600 hover:text-accent-red hover:bg-accent-red/10'}`}
              >
                {isDisabled ? <CheckCircle size={14} /> : <XCircle size={14} />}
              </button>
            </div>
            {hasFiles && !isDisabled && (
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

const EMPTY_FORM = { company: '', cnpj: '', sector: '', opType: 'Debentures', value: '', deadline: '', rating: '', guarantees: [], agents: ['md_orchestrator'], priority: 'Alta', notes: '', selectedDocs: [], additionalRequest: '' }

export default function ProjectOpening() {
  const { dispatch, toast, state } = useApp()
  const [step, setStep] = useState(0)
  const [form, setForm] = useState({ ...EMPTY_FORM })
  const [uploadedDocs, setUploadedDocs] = useState({})
  const [disabledDocs, setDisabledDocs] = useState([])

  const submit = async () => {
    if (!form.company.trim()) { toast('Informe o nome da empresa', 'error'); return }
    const opId = `op_${Date.now()}`
    const capturedForm = { ...form }
    const docs = DOC_CHECKLIST.map((doc, idx) => ({ ...doc, files: uploadedDocs[idx]?.files || [], disabled: disabledDocs.includes(idx) }))
    dispatch({ type: 'OPEN_PROJECT', payload: { form: capturedForm, docs, opId } })
    toast(`Projeto ${capturedForm.company} aberto! Etapa 1 em execucao...`, 'info')
    setStep(0)
    setForm({ ...EMPTY_FORM })
    setUploadedDocs({})
    setDisabledDocs([])

    // Fetch file context uploaded for this company
    let fileContext = ''
    try {
      const r = await fetch(`${API}/api/files-context/${encodeURIComponent(capturedForm.company)}`)
      const d = await r.json()
      fileContext = d.context || ''
    } catch {}

    const ecmTypes = ['IPO', 'Follow-on', 'Block Trade']
    const operation = {
      id: opId,
      name: `${capturedForm.company} — ${capturedForm.opType}`,
      type: ecmTypes.includes(capturedForm.opType) ? 'ECM' : 'DCM',
      company: capturedForm.company,
      sector: capturedForm.sector,
      value: capturedForm.value,
      rating: capturedForm.rating,
      guarantees: capturedForm.guarantees,
      deadline: capturedForm.deadline,
    }

    const etapa1 = [
      { agentId: 'accountant',    taskId: `${opId}_accountant`, title: `Etapa 1 — Revisao de DFs: ${capturedForm.company}` },
      { agentId: 'legal_advisor', taskId: `${opId}_legal`,      title: `Etapa 1 — Due Diligence Juridica: ${capturedForm.company}` },
    ]

    for (const task of etapa1) {
      try {
        const agentConfig = state.agents.find(a => a.id === task.agentId)
        const r = await fetch(`${API}/api/run-agent-task`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            agent_id: task.agentId,
            operation,
            file_context: fileContext,
            task_title: task.title,
            additional_context: capturedForm.additionalRequest,
            custom_prompt: agentConfig?.promptBase || '',
          }),
        })
        const data = await r.json()
        if (data.text) {
          const now = new Date().toISOString()
          dispatch({ type: 'APPEND_TASK_LOG', payload: {
            taskId: task.taskId,
            column: 'Em Revisao',
            entries: [
              { time: now, agent: task.agentId, type: 'start', text: `Executando: ${task.title}` },
              { time: now, agent: task.agentId, type: 'progress', text: data.text },
            ],
          }})
          dispatch({ type: 'ADD_AGENT_RESPONSE', payload: {
            threadId: `msg_${opId}`,
            agentId: task.agentId,
            text: data.text,
          }})
          // Registra documento gerado em Documentos Gerados da operação
          const docNames = {
            accountant:   'Análise Contábil e Ajustes (IFRS 16)',
            legal_advisor:'Due Diligence Jurídica',
          }
          dispatch({ type: 'ADD_AGENT_DOC', payload: {
            opId,
            doc: {
              name: docNames[task.agentId] || task.title,
              agent: task.agentId,
              status: 'em_revisao',
              version: 'v1.0',
              date: new Date().toLocaleDateString('pt-BR'),
            }
          }})
        }
      } catch (err) {
        console.error(`[${task.agentId}] Erro na execucao automatica:`, err)
      }
    }
    dispatch({ type: 'SET_THREAD_APPROVAL', payload: {
      threadId: `msg_${opId}`,
      awaitingApproval: true,
      approvalTaskIds: etapa1.map(t => t.taskId),
    }})
    toast('Etapa 1 concluida — aguardando sua aprovacao em Revisoes & Comunicacao', 'success')
  }

  return (
    <div>
      <h2 className="text-xl font-bold text-white font-editorial mb-1">Abertura de Projetos</h2>
      <p className="text-xs text-gray-500 mb-6">Configure e abra novas operacoes no pipeline</p>

      <div className="card p-6">
        <Stepper step={step} setStep={setStep} />
        {step === 0 && <StepIdentification form={form} setForm={setForm} />}
        {step === 1 && <StepChecklist form={form} uploadedDocs={uploadedDocs} setUploadedDocs={setUploadedDocs} disabledDocs={disabledDocs} setDisabledDocs={setDisabledDocs} />}
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
