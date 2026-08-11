/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0B1220",
        mist: "#E8EEF7",
        sand: "#F7F3EC",
        coral: "#E85D4C",
        pine: "#1F6B5A",
        slate: "#5B6B7C",
      },
      fontFamily: {
        display: ["var(--font-display)", "Georgia", "serif"],
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
      },
      backgroundImage: {
        "hero-glow":
          "radial-gradient(ellipse 80% 60% at 50% -20%, rgba(31,107,90,0.25), transparent), radial-gradient(ellipse 50% 40% at 90% 10%, rgba(232,93,76,0.15), transparent)",
      },
    },
  },
  plugins: [],
};
