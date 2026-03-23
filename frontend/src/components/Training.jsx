import { useState, useRef, useEffect } from 'react'
import { useApp } from '../context/AppContext'
import { AGENTS, TRAINING_RECOMMENDATIONS, MD_DEMANDS, MD_CHAT_HISTORY } from '../data/mockData'
import { CheckCircle, Clock, Loader, Send, Upload, Link2, BookOpen } from 'lucide-react'

const API = import.meta.env.VITE_API_URL || ''

const STATUS_CONFIG = {
  concluido: { label: 'Concluido', cls: 'badge-green', icon: CheckCircle },
  em_andamento: { label: 'Em Andamento', cls: 'badge-gold', icon: Loader },
  pendente: { label: 'Pendente', cls: 'badge-red', icon: Clock },
  atendido: { label: 'Atendido', cls: 'badge-green', icon: CheckCircle },
}

function RecommendationsPanel() {
  const { state, dispatch, toast } = useApp()

  return (
    <div>
      <p className="section-title">Recomendacoes de Treinamento</p>
      <div className="space-y-2">
        {state.training.map(tr => {
          const agent = AGENTS.find(a => a.id === tr.agent)
          const st = STATUS_CONFIG[tr.status]
          const Icon = st.icon
          return (
            <div key={tr.id} className="card-hover p-4 flex items-center gap-4">
              <div className="w-8 h-8 rounded-full flex items-center justify-center text-[9px] font-bold text-white flex-shrink-0"
                style={{ background: agent?.color }}>{agent?.avatar}</div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-200">{tr.topic}</p>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-[10px]" style={{ color: agent?.color }}>{agent?.name?.split(' ')[0]}</span>
                  <span className="text-[10px] text-gray-600">·</span>
                  <span className="text-[10px] text-gray-500">{tr.source}</span>
                  <span className="text-[10px] text-gray-600">·</span>
                  <span className="text-[10px] text-gray-500">{tr.date}</span>
                </div>
              </div>
              <span className={st.cls}>{st.label}</span>
              {tr.status !== 'concluido' && (
                <button
                  onClick={() => { dispatch({ type: 'COMPLETE_TRAINING', payload: tr.id }); toast('Treinamento marcado como concluido', 'info') }}
                  className="btn-ghost text-[10px]"
                >Concluir</button>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function MDChat() {
  const { toast } = useApp()
  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem('ib_md_chat')
      return saved ? JSON.parse(saved) : MD_CHAT_HISTORY.map(m => ({ ...m }))
    } catch { return MD_CHAT_HISTORY.map(m => ({ ...m })) }
  })
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const endRef = useRef(null)

  useEffect(() => { try { localStorage.setItem('ib_md_chat', JSON.stringify(messages)) } catch {} }, [messages])
  useEffect(() => endRef.current?.scrollIntoView({ behavior: 'smooth' }), [messages.length])

  const send = async () => {
    if (!input.trim() || loading) return
    const userMsg = { from: 'user', text: input, time: new Date().toISOString() }
    const updatedMessages = [...messages, userMsg]
    setMessages(updatedMessages)
    setInput('')
    setLoading(true)
    try {
      const history = updatedMessages.map(m => ({
        role: m.from === 'user' ? 'user' : 'assistant',
        content: m.text,
      }))
      const res = await fetch(`${API}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: history }),
      })
      const data = await res.json()
      setMessages(prev => [...prev, {
        from: 'md_orchestrator',
        text: data.text,
        time: new Date().toISOString(),
      }])
    } catch {
      toast('Erro ao conectar com o MD — verifique se o servidor esta rodando', 'error')
    } finally {
      setLoading(false)
    }
  }

  const mdAgent = AGENTS.find(a => a.id === 'md_orchestrator')

  return (
    <div className="flex flex-col h-[450px]">
      <p className="section-title flex items-center gap-2">
        Chat com o MD Senior
        <span className="w-2 h-2 bg-accent-green rounded-full animate-pulse" />
      </p>
      <div className="flex-1 overflow-y-auto space-y-3 mb-3 pr-1 card p-4">
        {messages.map((msg, i) => {
          const isUser = msg.from === 'user'
          return (
            <div key={i} className={`flex gap-2.5 ${isUser ? 'flex-row-reverse' : ''}`}>
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[8px] font-bold text-white flex-shrink-0 ${isUser ? 'bg-gold' : ''}`}
                style={!isUser ? { background: mdAgent?.color } : undefined}>
                {isUser ? 'VC' : mdAgent?.avatar}
              </div>
              <div className={`max-w-[75%]`}>
                <div className={`rounded-xl px-3 py-2 text-xs leading-relaxed ${
                  isUser ? 'bg-gold/15 text-gold-light' : 'bg-surface-100 text-gray-300'
                }`}>{msg.text}</div>
                <p className="text-[9px] text-gray-600 mt-0.5 px-1">
                  {new Date(msg.time).toLocaleString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          )
        })}
        <div ref={endRef} />
      </div>
      {loading && (
        <div className="flex gap-2.5 mb-2">
          <div className="w-6 h-6 rounded-full flex items-center justify-center text-[8px] font-bold text-white flex-shrink-0" style={{ background: '#d4a853' }}>MD</div>
          <div className="bg-surface-100 rounded-xl px-3 py-2 text-xs text-gray-400 flex items-center gap-1">
            <span className="animate-pulse">●</span><span className="animate-pulse" style={{animationDelay:'0.2s'}}>●</span><span className="animate-pulse" style={{animationDelay:'0.4s'}}>●</span>
          </div>
        </div>
      )}
      <div className="flex items-center gap-2">
        <input className="input-field flex-1" placeholder="Enviar instrucao ao MD..." value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && send()} disabled={loading} />
        <button onClick={send} className="btn-primary p-2" disabled={loading}><Send size={16} /></button>
      </div>
    </div>
  )
}

function MDDemands() {
  const { state, dispatch, toast } = useApp()

  return (
    <div>
      <p className="section-title">Demandas do MD Senior</p>
      <div className="space-y-2">
        {state.mdDemands.map(d => {
          const st = STATUS_CONFIG[d.status]
          return (
            <div key={d.id} className="card-hover p-4 flex items-center gap-4">
              <BookOpen size={16} className="text-gold flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm text-gray-200">{d.text}</p>
                <p className="text-[10px] text-gray-500 mt-0.5">{d.date}</p>
              </div>
              <span className={st.cls}>{st.label}</span>
              {d.status !== 'atendido' && (
                <div className="flex gap-1">
                  <button className="btn-ghost p-1.5" title="Enviar link"><Link2 size={13} /></button>
                  <button className="btn-ghost p-1.5" title="Upload"><Upload size={13} /></button>
                  <button onClick={() => { dispatch({ type: 'ATTEND_DEMAND', payload: d.id }); toast('Demanda atendida', 'info') }} className="btn-ghost text-[10px] text-accent-green">Atender</button>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default function Training() {
  return (
    <div>
      <h2 className="text-xl font-bold text-white font-editorial mb-1">Treinamento do MD</h2>
      <p className="text-xs text-gray-500 mb-6">Gestao de conhecimento e comunicacao com o agente orquestrador</p>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-8">
        <RecommendationsPanel />
        <MDDemands />
      </div>

      <MDChat />
    </div>
  )
}
