/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        bg: 'var(--bg)',
        surface: 'var(--surface)',
        'surface-raised': 'var(--surface-raised)',
        'surface-inset': 'var(--surface-inset)',
        border: 'var(--border)',
        'border-active': 'var(--border-active)',
        'text-primary': 'var(--text-primary)',
        'text-muted': 'var(--text-muted)',
        'text-dim': 'var(--text-dim)',
        'text-input': 'var(--text-input)',
        'accent-positive': 'var(--accent-positive)',
        'accent-positive-bg': 'var(--accent-positive-bg)',
        'accent-negative': 'var(--accent-negative)',
        'accent-negative-bg': 'var(--accent-negative-bg)',
        'accent-warning': 'var(--accent-warning)',
        'accent-warning-bg': 'var(--accent-warning-bg)',
        'accent-info': 'var(--accent-info)',
        'accent-info-bg': 'var(--accent-info-bg)',
        'node-company': 'var(--node-company)',
        'node-commodity': 'var(--node-commodity)',
        'node-sector': 'var(--node-sector)',
        'node-event': 'var(--node-event)',
      },
      fontFamily: {
        ui: 'var(--font-ui)',
        mono: 'var(--font-mono)',
      },
    },
  },
  plugins: [],
}
