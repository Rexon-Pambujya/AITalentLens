/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./app/**/*.{js,ts,jsx,tsx}', './components/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // "Paper" - cool near-white, not the generic cream (#F4F1EA) AI default
        paper: '#F5F6F8',
        paperRaised: '#FFFFFF',
        // "Ink" - near-black with a faint blue-violet undertone, not pure #000
        ink: {
          DEFAULT: '#14151F',
          soft: '#3A3C4C',
          faint: '#6C6E82',
        },
        line: '#E3E5EB',
        // "Lens" indigo - the brand/signal color. Deeper and more saturated
        // than a default Tailwind indigo-500, tuned specifically for this brief.
        lens: {
          DEFAULT: '#3B2FA3',
          soft: '#5A4FC4',
          faint: '#EEEBFA',
        },
        // Muted, desaturated semantic accents - used sparingly (badges,
        // small indicators), never as large fills.
        sage: { DEFAULT: '#3F7159', faint: '#E7F1EB' },
        clay: { DEFAULT: '#B65C43', faint: '#FBEBE6' },
        amber: { DEFAULT: '#C98A2C', faint: '#FBF0DE' },
      },
      fontFamily: {
        // Real deployments should swap these for next/font/google
        // (Fraunces / Inter / IBM Plex Mono) - see docs/design-decisions.md. System stacks
        // here approximate the intended feel without a network font fetch.
        display: ['Iowan Old Style', 'Palatino Linotype', 'Georgia', 'ui-serif', 'serif'],
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'ui-sans-serif', 'sans-serif'],
        mono: ['IBM Plex Mono', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      borderRadius: {
        sm: '6px',
        DEFAULT: '10px',
        lg: '14px',
      },
      boxShadow: {
        card: '0 1px 2px 0 rgba(20, 21, 31, 0.04), 0 1px 6px -2px rgba(20, 21, 31, 0.06)',
      },
    },
  },
  plugins: [],
};
