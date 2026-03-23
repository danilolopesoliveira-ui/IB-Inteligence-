import { useState } from 'react'
import { useApp } from '../context/AppContext'
import { AGENTS, OPERATIONS, KANBAN_COLUMNS } from '../data/mockData'
import { Clock, AlertTriangle, GripVertical, X, MessageCircle, Play, CheckCircle, AlertOctagon, ArrowUpRight, ShieldAlert, Zap } from 'lucide-react'

const DIFFICULTY_COLORS = ['#10b981', '#10b981', '#f59e0b', '#ef4444', '#dc2626']

const LOG_TYPE_CONFIG = {
  assign:     { icon: ArrowUpRight, color: '#d4a853', label: 'Atribuicao' },
  start:      { icon: Play, color: '#3b82f6', label: 'Inicio' },
  progress:   { icon: Zap, color: '#10b981', label: 'Progresso' },
  message:    { icon: MessageCircle, color: '#8b5cf6', label: 'Mensagem' },
  review:     { icon: CheckCircle, color: '#d4a853', label: 'Revisao' },
  approve:    { icon: CheckCircle, color: '#10b981', label: 'Aprovacao' },
  alert:      { icon: AlertTriangle, color: '#ef4444', label: 'Alerta' },
  blocked:    { icon: AlertOctagon, color: '#ef4444', label: 'Bloqueio' },
  escalation: { icon: ShieldAlert, color: '#f59e0b', label: 'Escalacao' },
}

function formatDateTime(isoStr) {
  const d = new Date(isoStr)
  return d.toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function formatDate(isoStr) {
  return new Date(isoStr).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })
}

function DifficultyDots({ level }) {
  return (
    <div className="flex gap-0.5">
      {[1,2,3,4,5].map(i => (
        <div key={i} className="w-1.5 h-1.5 rounded-full" style={{ background: i <= level ? DIFFICULTY_COLORS[level-1] : '#2a2a3e' }} />
      ))}
    </div>
  )
}

// ── Task Detail Modal ────────────────────────────────────────────────────────

