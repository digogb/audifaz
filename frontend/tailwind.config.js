/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        'bg-base': '#0B1527',
        'bg-mid': '#112040',
        'bg-surface': '#1A2D50',
        'bg-terminal': '#090F1C',
        'accent-blue': '#2D72D9',
        'text-blue': '#5B9EF4',
        'accent-orange': '#D4845A',
        'terminal-orange': '#E8865A',
        'text-primary': '#FFFFFF',
        'text-muted': '#A8B5CC',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
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
      boxShadow: {
        'glass-glow': '0 0 0 0.5px rgba(255,255,255,0.10)',
      },
    },
  },
  plugins: [],
}
