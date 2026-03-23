import { useState, useEffect } from 'react'
import { useApp } from '../context/AppContext'
import { AGENTS, KNOWLEDGE_ITEMS } from '../data/mockData'
import { BookOpen, Plus, FileText, Link2, Shield, Search, X, Upload, Eye, ExternalLink } from 'lucide-react'

const TYPE_ICONS = { PDF: FileText, Link: Link2, Regulamento: Shield, Research: Search }

function PreviewModal({ item, onClose }) {
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!item.url) {
      setError('Este arquivo nao possui um link disponivel ainda.')
      setLoading(false)
      return
    }
    fetch(item.url)
      .then(r => {
        if (!r.ok) throw new Error(`Erro ao carregar arquivo (${r.status})`)
        return r.text()
      })
      .then(text => { setContent(text); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [item.url])

  // Minimal markdown renderer: headers, bold, tables, code blocks, lists
  const renderMarkdown = (md) => {
    const lines = md.split('\n')
    const result = []
    let i = 0
    while (i < lines.length) {
      const line = lines[i]
      if (line.startsWith('# ')) {
        result.push(<h1 key={i} className="text-xl font-bold text-white mt-4 mb-2">{line.slice(2)}</h1>)
      } else if (line.startsWith('## ')) {
        result.push(<h2 key={i} className="text-base font-bold text-gold mt-4 mb-2">{line.slice(3)}</h2>)
      } else if (line.startsWith('### ')) {
        result.push(<h3 key={i} className="text-sm font-semibold text-gray-200 mt-3 mb-1">{line.slice(4)}</h3>)
      } else if (line.startsWith('---')) {
        result.push(<hr key={i} className="border-surface-200 my-3" />)
      } else if (line.startsWith('| ')) {
        // table
        const tableLines = []
        while (i < lines.length && lines[i].startsWith('|')) {
          tableLines.push(lines[i]); i++
        }
        const rows = tableLines.filter(l => !l.match(/^\|[-| ]+\|$/))
        result.push(
          <div key={`table-${i}`} className="overflow-x-auto my-3">
            <table className="text-xs w-full border-collapse">
              {rows.map((row, ri) => {
                const cells = row.split('|').filter((_, ci) => ci > 0 && ci < row.split('|').length - 1)
                const Tag = ri === 0 ? 'th' : 'td'
                return (
                  <tr key={ri} className={ri === 0 ? 'bg-surface-200' : ri % 2 === 0 ? 'bg-surface-100/30' : ''}>
                    {cells.map((cell, ci) => (
                      <Tag key={ci} className="border border-surface-200 px-2 py-1 text-left text-gray-300 whitespace-nowrap">{cell.trim()}</Tag>
                    ))}
                  </tr>
                )
              })}
            </table>
          </div>
        )
        continue
      } else if (line.startsWith('- ') || line.startsWith('* ')) {
        result.push(<li key={i} className="text-sm text-gray-300 ml-4 list-disc">{line.slice(2)}</li>)
      } else if (line.startsWith('```')) {
        const codeLines = []
        i++
        while (i < lines.length && !lines[i].startsWith('```')) { codeLines.push(lines[i]); i++ }
        result.push(
          <pre key={`code-${i}`} className="bg-black/40 rounded p-3 text-xs text-green-300 overflow-x-auto my-2 font-mono whitespace-pre-wrap">
            {codeLines.join('\n')}
          </pre>
        )
      } else if (line.trim() === '') {
        result.push(<div key={i} className="h-2" />)
      } else {
        // inline bold
        const parts = line.split(/\*\*(.*?)\*\*/)
        result.push(
          <p key={i} className="text-sm text-gray-300 leading-relaxed">
            {parts.map((p, pi) => pi % 2 === 1 ? <strong key={pi} className="text-white font-semibold">{p}</strong> : p)}
          </p>
        )
      }
      i++
    }
    return result
  }

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[100] flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-surface-50 border border-surface-200 rounded-xl w-full max-w-3xl max-h-[85vh] flex flex-col" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-surface-200 flex-shrink-0">
          <div>
            <h3 className="text-base font-bold text-white">{item.title}</h3>
            <p className="text-xs text-gray-500 mt-0.5">{item.type} · {item.date}</p>
          </div>
          <div className="flex items-center gap-2">
            {item.url && (
              <a href={item.url} target="_blank" rel="noreferrer"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-gray-400 hover:text-white hover:bg-surface-200 transition-all">
                <ExternalLink size={13} /> Abrir
              </a>
            )}
            <button onClick={onClose} className="text-gray-500 hover:text-white p-1"><X size={18} /></button>
          </div>
        </div>
        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5">
          {loading && <p className="text-sm text-gray-500 text-center py-8">Carregando...</p>}
          {error && <p className="text-sm text-gray-500 text-center py-8">{error}</p>}
          {!loading && !error && <div>{renderMarkdown(content)}</div>}
        </div>
      </div>
    </div>
  )
}

