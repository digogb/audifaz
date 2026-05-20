import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Sparkles, Target, PenLine, BookOpen, CheckCircle2 } from 'lucide-react'
import * as api from '../api'
import { useBrand } from '../contexts/BrandContext'

function Feature({ icon: Icon, title, desc }) {
  return (
    <div className="surface-card p-4 sm:p-5">
      <Icon size={20} className="text-accent-text mb-3" strokeWidth={1.75} />
      <h3 className="font-heading font-bold text-primary text-[15px]">{title}</h3>
      <p className="text-[13px] text-muted mt-1 leading-relaxed">{desc}</p>
    </div>
  )
}

export default function Landing() {
  const { meta: brand } = useBrand()
  const [concursos, setConcursos] = useState([])

  useEffect(() => {
    api.getConcursosPublicos().then(r => setConcursos(r.data)).catch(() => {})
  }, [])

  const featured = concursos.find(c => c.requer_assinatura) || concursos[0]

  return (
    <div className="min-h-screen px-4 py-10 sm:py-16">
      <div className="max-w-3xl mx-auto space-y-12">
        <header className="text-center space-y-3">
          <p className="text-[11px] uppercase tracking-widest text-accent-text font-semibold">{brand.nome}</p>
          <h1 className="font-heading text-4xl sm:text-5xl font-extrabold tracking-tight text-primary leading-tight">
            {brand.tagline}
          </h1>
          {featured && (
            <p className="text-[14px] text-muted max-w-xl mx-auto">
              Plano de estudos diário, questões no estilo da banca, podcast de revisão e correção de redação
              — calibrados para <span className="text-primary font-semibold">{featured.nome}</span>.
            </p>
          )}
        </header>

        {featured && (
          <div className="surface-card p-6 sm:p-8 text-center space-y-4">
            <p className="text-[11px] uppercase tracking-widest text-subtle">Concurso em destaque</p>
            <h2 className="font-heading text-2xl font-bold text-primary">{featured.nome}</h2>
            <p className="text-[13px] text-muted max-w-xl mx-auto">{featured.descricao}</p>
            <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
              <Link
                to={`/signup?concurso=${featured.slug}`}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-btn bg-accent hover:bg-accent-hover text-[13px] font-semibold transition-colors"
                style={{ color: 'var(--color-bg)' }}
              >
                Começar grátis por 7 dias
              </Link>
              <p className="text-[12px] text-subtle">
                Depois R$ {(featured.preco_cents || 0) / 100} até a prova
              </p>
            </div>
          </div>
        )}

        <section className="grid sm:grid-cols-2 gap-3">
          <Feature
            icon={BookOpen}
            title="Plano de estudos diário"
            desc="Cronograma estruturado em fases, semanas e dias. Conteúdo gerado e validado todo dia conforme a sua trajetória."
          />
          <Feature
            icon={Sparkles}
            title="Questões no estilo da banca"
            desc="Cinco a quinze questões por dia, com gabarito, comentário e classificação por bloco temático."
          />
          <Feature
            icon={PenLine}
            title="Correção de redação"
            desc="Submeta sua redação e receba feedback estruturado segundo a rubrica oficial: nota por critério + sugestões inline."
          />
          <Feature
            icon={Target}
            title="Métricas por bloco"
            desc="Saiba em tempo real onde está o seu gargalo: peso × prioridade × meta. Acerto sobe, gap diminui."
          />
        </section>

        <section className="surface-card p-6 sm:p-7 space-y-3">
          <h3 className="font-heading text-lg font-bold text-primary">O que está incluso no trial</h3>
          <ul className="space-y-1.5">
            {[
              'Material diário gerado por IA (Claude)',
              'Questões classificadas por banca e por bloco temático',
              'Correção de redação ilimitada nos 7 dias',
              'Podcast diário (RSS privado) para revisão no trajeto',
              'Tracking de progresso e simulados',
            ].map(item => (
              <li key={item} className="flex items-start gap-2 text-[13px] text-primary">
                <CheckCircle2 size={14} className="text-success shrink-0 mt-0.5" strokeWidth={2} />
                {item}
              </li>
            ))}
          </ul>
        </section>

        <footer className="text-center pt-6">
          <p className="text-[12px] text-subtle">
            Já tem conta? <Link to="/login" className="text-accent-text hover:underline">Entrar</Link>
          </p>
        </footer>
      </div>
    </div>
  )
}
