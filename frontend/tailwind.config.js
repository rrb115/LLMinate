/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        sky: "#0284c7",
        mint: "#10b981",
        sand: "#fef3c7"
      }
    },
  },
  plugins: [],
};
