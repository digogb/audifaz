import { Link } from 'react-router-dom'
import { useBrand } from '../contexts/BrandContext'

export default function Privacidade() {
  const { meta: brand } = useBrand()
  return (
    <div className="min-h-screen px-4 py-10">
      <div className="max-w-2xl mx-auto space-y-5">
        <Link to="/" className="text-[12px] text-accent-text hover:underline">← Voltar</Link>
        <h1 className="font-heading text-3xl font-extrabold text-primary">Política de Privacidade</h1>
        <p className="text-[12px] text-subtle">Versão 2026-05-19 · Em conformidade com a Lei 13.709/2018 (LGPD)</p>

        <section className="space-y-3 text-[13px] text-muted leading-relaxed">
          <h2 className="font-heading text-lg font-bold text-primary mt-4">1. Dados coletados</h2>
          <p>O {brand.nome} coleta apenas o estritamente necessário:</p>
          <ul className="list-disc list-inside space-y-1 pl-2">
            <li><strong className="text-primary">Cadastro:</strong> nome de usuário, e-mail, senha (hash bcrypt).</li>
            <li><strong className="text-primary">Conteúdo de estudo:</strong> tópicos lidos, questões respondidas, redações submetidas, anotações, simulados registrados.</li>
            <li><strong className="text-primary">Pagamento:</strong> processado pelo Mercado Pago — não armazenamos número de cartão. Mantemos o ID do pagamento e o valor.</li>
            <li><strong className="text-primary">Logs técnicos:</strong> IP, user-agent e timestamps de requisições para auditoria de segurança. Retenção: 90 dias.</li>
          </ul>

          <h2 className="font-heading text-lg font-bold text-primary mt-4">2. Finalidade</h2>
          <p>Os dados são usados para: prestar o serviço (gerar material e correção de redação), executar contratos (assinaturas), cumprir obrigações legais (fiscal/tributário) e garantir segurança.</p>
          <p>Não vendemos, alugamos ou compartilhamos dados pessoais com terceiros para fins de marketing.</p>

          <h2 className="font-heading text-lg font-bold text-primary mt-4">3. Bases legais (LGPD art. 7º)</h2>
          <ul className="list-disc list-inside space-y-1 pl-2">
            <li>Execução de contrato (uso do serviço)</li>
            <li>Consentimento (cadastro e aceite dos termos)</li>
            <li>Cumprimento de obrigação legal (registro fiscal)</li>
            <li>Legítimo interesse (logs de segurança)</li>
          </ul>

          <h2 className="font-heading text-lg font-bold text-primary mt-4">4. Operadores e subcontratados</h2>
          <p>Para prestar o serviço, dados são processados também por:</p>
          <ul className="list-disc list-inside space-y-1 pl-2">
            <li><strong className="text-primary">Anthropic (Claude):</strong> conteúdo enviado para geração de material e correção de redação. <a className="text-accent-text" href="https://www.anthropic.com/legal/privacy" target="_blank" rel="noreferrer">Política Anthropic</a>.</li>
            <li><strong className="text-primary">Google Cloud (TTS):</strong> texto convertido em áudio. <a className="text-accent-text" href="https://policies.google.com/privacy" target="_blank" rel="noreferrer">Política Google</a>.</li>
            <li><strong className="text-primary">Mercado Pago:</strong> processamento de pagamento Pix. <a className="text-accent-text" href="https://www.mercadopago.com.br/privacidade" target="_blank" rel="noreferrer">Política Mercado Pago</a>.</li>
            <li><strong className="text-primary">Sentry:</strong> registro de erros técnicos (sem PII além do user-agent).</li>
          </ul>

          <h2 className="font-heading text-lg font-bold text-primary mt-4">5. Direitos do titular (LGPD art. 18)</h2>
          <p>Você pode, a qualquer momento:</p>
          <ul className="list-disc list-inside space-y-1 pl-2">
            <li><strong className="text-primary">Acessar:</strong> exportar todos os seus dados em JSON via <em>Configurações → Exportar meus dados</em>.</li>
            <li><strong className="text-primary">Corrigir:</strong> alterar e-mail e senha via Configurações.</li>
            <li><strong className="text-primary">Eliminar:</strong> excluir conta permanentemente via <em>Configurações → Excluir conta</em>.</li>
            <li><strong className="text-primary">Portar:</strong> o JSON exportado é o formato de portabilidade.</li>
            <li><strong className="text-primary">Revogar consentimento:</strong> ao excluir a conta.</li>
          </ul>

          <h2 className="font-heading text-lg font-bold text-primary mt-4">6. Segurança</h2>
          <p>Senhas armazenadas com hash bcrypt. Trânsito sempre por HTTPS (TLS). Banco de dados acessível apenas via aplicação. Backups diários com retenção de 30 dias.</p>

          <h2 className="font-heading text-lg font-bold text-primary mt-4">7. Cookies</h2>
          <p>Usamos apenas o necessário para autenticação (token JWT armazenado em localStorage). Não usamos cookies de rastreamento ou publicitários.</p>

          <h2 className="font-heading text-lg font-bold text-primary mt-4">8. Encarregado (DPO) e contato</h2>
          <p>Para exercer direitos LGPD ou esclarecer dúvidas: <strong className="text-primary">privacidade@anajud.com.br</strong>.</p>

          <h2 className="font-heading text-lg font-bold text-primary mt-4">9. Alterações</h2>
          <p>Esta política pode ser atualizada. Mudanças relevantes serão comunicadas por e-mail.</p>
        </section>
      </div>
    </div>
  )
}
