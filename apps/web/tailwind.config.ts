import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: "#0f1419",
          elevated: "#1a2332",
          overlay: "#243447",
        },
        accent: {
          DEFAULT: "#00d4aa",
          muted: "#00a884",
          dim: "rgba(0, 212, 170, 0.15)",
        },
        border: {
          DEFAULT: "#2d3d52",
          focus: "#00d4aa",
        },
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-geist-mono)", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
