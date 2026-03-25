import { createContext, useContext, useReducer, useCallback, useEffect } from 'react'
import { TASKS, MESSAGES, AGENTS, TRAINING_RECOMMENDATIONS, MD_DEMANDS, OPERATIONS } from '../data/mockData'

const AppContext = createContext(null)

const DATA_VERSION = '2026.04.b'
function checkAndClearStorage() {
  if (localStorage.getItem('ib_data_version') !== DATA_VERSION) {
    localStorage.removeItem('ib_operations')
    localStorage.removeItem('ib_thread_messages')
    localStorage.removeItem('ib_tasks')
    // ib_md_chat NAO e limpo — conversas com o MD devem persistir sempre
    localStorage.setItem('ib_data_version', DATA_VERSION)
  }
}
checkAndClearStorage()

function loadOperations() {
  try {
    const saved = localStorage.getItem('ib_operations')
    return saved ? JSON.parse(saved) : OPERATIONS.map(o => ({ ...o }))
  } catch {
    return OPERATIONS.map(o => ({ ...o }))
  }
}

function loadMessages() {
  try {
    const saved = localStorage.getItem('ib_thread_messages')
    return saved ? JSON.parse(saved) : MESSAGES.map(m => ({ ...m, messages: m.messages.map(msg => ({ ...msg })) }))
  } catch {
    return MESSAGES.map(m => ({ ...m, messages: m.messages.map(msg => ({ ...msg })) }))
  }
}

function loadTasks() {
  try {
    const saved = localStorage.getItem('ib_tasks')
    return saved ? JSON.parse(saved) : TASKS.map(t => ({ ...t }))
  } catch {
    return TASKS.map(t => ({ ...t }))
  }
}

const initialState = {
  currentPage: 'kanban',
  darkMode: true,
  tasks: loadTasks(),
  operations: loadOperations(),
  messages: loadMessages(),
  agents: AGENTS.map(a => ({ ...a })),
  training: TRAINING_RECOMMENDATIONS.map(t => ({ ...t })),
  mdDemands: MD_DEMANDS.map(d => ({ ...d })),
  proposals: [],
  selectedOperation: null,
  selectedAgent: null,
  filterAgent: null,
  filterOperation: null,
  toasts: [],
  sidebarCollapsed: false,
}

