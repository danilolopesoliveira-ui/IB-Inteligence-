/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: '#12121a',
          50: '#1a1a2e',
          100: '#22223a',
          200: '#2a2a3e',
          300: '#353548',
        },
        gold: {
          DEFAULT: '#d4a853',
          light: '#f0d78c',
          dark: '#b8942e',
          muted: 'rgba(212,168,83,0.15)',
        },
        accent: {
          blue: '#3b82f6',
          green: '#10b981',
          red: '#ef4444',
          amber: '#f59e0b',
          purple: '#8b5cf6',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        editorial: ['"Playfair Display"', 'Georgia', 'serif'],
      },
    },
  },
  plugins: [],
}
