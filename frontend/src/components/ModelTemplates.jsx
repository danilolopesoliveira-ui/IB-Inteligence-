import { useState, useRef, useEffect } from 'react'
import { useApp } from '../context/AppContext'
import { AGENTS, MODEL_TEMPLATES, MODEL_CATEGORIES } from '../data/mockData'
import { FileText, FileSpreadsheet, Presentation, Download, Eye, Search, Send, X, MessageCircle, ArrowLeft, Tag, Layers, Users, FolderOpen } from 'lucide-react'

const API = import.meta.env.VITE_API_URL || ''

// Arquivos servidos via API (busca recursiva nas subpastas de templates/models/)
const FILES = {
  tpl_17:'dossie_analitico_solaris_energia.pdf',
  tpl_16:'research_report_vetta_logistica.pdf',
  tpl_15:'pitchbook_final_cri_brz.pptx',
  tpl_14:'pitchbook_ai_agrovale.pptx',
  tpl_13:'pitchbook_v2_cra_meridian.pptx',
  tpl_12:'apresentacao_institucional_completa.pptx',
  tpl_10:'pitch_book_debentures_completo.pptx',
  tpl_01:'pitch_book_debentures_infra.pptx', tpl_02:'pitch_book_ecm_follow_on.pptx',
  tpl_03:'modelo_financeiro_dcf_credit.xlsx', tpl_04:'memorando_informacoes_debentures.pdf',
  tpl_05:'research_report_completo.pdf', tpl_06:'term_sheet_cra.pdf',
  tpl_07:'executive_memo_comite.pdf', tpl_08:'investor_presentation_roadshow.pptx',
  tpl_09:'modelo_bond_pricing.xlsx',
}

// Subpasta de cada template (para exibir na UI)
const FILE_FOLDER = {
  tpl_17:'memos_reports', tpl_16:'memos_reports', tpl_15:'pitch_books',
  tpl_14:'pitch_books',   tpl_13:'pitch_books',   tpl_12:'pitch_books',
  tpl_10:'pitch_books',   tpl_01:'pitch_books',   tpl_02:'pitch_books',
  tpl_03:'financial_models', tpl_09:'financial_models',
  tpl_04:'term_sheets',   tpl_06:'term_sheets',
  tpl_05:'memos_reports', tpl_07:'memos_reports', tpl_08:'pitch_books',
}

// Arquivos servidos diretamente pelo Vite (frontend/public/knowledge/)
const PUBLIC_FILES = {
  tpl_11:            '/knowledge/book_credito_meridian_alimentos_cra.pptx',
  tpl_dcm_parecer:   '/knowledge/parecer_credito_dcm.pptx',
  tpl_ecm_opinion:   '/knowledge/equity_opinion_ecm.pptx',
  tpl_nissei_credito:     '/knowledge/parecer_credito_nissei.pptx',
  tpl_nissei_analise_xlsx:'/knowledge/analise_credito_nissei.xlsx',
}
const PUBLIC_FOLDER = {
  tpl_11:'pareceres', tpl_dcm_parecer:'pareceres',
  tpl_ecm_opinion:'pareceres', tpl_nissei_credito:'pareceres',
  tpl_nissei_analise_xlsx:'pareceres',
}

const FOLDER_LABELS = {
  pitch_books:'Pitch Books', financial_models:'Modelos Financeiros',
  memos_reports:'Memos & Reports', term_sheets:'Term Sheets', pareceres:'Pareceres',
}

const ICONS = { PPTX: Presentation, XLSX: FileSpreadsheet, PDF: FileText }
const COLORS = { PPTX: '#ef4444', XLSX: '#10b981', PDF: '#3b82f6' }
const STATUS = { aprovado: { l: 'Aprovado', c: 'badge-green' }, em_revisao: { l: 'Em Revisao', c: 'badge-gold' }, rascunho: { l: 'Rascunho', c: 'bg-surface-200 text-gray-400 badge' } }

