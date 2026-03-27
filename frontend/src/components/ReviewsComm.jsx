import { useState, useRef, useEffect, useMemo } from 'react'
import { useApp } from '../context/AppContext'
import { AGENTS } from '../data/mockData'
import { Send, MessageCircle, AlertTriangle, RotateCcw, CheckCircle, Search, Plus, X, Loader, Paperclip, CornerDownLeft } from 'lucide-react'

// ── Markdown-lite renderer ──────────────────────────────────────────────────
function FormattedMessage({ text }) {
  const rendered = useMemo(() => {
    if (!text) return null
    const lines = text.split('\n')
    const elements = []
    let i = 0

    while (i < lines.length) {
      const line = lines[i]

      // Empty line → spacer
      if (line.trim() === '') {
        elements.push(<div key={i} className="h-2" />)
        i++
        continue
      }

      // Numbered list (1. 2. 3.)
      if (/^\d+\.\s/.test(line.trim())) {
        const items = []
        while (i < lines.length && /^\d+\.\s/.test(lines[i].trim())) {
          items.push(lines[i].trim().replace(/^\d+\.\s/, ''))
          i++
        }
        elements.push(
          <ol key={`ol-${i}`} className="list-decimal list-outside ml-4 space-y-1 my-1.5">
            {items.map((item, j) => <li key={j}><BoldText text={item} /></li>)}
          </ol>
        )
        continue
      }

      // Bullet list (- item)
      if (/^[-•]\s/.test(line.trim())) {
        const items = []
        while (i < lines.length && /^[-•]\s/.test(lines[i].trim())) {
          items.push(lines[i].trim().replace(/^[-•]\s/, ''))
          i++
        }
        elements.push(
          <ul key={`ul-${i}`} className="list-disc list-outside ml-4 space-y-1 my-1.5">
            {items.map((item, j) => <li key={j}><BoldText text={item} /></li>)}
          </ul>
        )
        continue
      }

      // Regular paragraph
      elements.push(<p key={i} className="my-1"><BoldText text={line} /></p>)
      i++
    }

    return elements
  }, [text])

  return <div className="formatted-msg">{rendered}</div>
}

// Inline bold (**text**) renderer
function BoldText({ text }) {
  if (!text) return null
  const parts = text.split(/(\*\*[^*]+\*\*)/)
  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return <strong key={i} className="font-semibold text-white">{part.slice(2, -2)}</strong>
        }
        return <span key={i}>{part}</span>
      })}
    </>
  )
}

const API = import.meta.env.VITE_API_URL || ''

const TYPE_ICONS = {
  duvida: { icon: MessageCircle, label: 'Duvida', cls: 'text-accent-blue' },
  revisao: { icon: RotateCcw, label: 'Revisao', cls: 'text-gold' },
  alerta: { icon: AlertTriangle, label: 'Alerta', cls: 'text-accent-red' },
  resposta: { icon: CheckCircle, label: 'Resposta', cls: 'text-accent-green' },
}

const AGENT_DOC_NAMES = {
  accountant:        'Análise Contábil e Ajustes (IFRS 16)',
  legal_advisor:     'Due Diligence Jurídica',
  research_analyst:  'Dossiê Analítico (Research Report)',
  financial_modeler: 'Modelo Financeiro e Projeções',
  dcm_specialist:    'Relatório de Viabilidade DCM',
  ecm_specialist:    'Relatório de Viabilidade ECM',
  risk_compliance:   'Relatório de Risco e Compliance',
  deck_builder:      'Book de Crédito / CIM e Teaser',
}

// Pipeline advancement logic — mirrors the project pipeline stages
const PIPELINE_NEXT = {
  accountant: { nexts: ['research'],           requires: ['accountant', 'legal'] },
  legal:      { nexts: ['research'],           requires: ['accountant', 'legal'] },
  research:   { nexts: ['modeling'],           requires: ['research'] },
  modeling:   { nexts: ['specialist', 'risk'], requires: ['modeling'] },
  specialist: { nexts: ['deck'],               requires: ['specialist', 'risk'] },
  risk:       { nexts: ['deck'],               requires: ['specialist', 'risk'] },
  deck:       { nexts: [],                     requires: [] },
}

function getTaskSuffix(taskId) {
  const parts = taskId.split('_')
  return parts[parts.length - 1]
}

