import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#15201c",
        moss: "#52665a",
        sage: "#7f9b87",
        blush: "#d98c8c",
        linen: "#f7f3ee",
        mist: "#e9f0ec",
      },
      boxShadow: {
        soft: "0 18px 50px rgba(21, 32, 28, 0.08)",
      },
    },
  },
  plugins: [],
};

export default config;
