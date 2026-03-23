import { useState } from 'react'
import { useApp } from '../context/AppContext'
import { INSTITUTIONS, FUNDS, OPERATIONS, BRL_COMPACT, BRL } from '../data/mockData'
import { Plus, X, Upload, Search, Building2, Landmark, TrendingUp, Shield, ChevronDown, FileText, Zap } from 'lucide-react'

function InstitutionModal({ onClose }) {
  const { toast } = useApp()
  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100] flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-surface-50 border border-surface-200 rounded-xl w-full max-w-lg p-6 max-h-[85vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-lg font-bold text-white">Nova Instituicao Financeira</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-white"><X size={18} /></button>
        </div>
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div><label className="text-xs text-gray-400 mb-1 block">Nome</label><input className="input-field" placeholder="Ex: Itau Asset" /></div>
            <div><label className="text-xs text-gray-400 mb-1 block">Tipo</label>
              <select className="input-field"><option>Asset</option><option>Banco</option><option>Family Office</option><option>Fundo de Pensao</option><option>Seguradora</option></select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="text-xs text-gray-400 mb-1 block">AUM (R$)</label><input className="input-field" placeholder="Ex: 50000000000" /></div>
            <div><label className="text-xs text-gray-400 mb-1 block">Ticket Medio (R$)</label><input className="input-field" placeholder="Ex: 50000000" /></div>
          </div>
          <div><label className="text-xs text-gray-400 mb-1 block">Perfil de Risco</label>
            <select className="input-field"><option>Conservador</option><option>Moderado</option><option>Agressivo</option></select>
          </div>
          <div><label className="text-xs text-gray-400 mb-1 block">Setores de Interesse</label><input className="input-field" placeholder="Energia, Agro, Infraestrutura..." /></div>
          <div><label className="text-xs text-gray-400 mb-1 block">Instrumentos</label><input className="input-field" placeholder="Debentures, CRI, CRA, Acoes..." /></div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="text-xs text-gray-400 mb-1 block">Rating Minimo</label><input className="input-field" placeholder="AA-" /></div>
            <div><label className="text-xs text-gray-400 mb-1 block">Duration Maxima</label><input className="input-field" placeholder="7 anos" /></div>
          </div>
          <div><label className="text-xs text-gray-400 mb-1 block">Contato Principal</label><input className="input-field" placeholder="Nome — Cargo" /></div>
        </div>
        <div className="flex justify-end gap-2 mt-5">
          <button onClick={onClose} className="btn-ghost">Cancelar</button>
          <button onClick={() => { toast('Instituicao cadastrada', 'info'); onClose() }} className="btn-primary">Cadastrar</button>
        </div>
      </div>
    </div>
  )
}

