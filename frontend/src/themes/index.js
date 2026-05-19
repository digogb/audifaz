/* Theme registry. Cada tema tem:
 *   - slug: string usada em data-theme="..." no <html>
 *   - mode: 'dark' | 'light' (color-scheme + lógica condicional)
 *   - fonts: links Google Fonts a serem carregados quando o tema está ativo
 *
 * As cores e variáveis CSS reais ficam em src/index.css, agrupadas por
 * [data-theme="<slug>"]. Esta tabela é só metadado de runtime.
 */

export const themes = {
  audifaz: {
    slug: 'audifaz',
    name: 'AudiFaz Dark',
    mode: 'dark',
    fonts: [],
  },
  lexlumina: {
    slug: 'lexlumina',
    name: 'LexLumina Legal',
    mode: 'light',
    fonts: [
      'https://fonts.googleapis.com/css2?family=Merriweather:wght@400;600;700&family=Inter:wght@400;500;600;700&display=swap',
    ],
  },
}

export const DEFAULT_THEME = 'audifaz'

export function resolveTheme(slug) {
  return themes[slug] || themes[DEFAULT_THEME]
}
