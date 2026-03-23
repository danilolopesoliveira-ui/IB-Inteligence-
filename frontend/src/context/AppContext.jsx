import { createContext, useContext, useReducer, useCallback, useEffect } from 'react'
import { TASKS, MESSAGES, AGENTS, TRAINING_RECOMMENDATIONS, MD_DEMANDS, OPERATIONS } from '../data/mockData'

const AppContext = createContext(null)

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

const initialState = {
  currentPage: 'kanban',
  darkMode: true,
  tasks: TASKS.map(t => ({ ...t })),
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
    case 'OPEN_PROJECT': {
      const { form, docs } = action.payload
      const ecmTypes = ['IPO', 'Follow-on', 'Block Trade']
      const opId = `op_${Date.now()}`
      const newOp = {
        id: opId,
        name: `${form.company} — ${form.opType}`,
        type: ecmTypes.includes(form.opType) ? 'ECM' : 'DCM',
        instrument: form.opType,
        value: parseFloat(form.value) || 0,
        status: 'Em Estruturacao',
        stage: 'Etapa 1 — Revisao Documental',
        company: form.company,
        cnpj: form.cnpj,
        sector: form.sector,
        deadline: form.deadline,
        rating: form.rating,
        guarantee: form.guarantee,
        priority: form.priority,
        notes: form.notes,
        agents: form.agents,
        selectedDocs: form.selectedDocs || [],
        additionalRequest: form.additionalRequest || '',
        openedAt: new Date().toISOString(),
        pendingDocs: docs.filter(d => d.required && d.files.length === 0).map(d => d.label),
      }
      const newTask = {
        id: `task_${opId}`,
        title: `Etapa 1 — Revisao Documental: ${form.company}`,
        agent: 'md_orchestrator',
        operation: opId,
        column: 'Em Analise',
        difficulty: 3,
        hoursElapsed: 0,
        maxHours: 24,
        log: [{ time: new Date().toISOString(), agent: 'md_orchestrator', type: 'assign', text: `Projeto ${form.company} (${form.opType}) aberto. Prioridade: ${form.priority}. Iniciando pipeline — Etapa 1: Revisao Documental.${newOp.pendingDocs.length > 0 ? ` Documentos pendentes: ${newOp.pendingDocs.join(', ')}.` : ' Todos os documentos recebidos.'}` }],
      }
      const operations = [newOp, ...state.operations]
      const tasks = [newTask, ...state.tasks]
      try { localStorage.setItem('ib_operations', JSON.stringify(operations)) } catch {}
      return { ...state, operations, tasks }
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