function TaskDetailModal({ task, onClose }) {
  const agent = AGENTS.find(a => a.id === task.agent)
  const operation = OPERATIONS.find(o => o.id === task.operation)
  const log = task.log || []

  // Group log entries by date
  const grouped = {}
  log.forEach(entry => {
    const day = entry.time.slice(0, 10)
    if (!grouped[day]) grouped[day] = []
    grouped[day].push(entry)
  })

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[100] flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-surface-50 border border-surface-200 rounded-xl w-full max-w-2xl max-h-[85vh] flex flex-col" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="p-5 border-b border-surface-200 flex-shrink-0">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold text-white" style={{ background: agent?.color }}>{agent?.avatar}</div>
                <span className="text-xs text-gray-400">{agent?.name}</span>
                <span className={`badge ${operation?.type === 'DCM' ? 'badge-blue' : 'badge-green'}`}>{operation?.type}</span>
                <span className="badge bg-surface-200 text-gray-400">{task.column}</span>
              </div>
              <h3 className="text-base font-bold text-white">{task.title}</h3>
              <p className="text-[11px] text-gray-500 mt-1">{operation?.name} · {operation?.company}</p>
            </div>
            <button onClick={onClose} className="text-gray-500 hover:text-white p-1"><X size={18} /></button>
          </div>

          {/* Stats bar */}
          <div className="flex items-center gap-4 mt-4">
            <div className="flex items-center gap-1.5">
              <DifficultyDots level={task.difficulty} />
              <span className="text-[10px] text-gray-500">Dificuldade {task.difficulty}/5</span>
            </div>
            {task.hoursElapsed > 0 && (
              <div className="flex items-center gap-1.5 text-[11px] text-gray-400">
                <Clock size={11} />
                <span>{task.hoursElapsed}h / {task.maxHours}h</span>
                <div className="w-16 h-1 bg-surface-200 rounded-full overflow-hidden">
                  <div className="h-full rounded-full" style={{
                    width: `${Math.min((task.hoursElapsed / task.maxHours) * 100, 100)}%`,
                    background: task.hoursElapsed > task.maxHours ? '#ef4444' : '#d4a853',
                  }} />
                </div>
              </div>
            )}
            {task.staleHours && <span className="badge-red flex items-center gap-1"><AlertTriangle size={9} /> Parado ha {task.staleHours}h</span>}
            <span className="text-[10px] text-gray-500 ml-auto">{log.length} eventos registrados</span>
          </div>
        </div>

        {/* Timeline / Activity Log */}
        <div className="flex-1 overflow-y-auto p-5">
          {log.length === 0 ? (
            <div className="text-center py-10">
              <MessageCircle size={32} className="mx-auto text-gray-600 mb-3" />
              <p className="text-sm text-gray-500">Nenhuma atividade registrada</p>
              <p className="text-[11px] text-gray-600 mt-1">Esta tarefa ainda nao foi iniciada</p>
            </div>
          ) : (
            <div className="space-y-0">
              {Object.entries(grouped).map(([day, entries]) => (
                <div key={day}>
                  {/* Day header */}
                  <div className="flex items-center gap-3 mb-3 mt-4 first:mt-0">
                    <div className="h-px flex-1 bg-surface-200" />
                    <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">{formatDate(day + 'T00:00:00')}</span>
                    <div className="h-px flex-1 bg-surface-200" />
                  </div>

                  {/* Entries for this day */}
                  <div className="relative pl-8">
                    {/* Vertical line */}
                    <div className="absolute left-[11px] top-0 bottom-0 w-px bg-surface-200" />

                    {entries.map((entry, i) => {
                      const cfg = LOG_TYPE_CONFIG[entry.type] || LOG_TYPE_CONFIG.message
                      const Icon = cfg.icon
                      const entryAgent = AGENTS.find(a => a.id === entry.agent)

                      return (
                        <div key={i} className="relative pb-4 last:pb-1">
                          {/* Dot on timeline */}
                          <div className="absolute left-[-25px] top-1 w-[22px] h-[22px] rounded-full border-2 flex items-center justify-center"
                            style={{ borderColor: cfg.color, background: '#12121a' }}>
                            <Icon size={10} style={{ color: cfg.color }} />
                          </div>

                          {/* Content */}
                          <div className="card p-3 hover:border-surface-300 transition-colors">
                            <div className="flex items-center gap-2 mb-1.5">
                              <div className="w-5 h-5 rounded-full flex items-center justify-center text-[8px] font-bold text-white"
                                style={{ background: entryAgent?.color || '#666' }}>
                                {entryAgent?.avatar || '?'}
                              </div>
                              <span className="text-xs font-medium text-gray-300">{entryAgent?.name || entry.agent}</span>
                              <span className="text-[9px] font-medium px-1.5 py-0.5 rounded" style={{ color: cfg.color, background: cfg.color + '15' }}>
                                {cfg.label}
                              </span>
                              <span className="text-[10px] text-gray-600 ml-auto">
                                {new Date(entry.time).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                              </span>
                            </div>
                            <p className="text-xs text-gray-300 leading-relaxed">{entry.text}</p>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Task Card ────────────────────────────────────────────────────────────────

function TaskCard({ task, onClick }) {
  const agent = AGENTS.find(a => a.id === task.agent)
  const operation = OPERATIONS.find(o => o.id === task.operation)
  const isStale = task.staleHours && task.staleHours > 24
  const hasLog = task.log && task.log.length > 0

  return (
    <div
      draggable
      onDragStart={(e) => e.dataTransfer.setData('taskId', task.id)}
      onClick={() => onClick(task)}
      className="card-hover p-3.5 cursor-pointer active:cursor-grabbing group"
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-full flex items-center justify-center text-[9px] font-bold text-white flex-shrink-0"
            style={{ background: agent?.color || '#666' }}>{agent?.avatar}</div>
          <span className="text-xs text-gray-400">{agent?.name?.split(' ')[0]}</span>
        </div>
        <div className="flex items-center gap-1.5">
          {isStale && <AlertTriangle size={13} className="text-accent-red" />}
          {hasLog && (
            <span className="flex items-center gap-0.5 text-[9px] text-gray-500">
              <MessageCircle size={10} /> {task.log.length}
            </span>
          )}
          <GripVertical size={14} className="text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>
      </div>

      <p className="text-[13px] font-medium text-gray-200 leading-snug mb-2.5">{task.title}</p>

      <div className="flex items-center justify-between">
        <span className={`badge ${operation?.type === 'DCM' ? 'badge-blue' : 'badge-green'}`}>{operation?.type}</span>
        <DifficultyDots level={task.difficulty} />
      </div>

      {task.hoursElapsed > 0 && (
        <div className="flex items-center gap-1.5 mt-2 text-[11px] text-gray-500">
          <Clock size={11} />
          <span>{task.hoursElapsed}h / {task.maxHours}h</span>
          <div className="flex-1 h-1 bg-surface-200 rounded-full ml-1 overflow-hidden">
            <div className="h-full rounded-full transition-all" style={{
              width: `${Math.min((task.hoursElapsed / task.maxHours) * 100, 100)}%`,
              background: task.hoursElapsed > task.maxHours ? '#ef4444' : '#d4a853',
            }} />
          </div>
        </div>
      )}
    </div>
  )
}

// ── Column ───────────────────────────────────────────────────────────────────

function Column({ name, tasks, onDrop, onTaskClick }) {
  const [isDragOver, setDragOver] = useState(false)
  const columnColors = {
    'Backlog': 'border-gray-600', 'Em Analise': 'border-accent-blue',
    'Em Revisao': 'border-gold', 'Aguardando Cliente': 'border-accent-amber',
    'Concluido': 'border-accent-green',
  }

  return (
    <div
      className={`flex flex-col min-w-[260px] flex-1 transition-colors ${isDragOver ? 'bg-surface-50/50' : ''}`}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => { e.preventDefault(); setDragOver(false); onDrop(e.dataTransfer.getData('taskId'), name) }}
    >
      <div className={`flex items-center gap-2 mb-3 pb-2 border-b-2 ${columnColors[name] || 'border-surface-200'}`}>
        <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400">{name}</h3>
        <span className="text-[10px] font-bold text-gray-500 bg-surface-200 px-1.5 py-0.5 rounded-full">{tasks.length}</span>
      </div>
      <div className="flex flex-col gap-2 flex-1 min-h-[100px]">
        {tasks.map(task => <TaskCard key={task.id} task={task} onClick={onTaskClick} />)}
      </div>
    </div>
  )
}

// ── Main Board ───────────────────────────────────────────────────────────────

export default function KanbanBoard() {
  const { state, dispatch, toast } = useApp()
  const { tasks, filterAgent, filterOperation } = state
  const [selectedTask, setSelectedTask] = useState(null)

  const filteredTasks = tasks.filter(t => {
    if (filterAgent && t.agent !== filterAgent) return false
    if (filterOperation && t.operation !== filterOperation) return false
    return true
  })

  const handleDrop = (taskId, column) => {
    dispatch({ type: 'MOVE_TASK', payload: { taskId, column } })
    toast(`Tarefa movida para "${column}"`, 'info')
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-xl font-bold text-white font-editorial">Kanban Operacional</h2>
          <p className="text-xs text-gray-500 mt-0.5">{filteredTasks.length} tarefas · Clique em um card para ver o historico</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            {AGENTS.map(a => (
              <button key={a.id} onClick={() => dispatch({ type: 'SET_FILTER_AGENT', payload: a.id })}
                className={`w-7 h-7 rounded-full flex items-center justify-center text-[9px] font-bold text-white transition-all ${
                  filterAgent === a.id ? 'ring-2 ring-gold ring-offset-2 ring-offset-surface scale-110' : 'opacity-50 hover:opacity-80'
                }`} style={{ background: a.color }} title={a.name}>{a.avatar}</button>
            ))}
            {filterAgent && <button onClick={() => dispatch({ type: 'SET_FILTER_AGENT', payload: null })} className="btn-ghost text-[10px] ml-1">Limpar</button>}
          </div>
          <div className="flex gap-1 ml-2 border-l border-surface-200 pl-2">
            {OPERATIONS.map(op => (
              <button key={op.id} onClick={() => dispatch({ type: 'SET_FILTER_OPERATION', payload: op.id })}
                className={`px-2 py-1 rounded text-[10px] font-semibold transition-all ${
                  filterOperation === op.id ? 'bg-gold/20 text-gold' : 'text-gray-500 hover:text-gray-300 hover:bg-surface-100'
                }`}>{op.instrument}</button>
            ))}
          </div>
        </div>
      </div>

      {/* Board */}
      <div className="flex gap-4 flex-1 overflow-x-auto pb-4">
        {KANBAN_COLUMNS.map(col => (
          <Column key={col} name={col} tasks={filteredTasks.filter(t => t.column === col)} onDrop={handleDrop} onTaskClick={setSelectedTask} />
        ))}
      </div>

      {/* Detail Modal */}
      {selectedTask && <TaskDetailModal task={selectedTask} onClose={() => setSelectedTask(null)} />}
    </div>
  )
}
