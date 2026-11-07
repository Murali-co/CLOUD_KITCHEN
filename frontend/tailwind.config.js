/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cream: {
          50: "#FDFBF7",
          100: "#FAF7F2",
          200: "#F3ECE1",
          300: "#E9DFD0",
        },
        terracotta: {
          50: "#FFF5F0",
          100: "#FFE6DB",
          200: "#FFCBB5",
          300: "#FFA885",
          400: "#F87F55",
          500: "#EA580C",
          600: "#D9480F",
          700: "#C2410C",
          800: "#9A3412",
        },
        charcoal: {
          700: "#3F3F46",
          800: "#27272A",
          900: "#18181B",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
      },
    },
  },
  plugins: [],
};