function FundXRay({ fund }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="card-hover p-4">
      <div className="flex items-center justify-between cursor-pointer" onClick={() => setOpen(!open)}>
        <div>
          <h4 className="text-sm font-bold text-white">{fund.name}</h4>
          <p className="text-[10px] text-gray-500">{fund.manager} · PL: {BRL_COMPACT(fund.pl)}</p>
        </div>
        <ChevronDown size={16} className={`text-gray-500 transition-transform ${open ? 'rotate-180' : ''}`} />
      </div>
      {open && (
        <div className="mt-3 pt-3 border-t border-surface-200 space-y-2 text-xs">
          <p className="text-gray-400"><span className="text-gray-500 font-medium">Mandato:</span> {fund.mandate}</p>
          <div className="grid grid-cols-2 gap-2">
            <p><span className="text-gray-500">Perfil:</span> <span className={fund.riskProfile === 'Conservador' ? 'text-accent-green' : fund.riskProfile === 'Agressivo' ? 'text-accent-red' : 'text-gold'}>{fund.riskProfile}</span></p>
            <p><span className="text-gray-500">Concentracao Max:</span> <span className="text-gray-300">{fund.maxConcentration}</span></p>
            <p><span className="text-gray-500">Benchmark:</span> <span className="text-gray-300">{fund.benchmark}</span></p>
            <p><span className="text-gray-500">Rating Min:</span> <span className="text-gray-300">{fund.ratingMin}</span></p>
          </div>
          <div>
            <span className="text-gray-500">Setores Permitidos:</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {fund.sectorsAllowed.map(s => <span key={s} className="badge badge-green">{s}</span>)}
            </div>
          </div>
          {fund.sectorsBlocked.length > 0 && (
            <div>
              <span className="text-gray-500">Setores Vedados:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {fund.sectorsBlocked.map(s => <span key={s} className="badge badge-red">{s}</span>)}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function DistributionReport() {
  const { toast } = useApp()
  const [selectedOp, setSelectedOp] = useState(OPERATIONS[0]?.id)
  const [generated, setGenerated] = useState(false)

  const op = OPERATIONS.find(o => o.id === selectedOp)

  const scoreInstitution = (inst) => {
    let score = 50
    if (op?.sector && inst.preferences.sectors.some(s => s === 'Multi-setor' || op.sector.includes(s))) score += 20
    if (op?.instrument && inst.preferences.instruments.includes(op.instrument)) score += 15
    if (inst.riskProfile === 'Moderado') score += 5
    if (inst.riskProfile === 'Agressivo') score += 10
    return Math.min(score, 98)
  }

  const ranked = [...INSTITUTIONS].map(i => ({ ...i, score: scoreInstitution(i) })).sort((a, b) => b.score - a.score)

  return (
    <div className="mt-8">
      <p className="section-title">Relatorio de Potenciais Investidores</p>
      <div className="flex items-center gap-3 mb-4">
        <select className="input-field w-64" value={selectedOp} onChange={e => setSelectedOp(e.target.value)}>
          {OPERATIONS.map(o => <option key={o.id} value={o.id}>{o.name}</option>)}
        </select>
        <button className="btn-primary flex items-center gap-2" onClick={() => { setGenerated(true); toast('Relatorio gerado', 'info') }}>
          <Zap size={14} /> Gerar Relatorio
        </button>
      </div>
      {generated && (
        <div className="space-y-2">
          {ranked.map((inst, i) => (
            <div key={inst.id} className="card-hover p-4 flex items-center gap-4">
              <span className="text-sm font-bold text-gold w-6">#{i + 1}</span>
              <div className="flex-1">
                <p className="text-sm font-medium text-white">{inst.name}</p>
                <p className="text-[10px] text-gray-500">{inst.type} · AUM: {BRL_COMPACT(inst.aum)} · {inst.contact}</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-bold" style={{ color: inst.score > 80 ? '#10b981' : inst.score > 60 ? '#d4a853' : '#9ca3af' }}>
                  {inst.score}%
                </p>
                <p className="text-[10px] text-gray-500">Aderencia</p>
              </div>
              <div className="text-right">
                <p className="text-xs font-medium text-gray-300">{BRL_COMPACT(inst.ticketMedio)}</p>
                <p className="text-[10px] text-gray-500">Ticket Sugerido</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function Distribution() {
  const [tab, setTab] = useState('institutions')
  const [showAdd, setShowAdd] = useState(false)

  return (
    <div>
      <h2 className="text-xl font-bold text-white font-editorial mb-1">Distribuicao & Investidores</h2>
      <p className="text-xs text-gray-500 mb-5">Base de {INSTITUTIONS.length} instituicoes financeiras cadastradas</p>

      <div className="flex gap-1 mb-5 border-b border-surface-200">
        {[
          { id: 'institutions', label: 'Instituicoes Financeiras' },
          { id: 'funds', label: 'Analise de Fundos' },
          { id: 'report', label: 'Relatorio de Distribuicao' },
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2.5 text-xs font-medium border-b-2 -mb-px transition-all ${
              tab === t.id ? 'border-gold text-gold' : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'institutions' && (
        <div>
          <div className="flex justify-end mb-3">
            <button className="btn-primary flex items-center gap-2" onClick={() => setShowAdd(true)}>
              <Plus size={14} /> Nova Instituicao
            </button>
          </div>
          <div className="card overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-surface-200 text-gray-500">
                  <th className="text-left p-3 font-medium">Nome</th>
                  <th className="text-left p-3 font-medium">Tipo</th>
                  <th className="text-right p-3 font-medium">AUM</th>
                  <th className="text-right p-3 font-medium">Ticket Medio</th>
                  <th className="text-center p-3 font-medium">Perfil</th>
                  <th className="text-left p-3 font-medium">Instrumentos</th>
                  <th className="text-left p-3 font-medium">Contato</th>
                </tr>
              </thead>
              <tbody>
                {INSTITUTIONS.map(inst => (
                  <tr key={inst.id} className="border-b border-surface-200/50 hover:bg-surface-100 transition-colors">
                    <td className="p-3 text-gray-200 font-medium">{inst.name}</td>
                    <td className="p-3 text-gray-400">{inst.type}</td>
                    <td className="p-3 text-right text-white font-medium">{BRL_COMPACT(inst.aum)}</td>
                    <td className="p-3 text-right text-gray-300">{BRL_COMPACT(inst.ticketMedio)}</td>
                    <td className="p-3 text-center">
                      <span className={`badge ${inst.riskProfile === 'Conservador' ? 'badge-green' : inst.riskProfile === 'Agressivo' ? 'badge-red' : 'badge-gold'}`}>
                        {inst.riskProfile}
                      </span>
                    </td>
                    <td className="p-3">
                      <div className="flex flex-wrap gap-1">
                        {inst.preferences.instruments.slice(0, 3).map(i => (
                          <span key={i} className="badge bg-surface-200 text-gray-400">{i}</span>
                        ))}
                      </div>
                    </td>
                    <td className="p-3 text-gray-400 text-[10px]">{inst.contact}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {showAdd && <InstitutionModal onClose={() => setShowAdd(false)} />}
        </div>
      )}

      {tab === 'funds' && (
        <div className="space-y-3">
          <div className="flex justify-end mb-2">
            <button className="btn-primary flex items-center gap-2">
              <Plus size={14} /> Inserir Fundo
            </button>
          </div>
          {FUNDS.map(f => <FundXRay key={f.id} fund={f} />)}
        </div>
      )}

      {tab === 'report' && <DistributionReport />}
    </div>
  )
}