function FolderBadge({ tplId }) {
  const folder = FILE_FOLDER[tplId] || PUBLIC_FOLDER[tplId]
  if (!folder) return null
  return (
    <span className="flex items-center gap-1 text-[9px] text-gray-500 bg-surface-100 px-1.5 py-0.5 rounded">
      <FolderOpen size={9} className="text-gold" />
      templates/models/{folder}/
    </span>
  )
}

function doDownload(tplId, name) {
  if (PUBLIC_FILES[tplId]) {
    const url = PUBLIC_FILES[tplId]
    const ext = url.split('.').pop()
    const a = document.createElement('a')
    a.href = url
    a.download = name.replace(/[^\w\s-]/g, '').trim().replace(/\s+/g, '_') + '.' + ext
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    return
  }
  const f = FILES[tplId]
  if (f) { window.open(`${API}/api/templates/download/${f}`, '_blank') }
}

function Card({ tpl, onClick }) {
  const ag = AGENTS.find(a => a.id === tpl.agent); const I = ICONS[tpl.format] || FileText; const st = STATUS[tpl.status] || STATUS.rascunho
  return (
    <div onClick={() => onClick(tpl)} className="card-hover p-4 cursor-pointer group">
      <div className="flex items-start gap-3 mb-3">
        <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: COLORS[tpl.format] + '20' }}><I size={20} style={{ color: COLORS[tpl.format] }} /></div>
        <div className="flex-1 min-w-0">
          <h4 className="text-[13px] font-bold text-white leading-tight group-hover:text-gold transition-colors">{tpl.name}</h4>
          <div className="flex items-center gap-2 mt-1">
            <span className={`badge ${tpl.dealType === 'DCM' ? 'badge-blue' : tpl.dealType === 'ECM' ? 'badge-green' : 'badge-gold'}`}>{tpl.dealType}</span>
            <span className={st.c}>{st.l}</span>
            <span className="text-[9px] text-gray-500">{tpl.format} · {tpl.pages}p · {tpl.version}</span>
          </div>
        </div>
      </div>
      <p className="text-[11px] text-gray-400 leading-relaxed mb-3 line-clamp-2">{tpl.description}</p>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded-full flex items-center justify-center text-[7px] font-bold text-white" style={{ background: ag?.color }}>{ag?.avatar}</div>
          <span className="text-[10px] text-gray-500">{ag?.name?.split(' ')[0]}</span>
        </div>
        <div className="flex items-center gap-3">
          {(tpl.feedback?.length || 0) > 0 && <span className="flex items-center gap-1 text-[10px] text-gray-500"><MessageCircle size={10} /> {tpl.feedback.length}</span>}
          <span className="text-[10px] text-gray-600">{tpl.lastUpdated}</span>
        </div>
      </div>
      <div className="mt-2 pt-2 border-t border-surface-200">
        <FolderBadge tplId={tpl.id} />
      </div>
    </div>
  )
}

