import { useApp } from '../context/AppContext'
import {
  LayoutDashboard, Inbox, KanbanSquare, Users, BookOpen, DollarSign,
  FolderOpen, PieChart, Briefcase, MessageSquare, GraduationCap,
  ChevronLeft, ChevronRight, Sun, Moon, Bell, FileStack,
} from 'lucide-react'

const NAV_ITEMS = [
  { id: 'projects', label: 'Abertura de Projetos', icon: Briefcase, highlight: true },
  { id: 'kanban', label: 'Kanban Operacional', icon: KanbanSquare },
  { id: 'agents', label: 'Estrutura de Agentes', icon: Users },
  { id: 'models', label: 'Modelos', icon: FileStack, badgeKey: 'models' },
  { id: 'knowledge', label: 'Biblioteca de Conhecimento', icon: BookOpen },
  { id: 'costs', label: 'Painel de Custos', icon: DollarSign },
  { id: 'operations', label: 'Operacoes & Documentos', icon: FolderOpen },
  { id: 'distribution', label: 'Distribuicao & Investidores', icon: PieChart },
  { id: 'reviews', label: 'Revisoes & Comunicacao', icon: MessageSquare, badgeKey: 'reviews' },
  { id: 'training', label: 'Treinamento do MD', icon: GraduationCap, badgeKey: 'training' },
]

export default function Sidebar() {
  const { state, dispatch } = useApp()
  const { currentPage, sidebarCollapsed, darkMode, messages, training, mdDemands } = state

  const badges = {
    reviews: messages.reduce((sum, m) => sum + m.unread, 0),
    training: training.filter(t => t.status === 'pendente').length + mdDemands.filter(d => d.status === 'pendente').length,
    models: 0,
  }

  return (
    <aside
      className={`fixed left-0 top-0 h-screen bg-surface border-r border-surface-200 flex flex-col z-50 transition-all duration-300 ${
        sidebarCollapsed ? 'w-[68px]' : 'w-[260px]'
      }`}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 h-16 border-b border-surface-200 flex-shrink-0">
        <div className="w-8 h-8 rounded-lg bg-gold/20 flex items-center justify-center flex-shrink-0">
          <LayoutDashboard size={18} className="text-gold" />
        </div>
        {!sidebarCollapsed && (
          <div className="overflow-hidden">
            <h1 className="text-sm font-bold text-white tracking-wide whitespace-nowrap">IB Intelligence</h1>
            <p className="text-[10px] text-gray-500 uppercase tracking-[0.2em]">DCM / ECM Platform</p>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-4 px-3">
        <div className={`${sidebarCollapsed ? '' : 'mb-2'}`}>
          {!sidebarCollapsed && <p className="section-title px-2 mb-2">Modulos</p>}
          {NAV_ITEMS.map(item => {
            const Icon = item.icon
            const isActive = currentPage === item.id
            const badgeCount = item.badgeKey ? badges[item.badgeKey] : 0
            return (
              <button
                key={item.id}
                onClick={() => dispatch({ type: 'SET_PAGE', payload: item.id })}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg mb-0.5 transition-all duration-150 group relative ${
                  item.highlight && !isActive
                    ? 'bg-gold/15 text-gold border border-gold/30 mb-2'
                    : isActive
                    ? 'bg-gold/10 text-gold'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-surface-100'
                }`}
                title={sidebarCollapsed ? item.label : undefined}
              >
                <Icon size={18} className={`flex-shrink-0 ${isActive ? 'text-gold' : 'text-gray-500 group-hover:text-gray-300'}`} />
                {!sidebarCollapsed && (
                  <>
                    <span className="text-[13px] font-medium truncate">{item.label}</span>
                    {badgeCount > 0 && (
                      <span className="ml-auto bg-accent-red text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full min-w-[18px] text-center">
                        {badgeCount}
                      </span>
                    )}
                  </>
                )}
                {sidebarCollapsed && badgeCount > 0 && (
                  <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-accent-red rounded-full" />
                )}
              </button>
            )
          })}
        </div>
      </nav>

      {/* Footer controls */}
      <div className="border-t border-surface-200 px-3 py-3 flex flex-col gap-2">
        <button
          onClick={() => dispatch({ type: 'TOGGLE_SIDEBAR' })}
          className="btn-ghost flex items-center justify-center gap-2 w-full"
        >
          {sidebarCollapsed ? <ChevronRight size={16} /> : <><ChevronLeft size={16} /><span className="text-xs">Recolher</span></>}
        </button>
      </div>
    </aside>
  )
}
