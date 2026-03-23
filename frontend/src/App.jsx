import { AppProvider, useApp } from './context/AppContext'
import Sidebar from './components/Sidebar'
import KanbanBoard from './components/KanbanBoard'
import AgentStructure from './components/AgentStructure'
import KnowledgeLibrary from './components/KnowledgeLibrary'
import CostPanel from './components/CostPanel'
import Operations from './components/Operations'
import Distribution from './components/Distribution'
import ProjectOpening from './components/ProjectOpening'
import ReviewsComm from './components/ReviewsComm'
import Training from './components/Training'
import ModelTemplates from './components/ModelTemplates'
import { X, CheckCircle, AlertTriangle, Info } from 'lucide-react'

const PAGES = {
  kanban: KanbanBoard,
  agents: AgentStructure,
  models: ModelTemplates,
  knowledge: KnowledgeLibrary,
  costs: CostPanel,
  operations: Operations,
  distribution: Distribution,
  projects: ProjectOpening,
  reviews: ReviewsComm,
  training: Training,
}

function Toast({ toast, onRemove }) {
  const icons = { info: Info, success: CheckCircle, error: AlertTriangle }
  const colors = { info: 'border-accent-blue/30 bg-accent-blue/10', success: 'border-accent-green/30 bg-accent-green/10', error: 'border-accent-red/30 bg-accent-red/10' }
  const iconColors = { info: 'text-accent-blue', success: 'text-accent-green', error: 'text-accent-red' }
  const Icon = icons[toast.type] || Info

  return (
    <div className={`flex items-center gap-3 px-4 py-3 rounded-lg border ${colors[toast.type] || colors.info} backdrop-blur-sm shadow-xl animate-slideIn`}>
      <Icon size={16} className={iconColors[toast.type] || iconColors.info} />
      <span className="text-xs text-gray-200 flex-1">{toast.message}</span>
      <button onClick={() => onRemove(toast.id)} className="text-gray-500 hover:text-white"><X size={14} /></button>
    </div>
  )
}

function Layout() {
  const { state, dispatch } = useApp()
  const PageComponent = PAGES[state.currentPage] || KanbanBoard

  return (
    <div className="h-screen flex overflow-hidden bg-[#0a0a0f]">
      <Sidebar />

      <main
        className="flex-1 overflow-y-auto transition-all duration-300"
        style={{ marginLeft: state.sidebarCollapsed ? 68 : 260 }}
      >
        <div className="p-6 max-w-[1600px] mx-auto h-full">
          <PageComponent />
        </div>
      </main>

      {/* Toasts */}
      {state.toasts.length > 0 && (
        <div className="fixed bottom-6 right-6 z-[200] space-y-2 w-80">
          {state.toasts.map(t => (
            <Toast key={t.id} toast={t} onRemove={id => dispatch({ type: 'REMOVE_TOAST', payload: id })} />
          ))}
        </div>
      )}

      <style>{`
        @keyframes slideIn {
          from { opacity: 0; transform: translateX(20px); }
          to { opacity: 1; transform: translateX(0); }
        }
        .animate-slideIn { animation: slideIn 0.25s ease-out; }
        .line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
      `}</style>
    </div>
  )
}

export default function App() {
  return (
    <AppProvider>
      <Layout />
    </AppProvider>
  )
}
