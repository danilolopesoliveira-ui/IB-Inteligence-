import { useState } from 'react'
import { useApp } from '../context/AppContext'
import { X, Plus, Trash2, FileText, Upload, Download } from 'lucide-react'

const INSTRUMENTOS = [
  'Loan Offshore', 'Debenture Simples', 'Debenture Incentivada (Lei 12.431)',
  'CRI', 'CRA', 'CPR', 'FIDC', 'Nota Comercial', 'CCB',
  'SBLC / Carta de Crédito', 'Operação 4.131',
]

const MOEDAS = ['BRL', 'USD', 'EUR', 'CHF']

const REGIMES = [
  'Não haverá registro de oferta',
  'Melhores esforços',
  'Garantia firme',
  'RCVM 160 — Regime Ordinário',
  'RCVM 160 — Regime Automático ANBIMA',
]

const TIPO_GARANTIA_OPTIONS = [
  'Garantia Real (Imóvel / Fazenda)',
  'Recebíveis',
  'Aval dos Sócios',
  'Aval Cruzado das Empresas',
  'Produção Agrícola Não Alienada',
  'Duplicatas',
  'Estoque',
  'Infraestrutura / Equipamentos',
  'SBLC / Carta de Crédito',
  'Alienação Fiduciária de Cotas',
  'Outro',
]

const PUBLICO_ALVO_OPCOES = [
  'Bancos Nacionais',
  'Bancos Internacionais',
  'Gestoras de Recursos',
  'Fundos de Crédito',
  'Previdência / Seguradoras',
  'Investidores Qualificados',
]

function GarantiaRow({ garantia, onChange, onRemove, onFileChange }) {
  return (
    <div className="border border-surface-200 rounded-lg p-3 space-y-2 bg-surface-100/20">
      <div className="flex items-center gap-2">
        <select
          className="input-field flex-1 text-xs"
          value={garantia.tipo}
          onChange={e => onChange({ ...garantia, tipo: e.target.value })}
        >
          {TIPO_GARANTIA_OPTIONS.map(t => <option key={t}>{t}</option>)}
        </select>
        <button onClick={onRemove} className="text-gray-500 hover:text-accent-red transition-colors p-1">
          <Trash2 size={14} />
        </button>
      </div>
      <input
        className="input-field text-xs"
        placeholder="Descrição (ex: Fazenda Santo Estevão I, II e III — matrículas 1234, 1235)"
        value={garantia.descricao}
        onChange={e => onChange({ ...garantia, descricao: e.target.value })}
      />
      <div className="flex items-center gap-2">
        <label className="flex items-center gap-1.5 cursor-pointer px-2.5 py-1.5 rounded-lg border border-dashed border-surface-200 hover:border-gold/40 transition-colors text-xs text-gray-400 hover:text-gray-200">
          <Upload size={12} />
          {garantia.file ? garantia.file.name : 'Anexar matrícula / planilha (PDF ou Excel)'}
          <input
            type="file"
            accept=".pdf,.xlsx,.xls,.csv"
            className="hidden"
            onChange={e => onFileChange(e.target.files[0])}
          />
        </label>
        {garantia.file && (
          <button onClick={() => onFileChange(null)} className="text-gray-500 hover:text-white">
            <X size={12} />
          </button>
        )}
      </div>
      {garantia.cobertura && (
        <input
          className="input-field text-xs"
          placeholder="Cobertura / LTV estimado (ex: R$ 15M — cobertura 1.2x)"
          value={garantia.cobertura}
          onChange={e => onChange({ ...garantia, cobertura: e.target.value })}
        />
      )}
    </div>
  )
}

