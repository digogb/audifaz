/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        brand: '#8E44AD',
        'brand-light': '#F3E5F5',
        'brand-dark': '#6C3483',
        coral: '#F04747',
        tangerine: '#E67E22',
        gold: '#F39C12',
        sage: '#27AE60',
        'surface-bg': '#F8F9FD',
        'surface-card': '#FFFFFF',
        'surface-border': '#E8E8F0',
        'text-main': '#1A252F',
        'text-muted': '#4A5568',
        'text-faint': '#8896A5',
      },
      boxShadow: {
        card: '0px 4px 20px rgba(0, 0, 0, 0.06)',
        'card-hover': '0px 8px 30px rgba(0, 0, 0, 0.10)',
      },
      borderRadius: {
        card: '16px',
      },
    },
  },
  plugins: [],
}