function reducer(state, action) {
  switch (action.type) {
    case 'SET_PAGE':
      return { ...state, currentPage: action.payload }
    case 'TOGGLE_DARK':
      return { ...state, darkMode: !state.darkMode }
    case 'TOGGLE_SIDEBAR':
      return { ...state, sidebarCollapsed: !state.sidebarCollapsed }
    case 'MOVE_TASK': {
      const tasks = state.tasks.map(t =>
        t.id === action.payload.taskId ? { ...t, column: action.payload.column } : t
      )
      try { localStorage.setItem('ib_tasks', JSON.stringify(tasks)) } catch {}
      return { ...state, tasks }
    }
    case 'SET_FILTER_AGENT':
      return { ...state, filterAgent: state.filterAgent === action.payload ? null : action.payload }
    case 'SET_FILTER_OPERATION':
      return { ...state, filterOperation: state.filterOperation === action.payload ? null : action.payload }
    case 'SELECT_OPERATION':
      return { ...state, selectedOperation: action.payload }
    case 'SELECT_AGENT':
      return { ...state, selectedAgent: action.payload }
    case 'SEND_MESSAGE': {
      const messages = state.messages.map(m => {
        if (m.id === action.payload.threadId) {
          return {
            ...m,
            messages: [...m.messages, {
              from: 'user',
              text: action.payload.text,
              time: new Date().toISOString(),
              type: 'resposta',
            }],
            unread: 0,
          }
        }
        return m
      })
      try { localStorage.setItem('ib_thread_messages', JSON.stringify(messages)) } catch {}
      return { ...state, messages }
    }
    case 'ADD_AGENT_RESPONSE': {
      const messages = state.messages.map(m => {
        if (m.id === action.payload.threadId) {
          return {
            ...m,
            messages: [...m.messages, {
              from: action.payload.agentId,
              text: action.payload.text,
              time: new Date().toISOString(),
              type: 'resposta',
            }],
          }
        }
        return m
      })
      try { localStorage.setItem('ib_thread_messages', JSON.stringify(messages)) } catch {}
      return { ...state, messages }
    }
    case 'UPDATE_AGENT': {
      const agents = state.agents.map(a =>
        a.id === action.payload.id ? { ...a, ...action.payload.updates } : a
      )
      return { ...state, agents }
    }
    case 'COMPLETE_TRAINING': {
      const training = state.training.map(t =>
        t.id === action.payload ? { ...t, status: 'concluido' } : t
      )
      return { ...state, training }
    }
    case 'ATTEND_DEMAND': {
      const mdDemands = state.mdDemands.map(d =>
        d.id === action.payload ? { ...d, status: 'atendido' } : d
      )
      return { ...state, mdDemands }
    }
    case 'APPEND_TASK_LOG': {
      const tasks = state.tasks.map(t => {
        if (t.id !== action.payload.taskId) return t
        const newLog = [...(t.log || []), ...(action.payload.entries || [])]
        const updates = { log: newLog }
        if (action.payload.column) updates.column = action.payload.column
        return { ...t, ...updates }
      })
      try { localStorage.setItem('ib_tasks', JSON.stringify(tasks)) } catch {}
      return { ...state, tasks }
    }
    case 'OPEN_PROJECT': {
      const { form, docs } = action.payload
      const ecmTypes = ['IPO', 'Follow-on', 'Block Trade']
      const isECM = ecmTypes.includes(form.opType)
      const opId = action.payload.opId || `op_${Date.now()}`
      const now = new Date().toISOString()

      const pendingDocs = docs.filter(d => d.required && d.files.length === 0).map(d => d.label)
      const pendingNote = pendingDocs.length > 0
        ? `Documentos pendentes: ${pendingDocs.join(', ')}. Os agentes prosseguem com o disponivel e solicitarao os itens faltantes conforme necessario.`
        : 'Documentacao completa recebida.'

      const newOp = {
        id: opId,
        name: `${form.company} — ${form.opType}`,
        type: isECM ? 'ECM' : 'DCM',
        instrument: form.opType,
        value: parseFloat(form.value) || 0,
        status: 'Em Estruturacao',
        stage: 'Etapa 1 — Revisao Documental',
        company: form.company,
        cnpj: form.cnpj,
        sector: form.sector,
        deadline: form.deadline,
        rating: form.rating,
        guarantees: form.guarantees || [],
        priority: form.priority,
        notes: form.notes,
        agents: form.agents,
        selectedDocs: form.selectedDocs || [],
        additionalRequest: form.additionalRequest || '',
        openedAt: now,
        pendingDocs,
      }

      const mk = (id, title, agent, column, difficulty, maxHours, logText) => ({
        id: `${opId}_${id}`,
        title: `${title}: ${form.company}`,
        agent,
        operation: opId,
        column,
        difficulty,
        hoursElapsed: 0,
        maxHours,
        log: [{ time: now, agent: 'md_orchestrator', type: 'assign', text: logText }],
      })

      const pipelineTasks = [
        mk('accountant', 'Etapa 1 — Revisao de DFs', 'accountant', 'Em Analise', 3, 16,
          `Revisar e ajustar as demonstracoes financeiras (IFRS 16, normalizacao de EBITDA). ${pendingNote}`),
        mk('legal', 'Etapa 1 — Due Diligence Juridica', 'legal_advisor', 'Em Analise', 3, 20,
          `Iniciar due diligence juridica: documentos societarios, garantias e compliance CVM/ANBIMA. ${pendingNote}`),
        mk('research', 'Etapa 2 — Research Report', 'research_analyst', 'Backlog', 4, 24,
          `Aguardando outputs da Etapa 1 (Contador + Juridico) para iniciar research corporativo.`),
        mk('modeling', 'Etapa 3 — Modelagem Financeira', 'financial_modeler', 'Backlog', 5, 32,
          `Aguardando Research Report (Etapa 2) para iniciar modelagem financeira ${isECM ? 'ECM' : 'DCM'}.`),
        mk('specialist', `Etapa 4 — Relatorio de Viabilidade ${isECM ? 'ECM' : 'DCM'}`,
          isECM ? 'ecm_specialist' : 'dcm_specialist', 'Backlog', 5, 24,
          `Aguardando Modelagem Financeira (Etapa 3) para elaborar Relatorio de Viabilidade.`),
        mk('risk', 'Etapa 4 — Risk & Compliance', 'risk_compliance', 'Backlog', 3, 16,
          `Revisar compliance e riscos regulatorios da operacao ${form.opType} em paralelo na Etapa 4.`),
        mk('deck', `Etapa 5 — ${isECM ? 'CIM e Teaser' : 'Book de Credito e Teaser'}`, 'deck_builder', 'Backlog', 4, 20,
          `Elaborar materiais de distribuicao apos aprovacao do Relatorio de Viabilidade (Etapa 4).`),
      ]

      const mdThread = {
        id: `msg_${opId}`,
        agent: 'md_orchestrator',
        operation: opId,
        type: 'resposta',
        subject: `Pipeline iniciado — ${form.company} (${form.opType})`,
        messages: [{
          from: 'md_orchestrator',
          text: `Projeto ${form.company} recebido. Tipo: ${isECM ? 'ECM' : 'DCM'} — ${form.opType}. Prioridade: ${form.priority}.\n\nEtapa 1 (em andamento, paralelo): Contador revisando DFs; Juridico iniciando due diligence. Etapas 2 a 5 estao no backlog aguardando os outputs anteriores.\n\n${pendingNote}${form.notes ? `\n\nObservacoes do mandante: ${form.notes}` : ''}`,
          time: now,
          type: 'resposta',
        }],
        status: 'aberto',
        urgency: form.priority === 'Alta' ? 'alta' : form.priority === 'Media' ? 'media' : 'baixa',
        unread: 1,
      }

      const operations = [newOp, ...state.operations]
      const tasks = [...pipelineTasks, ...state.tasks]
      const messages = [mdThread, ...state.messages]
      try { localStorage.setItem('ib_operations', JSON.stringify(operations)) } catch {}
      try { localStorage.setItem('ib_tasks', JSON.stringify(tasks)) } catch {}
      try { localStorage.setItem('ib_thread_messages', JSON.stringify(messages)) } catch {}
      return { ...state, operations, tasks, messages }
    }
    case 'ADD_THREAD': {
      const messages = [action.payload, ...state.messages]
      try { localStorage.setItem('ib_thread_messages', JSON.stringify(messages)) } catch {}
      return { ...state, messages }
    }
    case 'ADD_PROPOSAL':
      return { ...state, proposals: [action.payload, ...state.proposals] }
    case 'ADD_TOAST':
      return { ...state, toasts: [...state.toasts, { id: Date.now(), ...action.payload }] }
    case 'REMOVE_TOAST':
      return { ...state, toasts: state.toasts.filter(t => t.id !== action.payload) }
    default:
      return state
  }
}

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState)

  const toast = useCallback((message, type = 'info') => {
    const id = Date.now()
    dispatch({ type: 'ADD_TOAST', payload: { message, type } })
    setTimeout(() => dispatch({ type: 'REMOVE_TOAST', payload: id }), 4000)
  }, [])

  return (
    <AppContext.Provider value={{ state, dispatch, toast }}>
      {children}
    </AppContext.Provider>
  )
}

export const useApp = () => useContext(AppContext)