export default function TermSheetModal({ onClose, operationName = '' }) {
  const { toast, dispatch } = useApp()

  const [form, setForm] = useState({
    emissor: operationName || '',
    tipoOperacao: 'DCM',
    instrumento: 'Loan Offshore',
    volume: '',
    moeda: 'BRL',
    prazo: '',
    taxa: '',
    regime: 'Não haverá registro de oferta',
    publicoAlvo: [],
    destinacao: '',
    comissionamento: '2,5%',
    coberturaFX: '',
    vencimentoAntecipado: 'Em termos usuais de mercado e habitualmente adotados pela Gennesys em operações semelhantes.',
    resgateAntecipado: 'Liquidação e amortização antecipada a mercado, sem incidência de penalty fee.',
    outrasCondicoes: '',
    aviso: true,
    garantias: [],
  })

  const [step, setStep] = useState(1) // 1: dados, 2: garantias, 3: revisão

  const setField = (field, value) => setForm(f => ({ ...f, [field]: value }))

  const addGarantia = () => setForm(f => ({
    ...f,
    garantias: [...f.garantias, { tipo: 'Garantia Real (Imóvel / Fazenda)', descricao: '', file: null, cobertura: '' }],
  }))

  const updateGarantia = (idx, updated) => setForm(f => ({
    ...f,
    garantias: f.garantias.map((g, i) => i === idx ? updated : g),
  }))

  const removeGarantia = idx => setForm(f => ({
    ...f,
    garantias: f.garantias.filter((_, i) => i !== idx),
  }))

  const setGarantiaFile = (idx, file) => updateGarantia(idx, { ...form.garantias[idx], file })

  const togglePublico = (p) => setForm(f => ({
    ...f,
    publicoAlvo: f.publicoAlvo.includes(p) ? f.publicoAlvo.filter(x => x !== p) : [...f.publicoAlvo, p],
  }))

  const generate = () => {
    if (!form.emissor) { toast('Informe o nome do Emissor', 'error'); return }
    if (!form.volume) { toast('Informe o Volume da operação', 'error'); return }
    toast('Gerando Term Sheet...', 'info')
    setTimeout(() => {
      const proposal = {
        id: `ts_${Date.now()}`,
        emissor: form.emissor,
        instrumento: form.instrumento,
        volume: form.volume,
        moeda: form.moeda,
        tipoOperacao: form.tipoOperacao,
        prazo: form.prazo,
        taxa: form.taxa,
        regime: form.regime,
        publicoAlvo: form.publicoAlvo,
        destinacao: form.destinacao,
        comissionamento: form.comissionamento,
        coberturaFX: form.coberturaFX,
        vencimentoAntecipado: form.vencimentoAntecipado,
        resgateAntecipado: form.resgateAntecipado,
        outrasCondicoes: form.outrasCondicoes,
        garantias: form.garantias.map(g => ({
          tipo: g.tipo,
          descricao: g.descricao,
          cobertura: g.cobertura,
          fileName: g.file?.name || null,
        })),
        createdAt: new Date().toISOString(),
        status: 'emitido',
      }
      dispatch({ type: 'ADD_PROPOSAL', payload: proposal })
      toast(`Term Sheet de ${form.emissor} disponível em Operações & Documentos → Propostas`, 'success')
      onClose()
    }, 1200)
  }

  const STEPS = ['Dados da Operação', 'Garantias', 'Revisão']

  return (
    <div
      className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[100] flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-surface-50 border border-surface-200 rounded-xl w-full max-w-2xl max-h-[90vh] flex flex-col"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-surface-200 flex-shrink-0">
          <div>
            <h3 className="text-base font-bold text-white">Emitir Proposta — Term Sheet Indicativo</h3>
            <p className="text-xs text-gray-500 mt-0.5">Gennesys · Estritamente Privado e Confidencial</p>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white p-1"><X size={18} /></button>
        </div>

        {/* Step tabs */}
        <div className="flex border-b border-surface-200 px-5 flex-shrink-0">
          {STEPS.map((s, i) => (
            <button
              key={s}
              onClick={() => setStep(i + 1)}
              className={`py-2.5 px-3 text-xs font-medium mr-1 border-b-2 transition-all ${
                step === i + 1
                  ? 'border-gold text-gold'
                  : 'border-transparent text-gray-400 hover:text-gray-200'
              }`}
            >
              {i + 1}. {s}
            </button>
          ))}
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-5">

          {/* STEP 1: Dados da Operação */}
          {step === 1 && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="col-span-2">
                  <label className="text-xs text-gray-400 block mb-1">Emissor *</label>
                  <input className="input-field" value={form.emissor} onChange={e => setField('emissor', e.target.value)} placeholder="Nome completo do emissor" />
                </div>

                <div>
                  <label className="text-xs text-gray-400 block mb-1">Tipo de Operação</label>
                  <select className="input-field" value={form.tipoOperacao} onChange={e => setField('tipoOperacao', e.target.value)}>
                    <option>DCM</option>
                    <option>ECM</option>
                    <option>Loan Offshore</option>
                    <option>M&A</option>
                    <option>FIDC</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs text-gray-400 block mb-1">Instrumento</label>
                  <select className="input-field" value={form.instrumento} onChange={e => setField('instrumento', e.target.value)}>
                    {INSTRUMENTOS.map(i => <option key={i}>{i}</option>)}
                  </select>
                </div>

                <div>
                  <label className="text-xs text-gray-400 block mb-1">Volume *</label>
                  <input className="input-field" value={form.volume} onChange={e => setField('volume', e.target.value)} placeholder="Ex: 50.000.000,00" />
                </div>

                <div>
                  <label className="text-xs text-gray-400 block mb-1">Moeda</label>
                  <select className="input-field" value={form.moeda} onChange={e => setField('moeda', e.target.value)}>
                    {MOEDAS.map(m => <option key={m}>{m}</option>)}
                  </select>
                </div>

                <div>
                  <label className="text-xs text-gray-400 block mb-1">Prazo</label>
                  <input className="input-field" value={form.prazo} onChange={e => setField('prazo', e.target.value)} placeholder="Ex: 36 meses / 5 anos" />
                </div>

                <div>
                  <label className="text-xs text-gray-400 block mb-1">Taxa / Spread</label>
                  <input className="input-field" value={form.taxa} onChange={e => setField('taxa', e.target.value)} placeholder="Ex: CDI + 3,5% a.a. / IPCA + 7% a.a." />
                </div>

                <div className="col-span-2">
                  <label className="text-xs text-gray-400 block mb-1">Regime de Colocação</label>
                  <select className="input-field" value={form.regime} onChange={e => setField('regime', e.target.value)}>
                    {REGIMES.map(r => <option key={r}>{r}</option>)}
                  </select>
                </div>

                <div className="col-span-2">
                  <label className="text-xs text-gray-400 block mb-1">Público Alvo</label>
                  <div className="flex flex-wrap gap-2">
                    {PUBLICO_ALVO_OPCOES.map(p => (
                      <button
                        key={p}
                        onClick={() => togglePublico(p)}
                        className={`px-2.5 py-1 rounded-full text-[11px] font-medium border transition-all ${
                          form.publicoAlvo.includes(p)
                            ? 'border-gold text-gold bg-gold/10'
                            : 'border-surface-200 text-gray-400 hover:text-gray-200'
                        }`}
                      >
                        {p}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="col-span-2">
                  <label className="text-xs text-gray-400 block mb-1">Destinação de Recursos</label>
                  <input className="input-field" value={form.destinacao} onChange={e => setField('destinacao', e.target.value)} placeholder="Ex: Capex de expansão / Capital de giro / Baixa de parcelamentos" />
                </div>

                <div>
                  <label className="text-xs text-gray-400 block mb-1">Comissionamento</label>
                  <input className="input-field" value={form.comissionamento} onChange={e => setField('comissionamento', e.target.value)} placeholder="Ex: 2,5% sobre o volume" />
                </div>

                {(form.moeda !== 'BRL') && (
                  <div>
                    <label className="text-xs text-gray-400 block mb-1">Cobertura FX</label>
                    <input className="input-field" value={form.coberturaFX} onChange={e => setField('coberturaFX', e.target.value)} placeholder="Ex: Cobertura até R$ 6,20/USD" />
                  </div>
                )}

                <div className="col-span-2">
                  <label className="text-xs text-gray-400 block mb-1">Vencimento Antecipado</label>
                  <textarea className="input-field h-14 resize-none text-xs" value={form.vencimentoAntecipado} onChange={e => setField('vencimentoAntecipado', e.target.value)} />
                </div>

                <div className="col-span-2">
                  <label className="text-xs text-gray-400 block mb-1">Resgate Antecipado</label>
                  <textarea className="input-field h-14 resize-none text-xs" value={form.resgateAntecipado} onChange={e => setField('resgateAntecipado', e.target.value)} />
                </div>

                <div className="col-span-2">
                  <label className="text-xs text-gray-400 block mb-1">Outras Condições</label>
                  <textarea className="input-field h-14 resize-none text-xs" value={form.outrasCondicoes} onChange={e => setField('outrasCondicoes', e.target.value)} placeholder="Condições adicionais específicas da operação..." />
                </div>
              </div>
            </div>
          )}

          {/* STEP 2: Garantias */}
          {step === 2 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <p className="text-sm font-medium text-white">Garantias Disponíveis</p>
                  <p className="text-xs text-gray-500 mt-0.5">Adicione cada garantia separadamente. Anexe matrículas (PDF) ou planilhas de recebíveis (Excel/CSV).</p>
                </div>
                <button onClick={addGarantia} className="btn-primary flex items-center gap-1.5 text-xs">
                  <Plus size={12} /> Adicionar
                </button>
              </div>

              {form.garantias.length === 0 && (
                <div className="border-2 border-dashed border-surface-200 rounded-lg p-8 text-center">
                  <FileText size={24} className="mx-auto text-gray-600 mb-2" />
                  <p className="text-xs text-gray-400">Nenhuma garantia adicionada.</p>
                  <p className="text-xs text-gray-500 mt-1">Clique em "Adicionar" para incluir garantias reais, recebíveis, avais, etc.</p>
                </div>
              )}

              {form.garantias.map((g, i) => (
                <GarantiaRow
                  key={i}
                  garantia={g}
                  onChange={updated => updateGarantia(i, updated)}
                  onRemove={() => removeGarantia(i)}
                  onFileChange={file => setGarantiaFile(i, file)}
                />
              ))}

              {form.garantias.length > 0 && (
                <div className="p-3 bg-accent-blue/5 border border-accent-blue/20 rounded-lg">
                  <p className="text-xs text-accent-blue font-medium mb-1">Tipos de arquivo aceitos por garantia:</p>
                  <ul className="text-xs text-gray-400 space-y-0.5">
                    <li>• <strong className="text-gray-300">Garantia Real (Imóvel):</strong> Matrícula do imóvel em PDF — o agente extrairá dados de proprietário, área e ônus</li>
                    <li>• <strong className="text-gray-300">Recebíveis / Duplicatas:</strong> Excel/CSV com carteira — agente calculará concentração, aging e cobertura</li>
                    <li>• <strong className="text-gray-300">Produção Agrícola:</strong> Laudo ou planilha com produtividade, área e safra estimada</li>
                    <li>• <strong className="text-gray-300">Equipamentos:</strong> Laudo de avaliação em PDF ou Excel com valor contábil</li>
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* STEP 3: Revisão */}
          {step === 3 && (
            <div className="space-y-4">
              <p className="text-xs text-gray-500 mb-3">Revise os dados antes de gerar o Term Sheet.</p>

              <div className="border border-surface-200 rounded-lg overflow-hidden">
                <div className="bg-surface-200/50 px-4 py-2.5 border-b border-surface-200">
                  <p className="text-xs font-bold text-gold uppercase tracking-wider">Term Sheet Indicativo</p>
                  <p className="text-[10px] text-gray-500 mt-0.5">Estritamente Privado e Confidencial</p>
                </div>
                <div className="divide-y divide-surface-200/50">
                  {[
                    ['Emissor', form.emissor || '—'],
                    ['Instrumento', form.instrumento],
                    ['Volume', `${form.moeda} ${form.volume || '—'}`],
                    ['Prazo', form.prazo || '—'],
                    ['Taxa / Spread', form.taxa || 'A definir'],
                    ['Regime de Colocação', form.regime],
                    ['Público Alvo', form.publicoAlvo.join(', ') || 'A definir'],
                    ['Destinação de Recursos', form.destinacao || '—'],
                    ['Comissionamento', `Fee de sucesso de ${form.comissionamento}, pagos na liquidação`],
                    ...(form.coberturaFX ? [['Cobertura FX', form.coberturaFX]] : []),
                  ].map(([label, value]) => (
                    <div key={label} className="flex px-4 py-2.5 gap-4">
                      <span className="text-xs text-gray-500 w-44 flex-shrink-0">{label}</span>
                      <span className="text-xs text-gray-200 flex-1">{value}</span>
                    </div>
                  ))}

                  {form.garantias.length > 0 && (
                    <div className="flex px-4 py-2.5 gap-4">
                      <span className="text-xs text-gray-500 w-44 flex-shrink-0">Garantias Disponíveis</span>
                      <div className="flex-1 space-y-1">
                        {form.garantias.map((g, i) => (
                          <div key={i} className="text-xs text-gray-200">
                            {i + 1 === 1 ? 'I' : i + 1 === 2 ? 'II' : i + 1 === 3 ? 'III' : `${i + 1}.`}. {g.tipo}{g.descricao ? ` — ${g.descricao}` : ''}
                            {g.file && <span className="text-accent-blue ml-1.5">({g.file.name})</span>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex px-4 py-2.5 gap-4">
                    <span className="text-xs text-gray-500 w-44 flex-shrink-0">Vencimento Antecipado</span>
                    <span className="text-xs text-gray-400 flex-1">{form.vencimentoAntecipado}</span>
                  </div>
                  <div className="flex px-4 py-2.5 gap-4">
                    <span className="text-xs text-gray-500 w-44 flex-shrink-0">Resgate Antecipado</span>
                    <span className="text-xs text-gray-400 flex-1">{form.resgateAntecipado}</span>
                  </div>
                  {form.outrasCondicoes && (
                    <div className="flex px-4 py-2.5 gap-4">
                      <span className="text-xs text-gray-500 w-44 flex-shrink-0">Outras Condições</span>
                      <span className="text-xs text-gray-400 flex-1">{form.outrasCondicoes}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="p-3 bg-gold/5 border border-gold/20 rounded-lg">
                <p className="text-xs text-gold font-medium mb-1">Aviso Legal</p>
                <p className="text-[11px] text-gray-400 leading-relaxed">
                  Todos os termos e condições expostos estão sujeitos à aprovação pelos comitês internos da Gennesys,
                  os quais poderão promover quaisquer alterações nas informações indicativas ora apresentadas.
                  Este documento é estritamente confidencial.
                </p>
              </div>

              {form.garantias.some(g => g.file) && (
                <div className="p-3 bg-accent-blue/5 border border-accent-blue/20 rounded-lg">
                  <p className="text-xs text-accent-blue font-medium mb-1">Análise de Garantias Pendente</p>
                  <p className="text-[11px] text-gray-400">
                    {form.garantias.filter(g => g.file).length} arquivo(s) de garantia serão enviados para análise
                    pelo agente de crédito após a geração do Term Sheet.
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-5 border-t border-surface-200 flex-shrink-0">
          <button
            onClick={() => step > 1 ? setStep(s => s - 1) : onClose()}
            className="btn-ghost text-xs"
          >
            {step > 1 ? 'Voltar' : 'Cancelar'}
          </button>
          <div className="flex items-center gap-2">
            <div className="flex gap-1 mr-2">
              {STEPS.map((_, i) => (
                <div key={i} className={`w-1.5 h-1.5 rounded-full transition-all ${step === i + 1 ? 'bg-gold' : 'bg-surface-200'}`} />
              ))}
            </div>
            {step < 3 ? (
              <button onClick={() => setStep(s => s + 1)} className="btn-primary text-xs">
                Próximo
              </button>
            ) : (
              <button onClick={generate} className="btn-primary flex items-center gap-2 text-xs">
                <Download size={14} /> Gerar Term Sheet
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