function Thread({ thread }) {
  const { state: appState, dispatch, toast } = useApp()
  const [reply, setReply] = useState('')
  const [loading, setLoading] = useState(false)
  const [approving, setApproving] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [reviewMode, setReviewMode] = useState(false)
  const [reviewFeedback, setReviewFeedback] = useState('')
  const [reviewing, setReviewing] = useState(false)
  const fileInputRef = useRef(null)
  const messagesEndRef = useRef(null)

  const agent = AGENTS.find(a => a.id === thread.agent)
  const op = appState.operations.find(o => o.id === thread.operation)

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  useEffect(scrollToBottom, [thread.messages.length])

  const send = async () => {
    if (!reply.trim() || loading) return
    const text = reply
    dispatch({ type: 'SEND_MESSAGE', payload: { threadId: thread.id, text } })
    setReply('')
    setLoading(true)
    try {
      const allMsgs = [
        ...thread.messages.map(m => ({
          role: m.from === 'user' ? 'user' : 'assistant',
          content: m.text,
        })),
        { role: 'user', content: text },
      ]
      // Anthropic exige que a primeira mensagem seja 'user' e que content nao seja vazio
      const filtered = allMsgs.filter(m => m.content && m.content.trim())
      const firstUser = filtered.findIndex(m => m.role === 'user')
      const history = firstUser >= 0 ? filtered.slice(firstUser) : filtered

      let fileContext = ''
      if (op?.company) {
        try {
          const r = await fetch(`${API}/api/files-context/${encodeURIComponent(op.company)}`)
          const d = await r.json()
          if (d.context) fileContext = `\n\nDOCUMENTOS DISPONIVEIS PARA ANALISE — ${op.company}:\n${d.context.slice(0, 5000)}`
        } catch {}
      }

      const res = await fetch(`${API}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: history,
          system_prompt: agent?.promptBase ? agent.promptBase + fileContext : undefined,
          operations_context: op ? `\n\nOperacao: ${op.name} | Tipo: ${op.type} | Instrumento: ${op.instrument} | Etapa: ${op.stage || 'Etapa 1'}${op.pendingDocs?.length > 0 ? ` | Docs pendentes: ${op.pendingDocs.join(', ')}` : ''}` : '',
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`)
      if (!data.text) throw new Error('Resposta vazia do servidor')
      dispatch({ type: 'ADD_AGENT_RESPONSE', payload: { threadId: thread.id, agentId: thread.agent, text: data.text } })
    } catch (err) {
      console.error('[Thread] Erro:', err)
      toast(`Erro: ${err.message}`, 'error')
      dispatch({ type: 'ADD_AGENT_RESPONSE', payload: {
        threadId: thread.id,
        agentId: thread.agent,
        text: `[Erro de conexao: ${err.message}]`,
      }})
    } finally {
      setLoading(false)
    }
  }

  const approveStage = async () => {
    setApproving(true)
    try {
      const now = new Date().toISOString()
      const taskIds = thread.approvalTaskIds || []
      if (taskIds.length === 0) return

      const opId = thread.operation
      const opTasks = appState.tasks.filter(t => t.operation === opId)

      // Mark all awaiting tasks as Concluido
      for (const taskId of taskIds) {
        const task = appState.tasks.find(t => t.id === taskId)
        dispatch({ type: 'APPEND_TASK_LOG', payload: {
          taskId,
          column: 'Concluido',
          entries: [{ time: now, agent: 'md_orchestrator', type: 'approve', text: `Aprovado pelo usuario: ${task?.title || taskId}` }],
        }})
      }

      // Clear approval state immediately
      dispatch({ type: 'SET_THREAD_APPROVAL', payload: {
        threadId: thread.id,
        awaitingApproval: false,
        approvalTaskIds: [],
      }})
      toast('Etapa aprovada!', 'success')

      // Fetch file context once
      let fileContext = ''
      if (op?.company) {
        try {
          const r = await fetch(`${API}/api/files-context/${encodeURIComponent(op.company)}`)
          const d = await r.json()
          fileContext = d.context || ''
        } catch {}
      }

      // Determine next tasks — deduplicate by suffix
      const startedSuffixes = new Set()
      const newTaskIds = []

      for (const taskId of taskIds) {
        const suffix = getTaskSuffix(taskId)
        const pipelineInfo = PIPELINE_NEXT[suffix]
        if (!pipelineInfo || pipelineInfo.nexts.length === 0) continue

        for (const nextSuffix of pipelineInfo.nexts) {
          if (startedSuffixes.has(nextSuffix)) continue
          startedSuffixes.add(nextSuffix)

          const nextTask = opTasks.find(t => getTaskSuffix(t.id) === nextSuffix)
          if (!nextTask || nextTask.column !== 'Backlog') continue

          try {
            const agentConfig = appState.agents.find(a => a.id === nextTask.agent)
            const r = await fetch(`${API}/api/run-agent-task`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                agent_id: nextTask.agent,
                operation: op || { id: opId },
                file_context: fileContext,
                task_title: nextTask.title,
                custom_prompt: agentConfig?.promptBase || '',
              }),
            })
            const data = await r.json()
            if (data.text) {
              const t2 = new Date().toISOString()
              dispatch({ type: 'APPEND_TASK_LOG', payload: {
                taskId: nextTask.id,
                column: 'Em Revisao',
                entries: [
                  { time: t2, agent: nextTask.agent, type: 'start', text: `Iniciado apos aprovacao: ${nextTask.title}` },
                  { time: t2, agent: nextTask.agent, type: 'progress', text: data.text },
                ],
              }})
              dispatch({ type: 'ADD_AGENT_RESPONSE', payload: {
                threadId: thread.id,
                agentId: nextTask.agent,
                text: data.text,
              }})
              // Registra documento gerado em Documentos Gerados da operação
              dispatch({ type: 'ADD_AGENT_DOC', payload: {
                opId: opId,
                doc: {
                  name: AGENT_DOC_NAMES[nextTask.agent] || nextTask.title,
                  agent: nextTask.agent,
                  status: 'em_revisao',
                  version: 'v1.0',
                  date: new Date().toLocaleDateString('pt-BR'),
                }
              }})
              newTaskIds.push(nextTask.id)
            }
          } catch (err) {
            console.error(`[${nextTask.agent}] Erro:`, err)
            toast(`Erro ao executar ${nextSuffix}: ${err.message}`, 'error')
          }
        }
      }

      if (newTaskIds.length > 0) {
        dispatch({ type: 'SET_THREAD_APPROVAL', payload: {
          threadId: thread.id,
          awaitingApproval: true,
          approvalTaskIds: newTaskIds,
        }})
        toast('Proxima etapa acionada — aguardando aprovacao!', 'success')
      } else {
        toast('Pipeline concluido!', 'success')
      }
    } catch (err) {
      toast(`Erro: ${err.message}`, 'error')
    } finally {
      setApproving(false)
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('company', op?.company || 'geral')
      const res = await fetch(`${API}/api/upload`, { method: 'POST', body: formData })
      const data = await res.json()
      if (!data.ok) throw new Error('Falha no upload')
      const text = `[Documento enviado: ${data.file} (${Math.round(data.size_kb)}KB)]`
      dispatch({ type: 'SEND_MESSAGE', payload: { threadId: thread.id, text } })
      toast(`Arquivo "${data.file}" enviado`, 'success')
    } catch (err) {
      toast(`Erro no upload: ${err.message}`, 'error')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  const requestRevision = async () => {
    if (!reviewFeedback.trim() || reviewing) return
    const feedback = reviewFeedback.trim()
    setReviewing(true)

    // Log user feedback as a message in the thread
    dispatch({ type: 'SEND_MESSAGE', payload: { threadId: thread.id, text: `[Solicitacao de revisao]: ${feedback}` } })

    // Move tasks back to "Devolvido p/ Ajuste"
    const taskIds = thread.approvalTaskIds || []
    const now = new Date().toISOString()
    for (const taskId of taskIds) {
      dispatch({ type: 'APPEND_TASK_LOG', payload: {
        taskId,
        column: 'Devolvido p/ Ajuste',
        entries: [{ time: now, agent: 'md_orchestrator', type: 'review', text: `Devolvido pelo MD para ajuste: ${feedback}` }],
      }})
    }

    try {
      // Fetch file context
      let fileContext = ''
      if (op?.company) {
        try {
          const r = await fetch(`${API}/api/files-context/${encodeURIComponent(op.company)}`)
          const d = await r.json()
          fileContext = d.context || ''
        } catch {}
      }

      // Reprocess each task with the MD feedback
      for (const taskId of taskIds) {
        const task = appState.tasks.find(t => t.id === taskId)
        if (!task) continue
        const agentConfig = appState.agents.find(a => a.id === task.agent)

        try {
          const r = await fetch(`${API}/api/run-agent-task`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              agent_id: task.agent,
              operation: op || { id: thread.operation },
              file_context: fileContext,
              task_title: task.title,
              custom_prompt: agentConfig?.promptBase || '',
              additional_context: `FEEDBACK DO MD PARA REVISAO — O MD devolveu esta etapa com os seguintes ajustes solicitados:\n${feedback}\n\nReprocesse sua analise incorporando este feedback. Mantenha o que estava correto e ajuste os pontos sinalizados.`,
            }),
          })
          const data = await r.json()
          if (data.text) {
            const t2 = new Date().toISOString()
            dispatch({ type: 'APPEND_TASK_LOG', payload: {
              taskId,
              column: 'Em Revisao',
              entries: [
                { time: t2, agent: task.agent, type: 'review', text: `Reprocessado apos feedback do MD` },
                { time: t2, agent: task.agent, type: 'progress', text: data.text },
              ],
            }})
            dispatch({ type: 'ADD_AGENT_RESPONSE', payload: {
              threadId: thread.id,
              agentId: task.agent,
              text: data.text,
            }})
          }
        } catch (err) {
          console.error(`[${task.agent}] Erro no reprocessamento:`, err)
          toast(`Erro ao reprocessar ${task.agent}: ${err.message}`, 'error')
        }
      }

      // Keep approval state active for the MD to approve the new output
      toast('Revisao solicitada — agente reprocessando com seu feedback', 'info')
    } catch (err) {
      toast(`Erro: ${err.message}`, 'error')
    } finally {
      setReviewing(false)
      setReviewMode(false)
      setReviewFeedback('')
    }
  }

  const urgencyColors = { alta: 'badge-red', media: 'badge-gold', baixa: 'badge-green' }

  return (
    <div className="flex flex-col h-full">
      {/* Thread header */}
      <div className="pb-4 mb-4 border-b border-surface-200">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-6 h-6 rounded-full flex items-center justify-center text-[9px] font-bold text-white" style={{ background: agent?.color }}>{agent?.avatar}</div>
          <span className="text-sm font-bold text-white">{agent?.name}</span>
          <span className={`badge ${urgencyColors[thread.urgency]}`}>{thread.urgency}</span>
          {op && <span className={`badge ${op.type === 'DCM' ? 'badge-blue' : 'badge-green'}`}>{op.instrument}</span>}
        </div>
        <p className="text-xs text-gray-300">{thread.subject}</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-1">
        {thread.messages.map((msg, i) => {
          const isUser = msg.from === 'user'
          const msgAgent = AGENTS.find(a => a.id === msg.from)
          const typeInfo = TYPE_ICONS[msg.type] || TYPE_ICONS.duvida
          const TypeIcon = typeInfo.icon

          return (
            <div key={i} className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
              <div className={`w-7 h-7 rounded-full flex items-center justify-center text-[9px] font-bold text-white flex-shrink-0 ${isUser ? 'bg-gold' : ''}`}
                style={!isUser ? { background: msgAgent?.color } : undefined}
              >
                {isUser ? 'MD' : msgAgent?.avatar || '?'}
              </div>
              <div className={`max-w-[70%] ${isUser ? 'text-right' : ''}`}>
                <div className={`rounded-xl px-3.5 py-2.5 text-xs leading-relaxed ${
                  isUser ? 'bg-gold/15 text-gold-light' : 'bg-surface-100 text-gray-300'
                }`}>
                  {!isUser && <TypeIcon size={12} className={`${typeInfo.cls} inline mr-1.5 -mt-0.5`} />}
                  {isUser ? msg.text : <FormattedMessage text={msg.text} />}
                </div>
                <p className="text-[10px] text-gray-600 mt-1">
                  {new Date(msg.time).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          )
        })}
        <div ref={messagesEndRef} />
      </div>

      {/* Typing indicator */}
      {loading && (
        <div className="flex gap-3 mb-2">
          <div className="w-7 h-7 rounded-full flex items-center justify-center text-[9px] font-bold text-white flex-shrink-0" style={{ background: agent?.color }}>{agent?.avatar}</div>
          <div className="bg-surface-100 rounded-xl px-3.5 py-2.5 text-xs text-gray-400 flex items-center gap-1">
            <span className="animate-pulse">●</span><span className="animate-pulse" style={{animationDelay:'0.2s'}}>●</span><span className="animate-pulse" style={{animationDelay:'0.4s'}}>●</span>
          </div>
        </div>
      )}
      {/* Approval / Review banner */}
      {thread.awaitingApproval && (
        op?.paused ? (
          <div className="flex items-center gap-2 px-4 py-3 mb-3 rounded-lg border border-amber-400/30 bg-amber-400/5">
            <span className="text-[11px] text-amber-300">Operacao pausada — aprovacao suspensa. Reative a operacao em Operacoes para continuar o pipeline.</span>
          </div>
        ) : (
          <div className="mb-3 rounded-lg border border-surface-200 bg-surface-50 overflow-hidden">
            {/* Action buttons row */}
            <div className="flex items-center justify-between gap-3 px-4 py-3">
              <div className="flex-1">
                <p className="text-xs font-semibold text-white">Etapa concluida — revise o output e decida</p>
                <p className="text-[11px] text-gray-400 mt-0.5">{thread.approvalTaskIds?.length || 0} tarefa(s) aguardando sua decisao</p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setReviewMode(!reviewMode)}
                  disabled={approving || reviewing}
                  className="btn-ghost flex items-center gap-1.5 px-3 py-1.5 border border-amber-400/40 text-amber-400 hover:bg-amber-400/10 text-xs whitespace-nowrap"
                >
                  <CornerDownLeft size={13} />
                  Solicitar Revisao
                </button>
                <button
                  onClick={approveStage}
                  disabled={approving || reviewing}
                  className="btn-ghost flex items-center gap-1.5 px-3 py-1.5 border border-accent-green text-accent-green hover:bg-accent-green/20 text-xs whitespace-nowrap"
                >
                  {approving ? <Loader size={13} className="animate-spin" /> : <CheckCircle size={13} />}
                  {approving ? 'Aprovando...' : 'Aprovar e Avancar'}
                </button>
              </div>
            </div>

            {/* Review feedback panel (expandable) */}
            {reviewMode && (
              <div className="px-4 pb-3 border-t border-surface-200 pt-3">
                <p className="text-[11px] text-gray-400 mb-2">Descreva os ajustes necessarios — o agente reprocessara com seu feedback:</p>
                <textarea
                  className="input-field text-xs h-20 resize-none mb-2"
                  placeholder="Ex: O EBITDA normalizado deve considerar o ajuste de IFRS 16. Revisar a premissa de capital de giro — ciclo de 87 dias parece subestimado dado o historico..."
                  value={reviewFeedback}
                  onChange={e => setReviewFeedback(e.target.value)}
                  disabled={reviewing}
                />
                <div className="flex justify-end gap-2">
                  <button
                    onClick={() => { setReviewMode(false); setReviewFeedback('') }}
                    disabled={reviewing}
                    className="btn-ghost text-xs text-gray-400"
                  >Cancelar</button>
                  <button
                    onClick={requestRevision}
                    disabled={reviewing || !reviewFeedback.trim()}
                    className="btn-ghost flex items-center gap-1.5 px-3 py-1.5 border border-amber-400 text-amber-400 hover:bg-amber-400/20 text-xs"
                  >
                    {reviewing ? <Loader size={13} className="animate-spin" /> : <Send size={13} />}
                    {reviewing ? 'Reprocessando...' : 'Enviar Feedback'}
                  </button>
                </div>
              </div>
            )}
          </div>
        )
      )}

      {/* Input */}
      <div className="flex items-center gap-2 pt-3 border-t border-surface-200">
        <input ref={fileInputRef} type="file" className="hidden" onChange={handleFileUpload} />
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={loading || approving || uploading}
          className="btn-ghost p-2 text-gray-400 hover:text-gold flex-shrink-0"
          title="Enviar documento"
        >
          {uploading ? <Loader size={15} className="animate-spin" /> : <Paperclip size={15} />}
        </button>
        <input
          className="input-field flex-1"
          placeholder="Escrever resposta..."
          value={reply}
          onChange={e => setReply(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
          disabled={loading || approving || uploading}
        />
        <button onClick={send} className="btn-primary p-2" disabled={loading || approving || uploading}><Send size={16} /></button>
      </div>
    </div>
  )
}

function NewThreadModal({ onClose }) {
  const { dispatch, toast, state } = useApp()
  const [agentId, setAgentId] = useState(AGENTS[0]?.id || '')
  const [subject, setSubject] = useState('')
  const [text, setText] = useState('')
  const [opId, setOpId] = useState('')

  const create = () => {
    if (!subject.trim() || !text.trim()) { toast('Preencha assunto e mensagem', 'error'); return }
    const now = new Date().toISOString()
    const thread = {
      id: `msg_${Date.now()}`,
      agent: agentId,
      operation: opId || null,
      type: 'duvida',
      subject: subject.trim(),
      messages: [{ from: 'user', text: text.trim(), time: now, type: 'duvida' }],
      status: 'aberto',
      urgency: 'media',
      unread: 0,
    }
    dispatch({ type: 'ADD_THREAD', payload: thread })
    toast('Conversa iniciada', 'success')
    onClose(thread.id)
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => onClose(null)}>
      <div className="bg-surface-50 border border-surface-200 rounded-xl w-full max-w-md p-6" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold text-white">Nova Conversa</h3>
          <button onClick={() => onClose(null)} className="text-gray-500 hover:text-white"><X size={16} /></button>
        </div>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Agente</label>
            <div className="flex flex-wrap gap-1.5">
              {AGENTS.map(a => (
                <button key={a.id} onClick={() => setAgentId(a.id)}
                  className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-xs transition-all ${agentId === a.id ? 'border-gold text-gold bg-gold/10' : 'border-surface-200 text-gray-400 hover:text-gray-200'}`}>
                  <div className="w-4 h-4 rounded-full flex items-center justify-center text-[7px] font-bold text-white" style={{ background: a.color }}>{a.avatar}</div>
                  {a.name.split(' ')[0]}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Operacao (opcional)</label>
            <select className="input-field text-xs" value={opId} onChange={e => setOpId(e.target.value)}>
              <option value="">Sem operacao vinculada</option>
              {state.operations.map(op => <option key={op.id} value={op.id}>{op.name}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Assunto</label>
            <input className="input-field text-xs" value={subject} onChange={e => setSubject(e.target.value)} placeholder="Ex: Revisao de premissas de WACC" />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Mensagem</label>
            <textarea className="input-field text-xs h-20 resize-none" value={text} onChange={e => setText(e.target.value)} placeholder="Descreva sua duvida ou solicitacao..." />
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <button onClick={() => onClose(null)} className="btn-ghost text-xs">Cancelar</button>
            <button onClick={create} className="btn-primary text-xs flex items-center gap-1.5"><Send size={12} /> Iniciar</button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function ReviewsComm() {
  const { state, dispatch, toast } = useApp()
  const { messages } = state
  const [selectedThread, setSelectedThread] = useState(messages[0]?.id || null)
  const [filterStatus, setFilterStatus] = useState('all')
  const [search, setSearch] = useState('')
  const [showNewThread, setShowNewThread] = useState(false)

  // Abre/cria thread automaticamente quando vem do botão "Consultar MD" do Kanban
  useEffect(() => {
    if (!state.pendingThreadOpen) return
    const { agentId, operationId, subject } = state.pendingThreadOpen
    dispatch({ type: 'CLEAR_PENDING_THREAD' })
    // Verifica se já existe thread aberta para esse agente+operação
    const existing = messages.find(m => m.agent === agentId && m.operation === operationId && m.status === 'aberto')
    if (existing) {
      setSelectedThread(existing.id)
      return
    }
    // Cria nova thread
    const now = new Date().toISOString()
    const newThread = {
      id: `msg_${Date.now()}`,
      agent: agentId,
      operation: operationId || null,
      type: 'duvida',
      subject: subject || `Consulta sobre tarefa`,
      messages: [],
      status: 'aberto',
      urgency: 'media',
      unread: 0,
    }
    dispatch({ type: 'ADD_THREAD', payload: newThread })
    setSelectedThread(newThread.id)
    toast('Conversa aberta com o agente', 'info')
  }, [state.pendingThreadOpen])

  const filteredMessages = messages.filter(m => {
    if (filterStatus === 'aberto' && m.status !== 'aberto') return false
    if (filterStatus === 'resolvido' && m.status !== 'resolvido') return false
    if (search && !m.subject.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  const activeThread = messages.find(m => m.id === selectedThread)

  // Tabs by agent
  const agentTabs = AGENTS.map(a => ({
    ...a,
    unread: messages.filter(m => m.agent === a.id && m.unread > 0).length,
    total: messages.filter(m => m.agent === a.id).length,
  })).filter(a => a.total > 0)

  const [agentFilter, setAgentFilter] = useState(null)
  const displayed = agentFilter
    ? filteredMessages.filter(m => m.agent === agentFilter)
    : filteredMessages

  return (
    <div className="h-full flex flex-col">
      {showNewThread && <NewThreadModal onClose={(id) => { setShowNewThread(false); if (id) setSelectedThread(id) }} />}
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-xl font-bold text-white font-editorial">Revisoes & Comunicacao</h2>
        <button onClick={() => setShowNewThread(true)} className="btn-primary flex items-center gap-1.5 text-xs py-1.5 px-3">
          <Plus size={13} /> Nova Conversa
        </button>
      </div>
      <p className="text-xs text-gray-500 mb-4">{messages.reduce((s, m) => s + m.unread, 0)} mensagens nao lidas</p>

      {/* Agent tabs */}
      <div className="flex gap-1 mb-4 overflow-x-auto pb-1">
        <button
          onClick={() => setAgentFilter(null)}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${!agentFilter ? 'bg-gold/15 text-gold' : 'text-gray-400 hover:text-gray-200 hover:bg-surface-100'}`}
        >Todos</button>
        {agentTabs.map(a => (
          <button
            key={a.id}
            onClick={() => setAgentFilter(agentFilter === a.id ? null : a.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all flex items-center gap-1.5 ${
              agentFilter === a.id ? 'bg-gold/15 text-gold' : 'text-gray-400 hover:text-gray-200 hover:bg-surface-100'
            }`}
          >
            {a.name.split(' ')[0]}
            {a.unread > 0 && <span className="w-4 h-4 bg-accent-red text-white text-[9px] font-bold rounded-full flex items-center justify-center">{a.unread}</span>}
          </button>
        ))}
      </div>

      <div className="flex gap-4 flex-1 min-h-0">
        {/* Thread list */}
        <div className="w-80 flex-shrink-0 flex flex-col border-r border-surface-200 pr-4">
          {/* Filters */}
          <div className="flex gap-1 mb-3">
            {['all', 'aberto', 'resolvido'].map(f => (
              <button key={f} onClick={() => setFilterStatus(f)}
                className={`px-2 py-1 rounded text-[10px] font-medium ${filterStatus === f ? 'bg-surface-100 text-gray-200' : 'text-gray-500'}`}
              >{f === 'all' ? 'Todos' : f.charAt(0).toUpperCase() + f.slice(1)}</button>
            ))}
          </div>
          <div className="relative mb-3">
            <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-500" />
            <input className="input-field pl-7 py-1.5 text-xs" placeholder="Buscar..." value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <div className="flex-1 overflow-y-auto space-y-1">
            {displayed.map(m => {
              const agent = AGENTS.find(a => a.id === m.agent)
              const typeInfo = TYPE_ICONS[m.type]
              return (
                <button
                  key={m.id}
                  onClick={() => setSelectedThread(m.id)}
                  className={`w-full text-left p-3 rounded-lg transition-all ${
                    selectedThread === m.id ? 'bg-gold/10 border border-gold/20' : 'hover:bg-surface-100 border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <div className="w-5 h-5 rounded-full flex items-center justify-center text-[8px] font-bold text-white" style={{ background: agent?.color }}>{agent?.avatar}</div>
                    <span className="text-xs font-medium text-gray-300 truncate flex-1">{agent?.name?.split(' ')[0]}</span>
                    {m.unread > 0 && <span className="w-2 h-2 bg-gold rounded-full" />}
                    {m.awaitingApproval && <span className="text-[9px] font-bold text-accent-green border border-accent-green/40 rounded px-1 py-0.5">APROVAR</span>}
                    <span className={`${typeInfo?.cls} text-[10px]`}>{typeInfo?.label}</span>
                  </div>
                  <p className="text-[11px] text-gray-400 line-clamp-2">{m.subject}</p>
                </button>
              )
            })}
          </div>
        </div>

        {/* Active thread */}
        <div className="flex-1 min-w-0">
          {activeThread ? <Thread thread={activeThread} /> : (
            <div className="h-full flex items-center justify-center text-gray-500 text-sm">Selecione uma conversa</div>
          )}
        </div>
      </div>
    </div>
  )
}
