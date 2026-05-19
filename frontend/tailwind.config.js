/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // ---- semantic tokens (preferred) ----
        bg: 'var(--color-bg)',
        'bg-mid': 'var(--color-bg-mid)',
        'bg-surface': 'var(--color-bg-surface)',
        'bg-terminal': 'var(--color-bg-terminal)',
        primary: 'var(--color-text)',
        muted: 'var(--color-text-muted)',
        subtle: 'var(--color-text-subtle)',
        accent: 'var(--color-accent)',
        'accent-hover': 'var(--color-accent-hover)',
        'accent-text': 'var(--color-accent-text)',
        'accent-soft': 'var(--color-accent-soft)',
        secondary: 'var(--color-secondary)',
        'secondary-hover': 'var(--color-secondary-hover)',
        danger: 'var(--color-danger)',
        success: 'var(--color-success)',

        // ---- legacy aliases (compat com classes pré-tematizadas) ----
        // todas apontam pros tokens semânticos, então mudam com o tema
        'text-primary': 'var(--color-text)',
        'text-muted': 'var(--color-text-muted)',
        'text-blue': 'var(--color-accent-text)',
        'accent-blue': 'var(--color-accent)',
        'accent-orange': 'var(--color-danger)',
        'terminal-orange': 'var(--color-danger)',
        'bg-base': 'var(--color-bg)',
      },
      fontFamily: {
        sans: ['var(--font-body)', 'system-ui', 'sans-serif'],
        heading: ['var(--font-heading)', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
      },
      borderRadius: {
        btn: '10px',
        card: '10px',
        container: '12px',
        hero: '16px',
      },
      backdropBlur: {
        glass: '8px',
      },
    },
  },
  plugins: [],
}
