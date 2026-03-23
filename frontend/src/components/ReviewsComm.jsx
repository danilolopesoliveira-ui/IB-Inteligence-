import { useState, useRef, useEffect } from 'react'
import { useApp } from '../context/AppContext'
import { AGENTS, OPERATIONS } from '../data/mockData'
import { Send, Filter, MessageCircle, AlertTriangle, RotateCcw, CheckCircle, Search } from 'lucide-react'

const API = import.meta.env.VITE_API_URL || ''

const TYPE_ICONS = {
  duvida: { icon: MessageCircle, label: 'Duvida', cls: 'text-accent-blue' },
  revisao: { icon: RotateCcw, label: 'Revisao', cls: 'text-gold' },
  alerta: { icon: AlertTriangle, label: 'Alerta', cls: 'text-accent-red' },
  resposta: { icon: CheckCircle, label: 'Resposta', cls: 'text-accent-green' },
}

function Thread({ thread }) {
  const { dispatch, toast } = useApp()
  const [reply, setReply] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const agent = AGENTS.find(a => a.id === thread.agent)
  const op = OPERATIONS.find(o => o.id === thread.operation)

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
      // Anthropic exige que a primeira mensagem seja 'user'
      const firstUser = allMsgs.findIndex(m => m.role === 'user')
      const history = firstUser >= 0 ? allMsgs.slice(firstUser) : allMsgs
      const res = await fetch(`${API}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: history,
          system_prompt: agent?.promptBase || undefined,
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`)
      if (!data.text) throw new Error('Resposta vazia do servidor')
      dispatch({ type: 'ADD_AGENT_RESPONSE', payload: { threadId: thread.id, agentId: thread.agent, text: data.text } })
    } catch (err) {
      toast(`Erro: ${err.message}`, 'error')
    } finally {
      setLoading(false)
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
                  {msg.text}
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
      {/* Input */}
      <div className="flex items-center gap-2 pt-3 border-t border-surface-200">
        <input
          className="input-field flex-1"
          placeholder="Escrever resposta..."
          value={reply}
          onChange={e => setReply(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
          disabled={loading}
        />
        <button onClick={send} className="btn-primary p-2" disabled={loading}><Send size={16} /></button>
      </div>
    </div>
  )
}

export default function ReviewsComm() {
  const { state } = useApp()
  const { messages } = state
  const [selectedThread, setSelectedThread] = useState(messages[0]?.id || null)
  const [filterStatus, setFilterStatus] = useState('all')
  const [search, setSearch] = useState('')

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
      <h2 className="text-xl font-bold text-white font-editorial mb-1">Revisoes & Comunicacao</h2>
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