function AddResourceModal({ onClose }) {
  const { toast } = useApp()
  const [form, setForm] = useState({ title: '', type: 'PDF', url: '', description: '', tags: '', agents: [] })

  const save = () => {
    toast('Recurso adicionado com sucesso', 'info')
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100] flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-surface-50 border border-surface-200 rounded-xl w-full max-w-lg p-6" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-lg font-bold text-white">Adicionar Recurso</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-white"><X size={18} /></button>
        </div>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-gray-400 block mb-1">Titulo</label>
            <input className="input-field" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} placeholder="Ex: Resolucao CVM 160" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-400 block mb-1">Tipo</label>
              <select className="input-field" value={form.type} onChange={e => setForm({ ...form, type: e.target.value })}>
                <option>PDF</option><option>Link</option><option>Regulamento</option><option>Research</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Tags (separadas por virgula)</label>
              <input className="input-field" value={form.tags} onChange={e => setForm({ ...form, tags: e.target.value })} placeholder="CVM, Regulatorio" />
            </div>
          </div>
          <div>
            <label className="text-xs text-gray-400 block mb-1">URL ou Upload</label>
            <div className="border-2 border-dashed border-surface-200 rounded-lg p-6 text-center hover:border-gold/30 transition-colors cursor-pointer">
              <Upload size={24} className="mx-auto text-gray-500 mb-2" />
              <p className="text-xs text-gray-400">Arraste um arquivo ou clique para selecionar</p>
            </div>
          </div>
          <div>
            <label className="text-xs text-gray-400 block mb-1">Descricao</label>
            <textarea className="input-field h-16 resize-none" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
          </div>
          <div>
            <label className="text-xs text-gray-400 block mb-1">Agentes Destinatarios</label>
            <div className="flex flex-wrap gap-2">
              {AGENTS.map(a => (
                <button
                  key={a.id}
                  onClick={() => setForm({ ...form, agents: form.agents.includes(a.id) ? form.agents.filter(x => x !== a.id) : [...form.agents, a.id] })}
                  className={`px-2.5 py-1 rounded-full text-[11px] font-medium border transition-all ${
                    form.agents.includes(a.id) ? 'border-gold text-gold bg-gold/10' : 'border-surface-200 text-gray-400 hover:text-gray-200'
                  }`}
                >
                  {a.name.split(' ')[0]}
                </button>
              ))}
            </div>
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-5">
          <button onClick={onClose} className="btn-ghost">Cancelar</button>
          <button onClick={save} className="btn-primary">Adicionar</button>
        </div>
      </div>
    </div>
  )
}

export default function KnowledgeLibrary() {
  const [activeTab, setActiveTab] = useState('all')
  const [showAdd, setShowAdd] = useState(false)
  const [search, setSearch] = useState('')
  const [previewItem, setPreviewItem] = useState(null)

  const agents = [{ id: 'all', name: 'Todos' }, ...AGENTS]
  const items = KNOWLEDGE_ITEMS.filter(item => {
    if (activeTab !== 'all' && item.agent !== activeTab) return false
    if (search && !item.title.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  const unreadByAgent = AGENTS.reduce((acc, a) => {
    acc[a.id] = KNOWLEDGE_ITEMS.filter(k => k.agent === a.id && k.unread).length
    return acc
  }, {})

  return (
    <div>
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-xl font-bold text-white font-editorial">Biblioteca de Conhecimento</h2>
          <p className="text-xs text-gray-500 mt-0.5">{KNOWLEDGE_ITEMS.length} recursos cadastrados</p>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={() => setShowAdd(true)}>
          <Plus size={14} /> Adicionar Recurso
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-4 overflow-x-auto pb-1">
        {agents.map(a => {
          const unread = a.id === 'all' ? 0 : (unreadByAgent[a.id] || 0)
          return (
            <button
              key={a.id}
              onClick={() => setActiveTab(a.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all flex items-center gap-1.5 ${
                activeTab === a.id ? 'bg-gold/15 text-gold' : 'text-gray-400 hover:text-gray-200 hover:bg-surface-100'
              }`}
            >
              {a.name.split(' ')[0]}
              {unread > 0 && <span className="w-4 h-4 bg-accent-red text-white text-[9px] font-bold rounded-full flex items-center justify-center">{unread}</span>}
            </button>
          )
        })}
      </div>

      {/* Search */}
      <div className="relative mb-4">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
        <input className="input-field pl-8" placeholder="Buscar recurso..." value={search} onChange={e => setSearch(e.target.value)} />
      </div>

      {/* Items */}
      <div className="space-y-2">
        {items.map(item => {
          const Icon = TYPE_ICONS[item.type] || FileText
          const agent = AGENTS.find(a => a.id === item.agent)
          return (
            <div
              key={item.id}
              className="card-hover p-4 flex items-center gap-4 cursor-pointer"
              onClick={() => setPreviewItem(item)}
            >
              <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${item.unread ? 'bg-gold/20' : 'bg-surface-200'}`}>
                <Icon size={16} className={item.unread ? 'text-gold' : 'text-gray-400'} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className={`text-sm font-medium truncate ${item.unread ? 'text-white' : 'text-gray-300'}`}>{item.title}</p>
                  {item.unread && <span className="w-2 h-2 bg-gold rounded-full flex-shrink-0" />}
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-[10px] text-gray-500">{item.type}</span>
                  <span className="text-[10px] text-gray-600">·</span>
                  <span className="text-[10px] text-gray-500">{item.date}</span>
                  <span className="text-[10px] text-gray-600">·</span>
                  <span className="text-[10px]" style={{ color: agent?.color }}>{agent?.name?.split(' ')[0]}</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1.5">
                  {item.tags.slice(0, 2).map(tag => (
                    <span key={tag} className="badge bg-surface-200 text-gray-400">{tag}</span>
                  ))}
                </div>
                <Eye size={14} className={`flex-shrink-0 ${item.url ? 'text-gray-400 hover:text-gold' : 'text-gray-600'}`} />
              </div>
            </div>
          )
        })}
      </div>

      {showAdd && <AddResourceModal onClose={() => setShowAdd(false)} />}
      {previewItem && <PreviewModal item={previewItem} onClose={() => setPreviewItem(null)} />}
    </div>
  )
}
