import { useState } from 'react'
import { useApp } from '../context/AppContext'
import { AGENTS, BRL_COMPACT, DOC_CHECKLIST } from '../data/mockData'
import { ChevronRight, FileText, Download, Eye, Clock, CheckCircle, AlertCircle, Loader, FileSignature, X } from 'lucide-react'
import TermSheetModal from './TermSheetModal'

const STATUS_CONFIG = {
  analisado: { label: 'Analisado', cls: 'badge-green', icon: CheckCircle },
  em_analise: { label: 'Em Analise', cls: 'badge-gold', icon: Loader },
  pendente: { label: 'Pendente', cls: 'badge-red', icon: AlertCircle },
  rascunho: { label: 'Rascunho', cls: 'bg-surface-200 text-gray-400 badge', icon: FileText },
  em_revisao: { label: 'Em Revisao', cls: 'badge-gold', icon: Loader },
  aprovado: { label: 'Aprovado', cls: 'badge-green', icon: CheckCircle },
}

function OperationDetail({ operation, onBack, onTermSheet }) {
  const [tab, setTab] = useState('client')
  const tabs = [
    { id: 'client', label: 'Documentos do Cliente' },
    { id: 'agent', label: 'Documentos Gerados' },
    { id: 'timeline', label: 'Timeline' },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <button onClick={onBack} className="btn-ghost flex items-center gap-1 text-xs">
          <ChevronRight size={14} className="rotate-180" /> Voltar
        </button>
        <button
          onClick={e => onTermSheet(e, operation.company)}
          className="btn-primary flex items-center gap-2 text-xs"
        >
          <FileSignature size={14} /> Emitir Proposta
        </button>
      </div>

      <div className="flex items-center gap-4 mb-6">
        <span className={`badge ${operation.type === 'DCM' ? 'badge-blue' : 'badge-green'}`}>{operation.type} — {operation.instrument}</span>
        <h2 className="text-xl font-bold text-white font-editorial">{operation.name}</h2>
        <span className="text-xs text-gray-500">{operation.company} · {operation.sector}</span>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-5 gap-4 mb-6">
        {[
          { label: 'Valor', value: BRL_COMPACT(operation.value) },
          { label: 'Rating', value: operation.rating || '—' },
          { label: 'Abertura', value: operation.openDate || (operation.openedAt ? new Date(operation.openedAt).toLocaleDateString('pt-BR') : '—') },
          { label: 'Prazo', value: operation.targetDate || (operation.deadline ? `${operation.deadline} meses` : '—') },
          { label: 'Status', value: operation.status || '—' },
        ].map(s => (
          <div key={s.label} className="card p-3 text-center">
            <p className="text-[10px] text-gray-500 mb-1">{s.label}</p>
            <p className="text-sm font-bold text-white">{s.value}</p>
          </div>
        ))}
      </div>

      {/* Progress bar */}
      {operation.progress != null && (
        <div className="h-1.5 bg-surface-200 rounded-full overflow-hidden mb-6">
          <div className="h-full bg-gold rounded-full transition-all" style={{ width: `${operation.progress}%` }} />
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-4 border-b border-surface-200">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2.5 text-xs font-medium transition-all border-b-2 -mb-px ${
              tab === t.id ? 'border-gold text-gold' : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'client' && (
        <div className="space-y-2">
          {operation.clientDocs
            ? operation.clientDocs.map((doc, i) => {
                const st = STATUS_CONFIG[doc.status] || STATUS_CONFIG.pendente
                return (
                  <div key={i} className="card-hover p-4 flex items-center gap-4">
                    <FileText size={18} className="text-gray-500 flex-shrink-0" />
                    <div className="flex-1">
                      <p className="text-sm text-gray-200">{doc.name}</p>
                      <p className="text-[10px] text-gray-500">{doc.type} · {doc.date || 'Nao recebido'}</p>
                    </div>
                    <span className={st.cls}>{st.label}</span>
                    {doc.status !== 'pendente' && <button className="btn-ghost p-1"><Eye size={14} /></button>}
                  </div>
                )
              })
            : DOC_CHECKLIST.map(doc => {
                const isPending = operation.pendingDocs?.includes(doc.label)
                const st = isPending ? STATUS_CONFIG.pendente : STATUS_CONFIG.analisado
                return (
                  <div key={doc.id} className="card-hover p-4 flex items-center gap-4">
                    <FileText size={18} className="text-gray-500 flex-shrink-0" />
                    <div className="flex-1">
                      <p className="text-sm text-gray-200">{doc.label}</p>
                      <p className="text-[10px] text-gray-500">{doc.required ? 'Obrigatorio' : 'Opcional'}</p>
                    </div>
                    <span className={st.cls}>{st.label}</span>
                  </div>
                )
              })
          }
        </div>
      )}

      {tab === 'agent' && (
        <div className="space-y-2">
          {(operation.agentDocs || []).length === 0 ? (
            <p className="text-sm text-gray-500 py-8 text-center">Aguardando outputs dos agentes — pipeline em andamento.</p>
          ) : operation.agentDocs.map((doc, i) => {
            const st = STATUS_CONFIG[doc.status] || STATUS_CONFIG.rascunho
            const agent = AGENTS.find(a => a.id === doc.agent)
            return (
              <div key={i} className="card-hover p-4 flex items-center gap-4">
                <FileText size={18} className="text-gold flex-shrink-0" />
                <div className="flex-1">
                  <p className="text-sm text-gray-200">{doc.name}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-[10px]" style={{ color: agent?.color }}>{agent?.name?.split(' ')[0]}</span>
                    <span className="text-[10px] text-gray-500">· {doc.version} · {doc.date}</span>
                  </div>
                </div>
                <span className={st.cls}>{st.label}</span>
                <button className="btn-ghost p-1"><Download size={14} /></button>
              </div>
            )
          })}
        </div>
      )}

      {tab === 'timeline' && (
        <div className="relative pl-6 space-y-0">
          {(operation.timeline || [{ date: operation.openedAt || operation.openDate, event: 'Projeto aberto no pipeline', agent: 'md_orchestrator' }]).map((evt, i) => {
            const agent = AGENTS.find(a => a.id === evt.agent)
            return (
              <div key={i} className="relative pb-6 last:pb-0">
                {i < operation.timeline.length - 1 && (
                  <div className="absolute left-[-17px] top-3 w-px h-full bg-surface-200" />
                )}
                <div className="absolute left-[-20px] top-1.5 w-2 h-2 rounded-full border-2 border-gold bg-surface" />
                <div>
                  <p className="text-xs text-gray-500 mb-0.5">{evt.date}</p>
                  <p className="text-sm text-gray-200">{evt.event}</p>
                  <p className="text-[10px] mt-0.5" style={{ color: agent?.color }}>{agent?.name}</p>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

function ProposalPreview({ proposal, onClose }) {
  const roman = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII']
  const rows = [
    ['Emissor', proposal.emissor],
    ['Instrumento', proposal.instrumento],
    ['Volume', `${proposal.moeda} ${proposal.volume}`],
    ['Prazo', proposal.prazo || 'A definir'],
    ['Taxa / Spread', proposal.taxa || 'A definir'],
    ['Regime de Colocação', proposal.regime],
    ['Público Alvo', proposal.publicoAlvo?.join(', ') || 'A definir'],
    ['Destinação de Recursos', proposal.destinacao || '—'],
    ['Comissionamento', `Fee de sucesso de ${proposal.comissionamento}, pago na liquidação`],
    ...(proposal.coberturaFX ? [['Cobertura FX', proposal.coberturaFX]] : []),
    ['Vencimento Antecipado', proposal.vencimentoAntecipado],
    ['Resgate Antecipado', proposal.resgateAntecipado],
    ...(proposal.outrasCondicoes ? [['Outras Condições', proposal.outrasCondicoes]] : []),
  ]

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[100] flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-surface-50 border border-surface-200 rounded-xl w-full max-w-2xl max-h-[85vh] flex flex-col" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-5 border-b border-surface-200 flex-shrink-0">
          <div>
            <p className="text-[10px] text-gold uppercase tracking-wider font-medium mb-0.5">Term Sheet Indicativo — Estritamente Confidencial</p>
            <h3 className="text-base font-bold text-white">{proposal.emissor}</h3>
            <p className="text-xs text-gray-500 mt-0.5">{proposal.instrumento} · {proposal.tipoOperacao} · Emitido em {new Date(proposal.createdAt).toLocaleDateString('pt-BR')}</p>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white p-1"><X size={18} /></button>
        </div>

        <div className="flex-1 overflow-y-auto p-5">
          <div className="border border-surface-200 rounded-lg overflow-hidden mb-4">
            <div className="divide-y divide-surface-200/50">
              {rows.map(([label, value]) => (
                <div key={label} className="flex px-4 py-2.5 gap-4">
                  <span className="text-xs text-gray-500 w-44 flex-shrink-0">{label}</span>
                  <span className="text-xs text-gray-200 flex-1 leading-relaxed">{value}</span>
                </div>
              ))}
              {proposal.garantias?.length > 0 && (
                <div className="flex px-4 py-2.5 gap-4">
                  <span className="text-xs text-gray-500 w-44 flex-shrink-0">Garantias Disponíveis</span>
                  <div className="flex-1 space-y-1">
                    {proposal.garantias.map((g, i) => (
                      <p key={i} className="text-xs text-gray-200">
                        {roman[i] || `${i+1}.`}. {g.tipo}{g.descricao ? ` — ${g.descricao}` : ''}
                        {g.fileName && <span className="text-accent-blue ml-1.5 text-[10px]">({g.fileName})</span>}
                      </p>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="p-3 bg-gold/5 border border-gold/20 rounded-lg">
            <p className="text-[11px] text-gray-400 leading-relaxed">
              <strong className="text-gold">Aviso Legal:</strong> Todos os termos e condições expostos estão sujeitos à aprovação pelos comitês internos da Gennesys,
              os quais poderão promover quaisquer alterações nas informações indicativas ora apresentadas.
              Este documento é estritamente confidencial e não poderá ser divulgado sem autorização expressa.
            </p>
          </div>
        </div>

        <div className="flex justify-end gap-2 p-4 border-t border-surface-200 flex-shrink-0">
          <button onClick={onClose} className="btn-ghost text-xs">Fechar</button>
          <button
            onClick={() => window.print()}
            className="btn-primary flex items-center gap-2 text-xs"
          >
            <Download size={13} /> Exportar
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Operations() {
  const { state } = useApp()
  const [selected, setSelected] = useState(null)
  const [showTermSheet, setShowTermSheet] = useState(false)
  const [termSheetOp, setTermSheetOp] = useState('')
  const [activeTab, setActiveTab] = useState('operations')
  const [previewProposal, setPreviewProposal] = useState(null)

  const openTermSheet = (e, opName = '') => {
    e.stopPropagation()
    setTermSheetOp(opName)
    setShowTermSheet(true)
  }

  if (selected) {
    return (
      <>
        <OperationDetail operation={selected} onBack={() => setSelected(null)} onTermSheet={openTermSheet} />
        {showTermSheet && <TermSheetModal onClose={() => setShowTermSheet(false)} operationName={termSheetOp} />}
      </>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-white font-editorial">Operacoes & Documentos</h2>
        <button onClick={e => openTermSheet(e)} className="btn-primary flex items-center gap-2 text-xs">
          <FileSignature size={14} /> Emitir Proposta
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-5 border-b border-surface-200">
        {[
          { id: 'operations', label: `Operações (${state.operations.length})` },
          { id: 'proposals', label: `Propostas Emitidas (${state.proposals.length})` },
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`px-4 py-2.5 text-xs font-medium transition-all border-b-2 -mb-px ${
              activeTab === t.id ? 'border-gold text-gold' : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {showTermSheet && <TermSheetModal onClose={() => setShowTermSheet(false)} operationName={termSheetOp} />}
      {previewProposal && <ProposalPreview proposal={previewProposal} onClose={() => setPreviewProposal(null)} />}

      {/* Propostas tab */}
      {activeTab === 'proposals' && (
        <div>
          {state.proposals.length === 0 ? (
            <div className="text-center py-16">
              <FileSignature size={32} className="mx-auto text-gray-600 mb-3" />
              <p className="text-sm text-gray-400">Nenhuma proposta emitida ainda.</p>
              <p className="text-xs text-gray-500 mt-1">Clique em "Emitir Proposta" para gerar um Term Sheet.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {state.proposals.map(p => (
                <div key={p.id} className="card-hover p-4 flex items-center gap-4 cursor-pointer" onClick={() => setPreviewProposal(p)}>
                  <div className="w-9 h-9 rounded-lg bg-gold/15 flex items-center justify-center flex-shrink-0">
                    <FileSignature size={16} className="text-gold" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">Term Sheet — {p.emissor}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-[10px] text-gray-500">{p.instrumento}</span>
                      <span className="text-[10px] text-gray-600">·</span>
                      <span className="text-[10px] text-gray-500">{p.moeda} {p.volume}</span>
                      <span className="text-[10px] text-gray-600">·</span>
                      <span className="text-[10px] text-gray-500">{new Date(p.createdAt).toLocaleDateString('pt-BR')}</span>
                    </div>
                  </div>
                  {p.garantias?.length > 0 && (
                    <span className="badge bg-surface-200 text-gray-400">{p.garantias.length} garantia{p.garantias.length > 1 ? 's' : ''}</span>
                  )}
                  <span className="badge badge-green">Emitido</span>
                  <Eye size={14} className="text-gray-400 flex-shrink-0" />
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Operations tab */}
      {activeTab === 'operations' && <div className="space-y-3">
        {state.operations.length === 0 && (
          <div className="text-center py-16">
            <FileText size={32} className="mx-auto text-gray-600 mb-3" />
            <p className="text-sm text-gray-400">Nenhuma operacao aberta ainda.</p>
            <p className="text-xs text-gray-500 mt-1">Abra um novo projeto em "Abertura de Projetos".</p>
          </div>
        )}
        {state.operations.map(op => {
          const lead = AGENTS.find(a => a.id === (op.leadAgent || 'md_orchestrator'))
          return (
            <div
              key={op.id}
              onClick={() => setSelected(op)}
              className="card-hover p-5 cursor-pointer flex items-center gap-5"
            >
              <div className="flex-shrink-0 w-14 text-center">
                <span className={`badge ${op.type === 'DCM' ? 'badge-blue' : 'badge-green'}`}>{op.type}</span>
                <p className="text-[10px] text-gray-500 mt-1">{op.instrument}</p>
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-bold text-white">{op.name}</h3>
                <p className="text-xs text-gray-400 mt-0.5">{op.company} · {op.sector}</p>
              </div>
              <div className="text-right flex-shrink-0">
                <p className="text-sm font-bold text-gold">{BRL_COMPACT(op.value)}</p>
                <p className="text-[10px] text-gray-500">Target: {op.targetDate}</p>
              </div>
              <div className="w-24 flex-shrink-0">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] text-gray-500">Progresso</span>
                  <span className="text-[10px] text-gold font-bold">{op.progress}%</span>
                </div>
                <div className="h-1.5 bg-surface-200 rounded-full overflow-hidden">
                  <div className="h-full bg-gold rounded-full" style={{ width: `${op.progress}%` }} />
                </div>
              </div>
              <ChevronRight size={16} className="text-gray-600 flex-shrink-0" />
            </div>
          )
        })}
      </div>}
    </div>
  )
}
