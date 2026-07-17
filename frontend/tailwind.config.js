/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        primary: {
          50: '#FFFDF2',
          100: '#FFF6CC',
          200: '#FFEE99',
          300: '#FFE566',
          400: '#FFD633',
          500: '#FFCC00',
          600: '#E6B800',
          700: '#B38F00',
          800: '#8C7000',
          900: '#665200',
        },
        accent: {
          50: '#FFF8F0',
          100: '#FFEDD5',
          400: '#FB923C',
          500: '#F97316',
          600: '#EA580C',
        },
        bee: {
          black: '#000000',
          dark: '#1A1A1A',
          gray: '#2D2D2D',
          light: '#F5F5F0',
        },
      },
    },
  },
  plugins: [],
};