function Detail({ tpl, onBack }) {
  const { toast } = useApp()
  const [msgs, setMsgs] = useState(tpl.feedback?.map(f => ({ ...f })) || [])
  const [input, setInput] = useState('')
  const endRef = useRef(null)
  useEffect(() => endRef.current?.scrollIntoView({ behavior: 'smooth' }), [msgs.length])
  const ag = AGENTS.find(a => a.id === tpl.agent); const I = ICONS[tpl.format] || FileText; const st = STATUS[tpl.status] || STATUS.rascunho

  const send = () => {
    if (!input.trim()) return
    setMsgs(p => [...p, { from: 'user', text: input, time: new Date().toISOString() }]); setInput(''); toast('Orientacao enviada', 'info')
    setTimeout(() => setMsgs(p => [...p, { from: tpl.agent, text: `Entendido. Aplicarei na proxima versao (${tpl.version} -> v${(parseFloat(tpl.version.replace('v',''))+0.1).toFixed(1)}). Estimativa: 4h.`, time: new Date().toISOString() }]), 2000)
  }

  return (
    <div className="flex flex-col h-full">
      <button onClick={onBack} className="btn-ghost mb-3 flex items-center gap-1 text-xs w-fit"><ArrowLeft size={14} /> Voltar</button>
      <div className="card p-5 mb-4">
        <div className="flex items-start gap-4">
          <div className="w-14 h-14 rounded-xl flex items-center justify-center" style={{ background: COLORS[tpl.format] + '20' }}><I size={28} style={{ color: COLORS[tpl.format] }} /></div>
          <div className="flex-1">
            <h3 className="text-base font-bold text-white mb-1">{tpl.name}</h3>
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <span className={`badge ${tpl.dealType === 'DCM' ? 'badge-blue' : tpl.dealType === 'ECM' ? 'badge-green' : 'badge-gold'}`}>{tpl.dealType}</span>
              <span className={st.c}>{st.l}</span>
              <span className="text-[10px] text-gray-500">{tpl.format} · {tpl.pages}p · {tpl.version} · {tpl.lastUpdated}</span>
            </div>
            <p className="text-xs text-gray-400">{tpl.description}</p>
          </div>
          <div className="flex gap-2 flex-shrink-0">
            <button className="btn-ghost p-2" title="Visualizar"><Eye size={16} /></button>
            <button className="btn-primary flex items-center gap-1.5 text-xs" onClick={() => doDownload(tpl.id, tpl.name)}><Download size={14} /> Download</button>
          </div>
        </div>
        <div className="grid grid-cols-4 gap-4 mt-4 pt-4 border-t border-surface-200">
          <div><div className="flex items-center gap-1.5 text-[10px] text-gray-500 mb-1"><Users size={10} /> Agente</div>
            <div className="flex items-center gap-1.5"><div className="w-5 h-5 rounded-full flex items-center justify-center text-[7px] font-bold text-white" style={{ background: ag?.color }}>{ag?.avatar}</div><span className="text-xs text-gray-300">{ag?.name}</span></div></div>
          <div><div className="flex items-center gap-1.5 text-[10px] text-gray-500 mb-1"><Layers size={10} /> Secoes</div><span className="text-xs text-gray-300">{tpl.sections?.length || 0} secoes</span></div>
          <div><div className="flex items-center gap-1.5 text-[10px] text-gray-500 mb-1"><Tag size={10} /> Usado Em</div><span className="text-xs text-gray-300">{tpl.usedIn?.length || 0} operacoes</span></div>
          <div><div className="flex items-center gap-1.5 text-[10px] text-gray-500 mb-1"><FolderOpen size={10} /> Pasta</div><FolderBadge tplId={tpl.id} /></div>
        </div>
        {tpl.sections?.length > 0 && <div className="mt-3 pt-3 border-t border-surface-200"><p className="text-[10px] text-gray-500 font-medium mb-2">Estrutura:</p><div className="flex flex-wrap gap-1.5">{tpl.sections.map((s, i) => <span key={i} className="text-[9px] text-gray-400 bg-surface px-2 py-1 rounded">{i+1}. {s}</span>)}</div></div>}
        {tpl.usedIn?.length > 0 && <div className="mt-3 pt-3 border-t border-surface-200"><p className="text-[10px] text-gray-500 font-medium mb-1.5">Operacoes:</p><div className="flex flex-wrap gap-1.5">{tpl.usedIn.map((o, i) => <span key={i} className="badge badge-gold">{o}</span>)}</div></div>}
      </div>
      <div className="card flex-1 flex flex-col min-h-[300px]">
        <div className="px-4 py-3 border-b border-surface-200 flex items-center justify-between">
          <div><h4 className="text-sm font-bold text-white">Canal de Orientacao</h4><p className="text-[10px] text-gray-500">Envie instrucoes de melhoria ao agente</p></div>
          <span className="text-[10px] text-gray-500">{msgs.length} mensagens</span>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {msgs.length === 0 && <div className="text-center py-8"><MessageCircle size={28} className="mx-auto text-gray-600 mb-2" /><p className="text-xs text-gray-500">Nenhuma orientacao ainda</p></div>}
          {msgs.map((m, i) => {
            const u = m.from === 'user'; const ma = AGENTS.find(a => a.id === m.from)
            return (<div key={i} className={`flex gap-2.5 ${u ? 'flex-row-reverse' : ''}`}>
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[8px] font-bold text-white flex-shrink-0 ${u ? 'bg-gold' : ''}`} style={!u ? { background: ma?.color || ag?.color } : undefined}>{u ? 'VC' : ma?.avatar || ag?.avatar}</div>
              <div className="max-w-[75%]"><div className={`rounded-xl px-3 py-2 text-xs leading-relaxed ${u ? 'bg-gold/15 text-gold-light' : 'bg-surface-100 text-gray-300'}`}>{m.text}</div>
              <p className="text-[9px] text-gray-600 mt-0.5 px-1">{new Date(m.time).toLocaleString('pt-BR',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'})}</p></div></div>)
          })}
          <div ref={endRef} />
        </div>
        <div className="flex items-center gap-2 p-3 border-t border-surface-200">
          <input className="input-field flex-1" placeholder="Ex: Ajustar slide X, mudar formato da tabela..." value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && send()} />
          <button onClick={send} className="btn-primary p-2"><Send size={16} /></button>
        </div>
      </div>
    </div>
  )
}

export default function ModelTemplates() {
  const [cat, setCat] = useState('all'); const [search, setSearch] = useState(''); const [sel, setSel] = useState(null)
  const filtered = MODEL_TEMPLATES.filter(t => { if (cat !== 'all' && t.category !== cat) return false; if (search && !t.name.toLowerCase().includes(search.toLowerCase())) return false; return true })
  if (sel) return <Detail tpl={sel} onBack={() => setSel(null)} />
  const approved = MODEL_TEMPLATES.filter(t => t.status === 'aprovado').length
  return (
    <div>
      <h2 className="text-xl font-bold text-white font-editorial mb-1">Modelos</h2>
      <p className="text-xs text-gray-500 mb-5">{MODEL_TEMPLATES.length} modelos · {approved} aprovados · Download disponivel via API</p>
      <div className="grid grid-cols-4 gap-3 mb-5">
        {[{l:'Pitch Books',c:MODEL_TEMPLATES.filter(t=>t.category==='pitch_book').length,co:'#ef4444'},{l:'Modelos Financeiros',c:MODEL_TEMPLATES.filter(t=>t.category==='financial_model').length,co:'#10b981'},{l:'Memos & Reports',c:MODEL_TEMPLATES.filter(t=>t.category==='memo'||t.category==='research').length,co:'#3b82f6'},{l:'Term Sheets & Outros',c:MODEL_TEMPLATES.filter(t=>t.category==='term_sheet'||t.category==='presentation').length,co:'#d4a853'}].map(s=>(
          <div key={s.l} className="card p-3"><p className="text-xl font-bold text-white">{s.c}</p><p className="text-[10px] text-gray-500">{s.l}</p><div className="h-0.5 rounded-full mt-2" style={{background:s.co,opacity:0.4}}/></div>
        ))}
      </div>
      <div className="flex items-center gap-3 mb-4">
        <div className="flex gap-1 overflow-x-auto pb-1">
          {MODEL_CATEGORIES.map(c=><button key={c.id} onClick={()=>setCat(c.id)} className={`px-3 py-1.5 rounded-lg text-[11px] font-medium whitespace-nowrap transition-all ${cat===c.id?'bg-gold/15 text-gold':'text-gray-400 hover:text-gray-200 hover:bg-surface-100'}`}>{c.label}</button>)}
        </div>
        <div className="relative flex-1 max-w-xs ml-auto"><Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-500" /><input className="input-field pl-7 py-1.5 text-xs" placeholder="Buscar..." value={search} onChange={e=>setSearch(e.target.value)} /></div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">{filtered.map(t=><Card key={t.id} tpl={t} onClick={setSel} />)}</div>
      {filtered.length===0&&<div className="text-center py-12"><FileText size={32} className="mx-auto text-gray-600 mb-3"/><p className="text-sm text-gray-500">Nenhum modelo encontrado</p></div>}
    </div>
  )
}
