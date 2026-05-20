import { AlertTriangle } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useBrand } from '../contexts/BrandContext'

export default function Termos() {
  const { meta: brand } = useBrand()
  return (
    <div className="min-h-screen px-4 py-10">
      <div className="max-w-2xl mx-auto space-y-5">
        <Link to="/" className="text-[12px] text-accent-text hover:underline">← Voltar</Link>
        <h1 className="font-heading text-3xl font-extrabold text-primary">Termos de Uso</h1>
        <p className="text-[12px] text-subtle">Versão 2026-05-20</p>

        <div
          className="rounded-btn p-4 space-y-2"
          style={{
            background: 'color-mix(in srgb, var(--color-danger) 8%, transparent)',
            border: '1px solid color-mix(in srgb, var(--color-danger) 35%, transparent)',
          }}
        >
          <div className="flex items-center gap-2">
            <AlertTriangle size={16} className="text-danger" strokeWidth={2} />
            <p className="text-[12px] font-bold uppercase tracking-wider text-danger">Avisos importantes — leia antes de assinar</p>
          </div>
          <ul className="text-[13px] text-primary space-y-1.5 leading-relaxed">
            <li><strong>O {brand.nome} não garante aprovação em concursos.</strong> O sucesso depende exclusivamente do empenho, da dedicação e do desempenho do candidato no dia da prova. Nenhum método ou material — incluindo este — substitui o estudo individual e a consulta às fontes oficiais.</li>
            <li><strong>Todo o conteúdo (textos, resumos, questões, comentários, podcasts, correções de redação) é gerado por modelos de inteligência artificial</strong> e <strong>pode conter erros, imprecisões, omissões e lacunas</strong>. A IA pode confundir versões de frameworks, atribuir códigos errados a normas, citar leis de forma imprecisa e produzir afirmações que parecem corretas mas não são (alucinações). É <strong>responsabilidade do aluno</strong> validar informações críticas em fontes oficiais antes de usá-las em prova ou em qualquer decisão.</li>
          </ul>
        </div>

        <section className="space-y-3 text-[13px] text-muted leading-relaxed">
          <h2 className="font-heading text-lg font-bold text-primary mt-4">1. Aceitação</h2>
          <p>Ao se cadastrar e utilizar a plataforma <strong>{brand.nome}</strong>, o usuário declara ter lido, compreendido e concordar integralmente com estes Termos, incluindo os Avisos Importantes acima.</p>

          <h2 className="font-heading text-lg font-bold text-primary mt-4">2. Natureza do serviço e limites da IA</h2>
          <p>O {brand.nome} é uma plataforma de estudos <strong>auxiliar e complementar</strong>, com conteúdo gerado por modelos de inteligência artificial (Claude, da Anthropic; Chirp HD, do Google Cloud). O conteúdo é uma <strong>ferramenta de apoio</strong> e <strong>não substitui</strong> a leitura de fontes oficiais (editais, normas, legislação, jurisprudência, doutrina, aulas).</p>
          <p>A IA pode produzir <strong>imprecisões factuais, lacunas de conteúdo, omissões temáticas e afirmações incorretas com aparência de verdade ("alucinações")</strong>. Isso é uma característica intrínseca à tecnologia atual e <strong>não constitui defeito do serviço</strong>. Riscos típicos no contexto de concursos incluem, sem limitação:</p>
          <ul className="list-disc list-inside space-y-1 pl-2">
            <li>Versões de frameworks confundidas (COBIT 5 vs 2019, ITIL v3 vs v4, PMBOK 6 vs 7, ISO 27001:2013 vs 2022).</li>
            <li>Códigos de processos, números de artigos, datas de leis e alíquotas trocados.</li>
            <li>Tópicos do edital insuficientemente cobertos ou ausentes do material gerado.</li>
            <li>Correções de redação que avaliam de forma diferente do que faria um corretor humano da banca.</li>
            <li>Questões com gabarito incorreto ou comentários que não se sustentam no exame de fonte oficial.</li>
          </ul>
          <p>O usuário <strong>compromete-se a tratar todo conteúdo como uma sugestão a ser confirmada</strong> em fontes oficiais antes de levá-lo para a prova.</p>

          <h2 className="font-heading text-lg font-bold text-primary mt-4">3. Cadastro e conta</h2>
          <p>O cadastro exige usuário, e-mail e senha válidos. O usuário é responsável pela confidencialidade da senha e por toda atividade realizada na conta.</p>

          <h2 className="font-heading text-lg font-bold text-primary mt-4">4. Assinatura e pagamento</h2>
          <p>O {brand.nome} oferece <strong>7 dias gratuitos</strong> de teste. Após esse período, o acesso a funcionalidades premium (geração de material, áudio, redação) requer pagamento único via Pix.</p>
          <p>A assinatura é válida até a data da prova do concurso contratado, acrescida de 30 dias para fins de revisão e recursos. Não há renovação automática.</p>
          <p>Pagamentos são processados pelo Mercado Pago. Em caso de cancelamento antes da confirmação do pagamento, basta não pagar o boleto Pix.</p>

          <h2 className="font-heading text-lg font-bold text-primary mt-4">5. Reembolso</h2>
          <p>O usuário pode solicitar reembolso integral em até 7 dias após o pagamento (Código de Defesa do Consumidor, art. 49). Após esse prazo, não há reembolso, salvo problema técnico comprovado.</p>

          <h2 className="font-heading text-lg font-bold text-primary mt-4">6. Conduta do usuário</h2>
          <p>É vedado: compartilhar credenciais com terceiros; revender ou redistribuir conteúdo; usar a plataforma para fins ilícitos ou que violem direitos autorais; tentar comprometer a segurança do serviço.</p>
          <p>Violações implicam suspensão imediata sem reembolso.</p>

          <h2 className="font-heading text-lg font-bold text-primary mt-4">7. Propriedade intelectual</h2>
          <p>O código, design, fluxos e prompts da plataforma são propriedade do operador. O conteúdo gerado para o usuário é licenciado para uso pessoal e não-comercial.</p>

          <h2 className="font-heading text-lg font-bold text-primary mt-4">8. Limitação de responsabilidade</h2>
          <p>O {brand.nome} <strong>não garante, sob nenhuma hipótese</strong>:</p>
          <ul className="list-disc list-inside space-y-1 pl-2">
            <li>Aprovação, classificação dentro do número de vagas ou qualquer pontuação mínima em qualquer concurso.</li>
            <li>Exatidão, completude ou atualidade absoluta do conteúdo gerado pela IA.</li>
            <li>Cobertura integral do conteúdo programático do edital — pode haver tópicos ausentes ou subdesenvolvidos.</li>
            <li>Que a correção automatizada de redação reflita exatamente a nota que um corretor humano da banca atribuiria.</li>
          </ul>
          <p>O sucesso na prova depende exclusivamente da preparação, do esforço e do desempenho individual do candidato no dia da prova. O {brand.nome} é, em sua essência, um <strong>auxílio de estudo</strong>, e o uso isolado ou exclusivo do material gerado não é estratégia recomendada.</p>
          <p>O operador não responde por danos materiais, morais ou de qualquer natureza decorrentes de eventual reprovação em concurso, de imprecisões do material ou de erros de correção, salvo nos casos previstos no Código de Defesa do Consumidor e na legislação aplicável quanto à prestação efetiva do serviço contratado (acesso à plataforma).</p>

          <h2 className="font-heading text-lg font-bold text-primary mt-4">9. Alterações</h2>
          <p>Estes Termos podem ser atualizados. A versão vigente sempre aparece nesta página. Mudanças relevantes serão comunicadas por e-mail.</p>

          <h2 className="font-heading text-lg font-bold text-primary mt-4">10. Foro</h2>
          <p>Fica eleito o foro da comarca de Fortaleza/CE para dirimir quaisquer controvérsias.</p>
        </section>
      </div>
    </div>
  )
}
