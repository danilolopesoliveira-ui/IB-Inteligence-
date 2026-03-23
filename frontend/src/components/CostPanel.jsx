import { useState, useEffect } from 'react'
import { AGENTS, OPERATIONS, COST_HISTORY, COST_BY_OPERATION, BRL, BRL_COMPACT, PCT } from '../data/mockData'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts'
import { AlertTriangle, RefreshCw, Wifi, WifiOff } from 'lucide-react'

const COST_API_URL = import.meta.env.VITE_API_URL || ''

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-surface-50 border border-surface-200 rounded-lg px-3 py-2 text-xs shadow-xl">
      <p className="text-gray-400 mb-1">{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }} className="font-medium">{p.name}: {BRL(p.value)}</p>
      ))}
    </div>
  )
}

export default function CostPanel() {
  const [liveData, setLiveData] = useState(null)
  const [isLive, setIsLive] = useState(false)
  const [loading, setLoading] = useState(false)

  const fetchLive = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${COST_API_URL}/api/costs`)
      if (!res.ok) throw new Error('API offline')
      const data = await res.json()
      setLiveData(data)
      setIsLive(true)
    } catch {
      setIsLive(false)
    }
    setLoading(false)
  }

  useEffect(() => { fetchLive() }, [])

  // -- Data source: live API or mock fallback --
  const hasLiveAgents = isLive && liveData?.by_agent?.length > 0

  const agentCosts = hasLiveAgents
    ? liveData.by_agent.map(a => ({
        name: a.agent_name.split(' ')[0],
        fullName: a.agent_name,
        hours: a.hours_logged,
        costHour: a.total_cost_brl / Math.max(a.total_calls, 1),
        total: a.total_cost_brl,
        tokens: a.total_tokens,
        calls: a.total_calls,
        color: AGENTS.find(ag => ag.id === a.agent_id)?.color || '#d4a853',
      }))
    : AGENTS.map(a => ({
        name: a.name.split(' ')[0],
        fullName: a.name,
        hours: a.hoursLogged,
        costHour: a.costPerHour,
        total: a.hoursLogged * a.costPerHour,
        tokens: 0,
        calls: 0,
        color: a.color,
      }))

  const totalCost = agentCosts.reduce((s, a) => s + a.total, 0)

  const opCosts = hasLiveAgents && liveData.by_operation?.length > 0
    ? liveData.by_operation.map(o => ({
        id: o.operation_id,
        name: o.name,
        type: 'DCM',
        sector: '',
        value: 0,
        totalCost: o.total_cost_brl,
        costPer100M: 0,
        tokens: o.total_tokens,
        calls: o.total_calls,
      }))
    : OPERATIONS.map(op => {
        const c = COST_BY_OPERATION.find(x => x.operationId === op.id)
        return { ...op, totalCost: c?.totalCost || 0, costPer100M: c?.costPer100M || 0 }
      })

  const timelineData = hasLiveAgents && liveData.timeline?.length > 0
    ? liveData.timeline.map(d => ({ month: d.date, real: d.cost_brl, projected: 0 }))
    : COST_HISTORY

  const session = liveData?.current_session || {}
  const threshold = 55000
  const latestProjected = timelineData[timelineData.length - 1]?.projected || 0
  const overBudget = latestProjected > threshold

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-xl font-bold text-white font-editorial">Painel de Custos</h2>
        <div className="flex items-center gap-3">
          {isLive ? (
            <span className="flex items-center gap-1.5 text-[10px] text-accent-green font-medium">
              <Wifi size={12} /> API Conectada — Dados Reais
            </span>
          ) : (
            <span className="flex items-center gap-1.5 text-[10px] text-gray-500 font-medium">
              <WifiOff size={12} /> Dados Mock (API offline)
            </span>
          )}
          <button onClick={fetchLive} className="btn-ghost p-1.5" title="Atualizar">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>
      <p className="text-xs text-gray-500 mb-6">
        Monitoramento de custos por agente e operacao — valores em R$
        {isLive && session.usd_brl_rate && ` · Cambio: USD/BRL ${session.usd_brl_rate}`}
      </p>

      {/* Live session banner */}
      {isLive && session.status === 'running' && (
        <div className="card p-4 mb-6 border-gold/30 bg-gold/5">
          <div className="flex items-center gap-3">
            <span className="w-2 h-2 bg-gold rounded-full animate-pulse" />
            <div>
              <p className="text-sm font-medium text-gold">{session.name || 'Sessao em andamento'}</p>
              <p className="text-[10px] text-gray-400">
                {session.total_calls || 0} chamadas · {(session.total_tokens || 0).toLocaleString('pt-BR')} tokens · R$ {(session.total_cost_brl || 0).toFixed(2)}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* A) Custo por Agente */}
      <div className="mb-8">
        <p className="section-title">Custo por Agente</p>
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          <div className="card p-4 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-200 text-xs text-gray-500">
                  <th className="text-left py-2 font-medium">Agente</th>
                  {hasLiveAgents && <th className="text-right py-2 font-medium">Chamadas</th>}
                  {hasLiveAgents && <th className="text-right py-2 font-medium">Tokens</th>}
                  {!hasLiveAgents && <th className="text-right py-2 font-medium">Horas</th>}
                  <th className="text-right py-2 font-medium">Total (R$)</th>
                  <th className="text-right py-2 font-medium">% Total</th>
                </tr>
              </thead>
              <tbody>
                {agentCosts.map(a => (
                  <tr key={a.name} className="border-b border-surface-200/50 hover:bg-surface-100 transition-colors">
                    <td className="py-2.5 flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full" style={{ background: a.color }} />
                      <span className="text-gray-200 text-xs">{a.fullName}</span>
                    </td>
                    {hasLiveAgents && <td className="text-right text-gray-300 text-xs">{a.calls}</td>}
                    {hasLiveAgents && <td className="text-right text-gray-300 text-xs">{a.tokens.toLocaleString('pt-BR')}</td>}
                    {!hasLiveAgents && <td className="text-right text-gray-300 text-xs">{a.hours}h</td>}
                    <td className="text-right text-white font-semibold text-xs">{BRL(a.total)}</td>
                    <td className="text-right text-gray-400 text-xs">{totalCost > 0 ? PCT((a.total / totalCost) * 100) : '—'}</td>
                  </tr>
                ))}
                <tr className="font-bold">
                  <td className="py-2.5 text-gold text-xs">Total</td>
                  {hasLiveAgents && <td className="text-right text-gold text-xs">{agentCosts.reduce((s, a) => s + a.calls, 0)}</td>}
                  {hasLiveAgents && <td className="text-right text-gold text-xs">{agentCosts.reduce((s, a) => s + a.tokens, 0).toLocaleString('pt-BR')}</td>}
                  {!hasLiveAgents && <td className="text-right text-gold text-xs">{agentCosts.reduce((s, a) => s + a.hours, 0)}h</td>}
                  <td className="text-right text-gold text-xs">{BRL(totalCost)}</td>
                  <td className="text-right text-gold text-xs">100%</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="card p-4">
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={agentCosts} layout="vertical" margin={{ left: 10, right: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3e" />
                <XAxis type="number" tickFormatter={v => `R$${(v / 1000).toFixed(0)}K`} tick={{ fill: '#6b7280', fontSize: 11 }} />
                <YAxis type="category" dataKey="name" tick={{ fill: '#9ca3af', fontSize: 11 }} width={70} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="total" radius={[0, 4, 4, 0]} barSize={18}>
                  {agentCosts.map((a, i) => <Cell key={i} fill={a.color} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* B) Custo por Operacao */}
      <div className="mb-8">
        <p className="section-title">Custo por Operacao</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {opCosts.map(op => (
            <div key={op.id} className="card-hover p-5">
              <div className="flex items-center justify-between mb-3">
                <span className={`badge ${op.type === 'DCM' ? 'badge-blue' : 'badge-green'}`}>{op.type}</span>
                <span className="text-[10px] text-gray-500">{op.sector}</span>
              </div>
              <h4 className="text-sm font-bold text-white mb-3">{op.name}</h4>
              <div className="space-y-2 text-xs">
                {op.value > 0 && <div className="flex justify-between"><span className="text-gray-400">Valor Analisado</span><span className="text-white font-medium">{BRL_COMPACT(op.value)}</span></div>}
                <div className="flex justify-between"><span className="text-gray-400">Custo Total Agentes</span><span className="text-gold font-medium">{BRL(op.totalCost)}</span></div>
                {op.tokens > 0 && <div className="flex justify-between"><span className="text-gray-400">Tokens</span><span className="text-white font-medium">{op.tokens.toLocaleString('pt-BR')}</span></div>}
                {op.costPer100M > 0 && <div className="flex justify-between"><span className="text-gray-400">Custo / R$ 100M</span><span className="text-white font-medium">{BRL(op.costPer100M)}</span></div>}
                {op.value > 0 && (
                  <div className="flex justify-between border-t border-surface-200 pt-2 mt-2">
                    <span className="text-gray-400">Margem Estimada</span>
                    <span className="text-accent-green font-bold">{PCT(100 - (op.totalCost / op.value) * 100)}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* C) Projecao de Custos */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <p className="section-title mb-0">Projecao de Custos</p>
          {overBudget && <span className="badge-red flex items-center gap-1"><AlertTriangle size={10} /> Acima do threshold</span>}
        </div>
        <div className="card p-5">
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={timelineData} margin={{ left: 10, right: 20, top: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3e" />
              <XAxis dataKey="month" tick={{ fill: '#6b7280', fontSize: 11 }} />
              <YAxis tickFormatter={v => `R$${(v / 1000).toFixed(0)}K`} tick={{ fill: '#6b7280', fontSize: 11 }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 11, color: '#9ca3af' }} />
              <Line type="monotone" dataKey="real" stroke="#d4a853" strokeWidth={2} dot={{ r: 3, fill: '#d4a853' }} name="Custo Real" />
              {timelineData.some(d => d.projected > 0) && (
                <Line type="monotone" dataKey="projected" stroke="#3b82f6" strokeWidth={2} strokeDasharray="5 5" dot={{ r: 3, fill: '#3b82f6' }} name="Projetado" />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Model pricing reference */}
      {isLive && liveData?.model_pricing && (
        <div className="mt-6">
          <p className="section-title">Tabela de Precos por Modelo</p>
          <div className="card p-4">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-surface-200 text-gray-500">
                  <th className="text-left py-2 font-medium">Modelo</th>
                  <th className="text-right py-2 font-medium">Input (USD/1M tokens)</th>
                  <th className="text-right py-2 font-medium">Output (USD/1M tokens)</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(liveData.model_pricing).map(([model, pricing]) => (
                  <tr key={model} className="border-b border-surface-200/50">
                    <td className="py-2 text-gray-300 font-mono">{model}</td>
                    <td className="py-2 text-right text-gray-300">${pricing.input.toFixed(2)}</td>
                    <td className="py-2 text-right text-gray-300">${pricing.output.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
