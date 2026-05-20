import { Link } from 'react-router-dom'
import { useBrand } from '../contexts/BrandContext'

export default function Termos() {
  const { meta: brand } = useBrand()
  return (
    <div className="min-h-screen px-4 py-10">
      <div className="max-w-2xl mx-auto space-y-5">
        <Link to="/" className="text-[12px] text-accent-text hover:underline">← Voltar</Link>
        <h1 className="font-heading text-3xl font-extrabold text-primary">Termos de Uso</h1>
        <p className="text-[12px] text-subtle">Versão 2026-05-19</p>

        <section className="space-y-3 text-[13px] text-muted leading-relaxed">
          <h2 className="font-heading text-lg font-bold text-primary mt-4">1. Aceitação</h2>
          <p>Ao se cadastrar e utilizar a plataforma <strong>{brand.nome}</strong>, o usuário declara ter lido e concorda integralmente com estes Termos.</p>

          <h2 className="font-heading text-lg font-bold text-primary mt-4">2. Natureza do serviço</h2>
          <p>O {brand.nome} é uma plataforma de estudos auxiliar, com conteúdo gerado por inteligência artificial (Claude, da Anthropic). O conteúdo é uma <strong>ferramenta de apoio</strong> e não substitui a leitura de fontes oficiais (editais, normas, legislação, jurisprudência, doutrina).</p>
          <p>A IA pode produzir <strong>imprecisões factuais</strong>. O usuário é responsável por validar informações críticas (códigos de processos, números de leis, datas, alíquotas, etc.) em fontes oficiais.</p>

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
          <p>O {brand.nome} não garante aprovação em concursos. A responsabilidade pelo desempenho na prova é exclusiva do candidato. Não respondemos por imprecisões da IA além do disposto na Seção 2.</p>

          <h2 className="font-heading text-lg font-bold text-primary mt-4">9. Alterações</h2>
          <p>Estes Termos podem ser atualizados. A versão vigente sempre aparece nesta página. Mudanças relevantes serão comunicadas por e-mail.</p>

          <h2 className="font-heading text-lg font-bold text-primary mt-4">10. Foro</h2>
          <p>Fica eleito o foro da comarca de Fortaleza/CE para dirimir quaisquer controvérsias.</p>
        </section>
      </div>
    </div>
  )
}
