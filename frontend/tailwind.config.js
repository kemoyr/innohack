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
          50: '#FFFEF5',
          100: '#FFF9E0',
          200: '#FFF2B8',
          300: '#FFEA8A',
          400: '#FFD93D',
          500: '#FFC800',
          600: '#E6B400',
          700: '#BF9600',
          800: '#997700',
          900: '#735900',
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
