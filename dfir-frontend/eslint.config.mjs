import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const compat = new FlatCompat({ baseDirectory: __dirname });

const config = [...compat.extends("next/core-web-vitals", "next/typescript")];

export default config.map(c => ({
  ...c,
  ignores: ["vendor/**", ".next/**", ".next-production/**", "next-env.d.ts", ...(c.ignores || [])]
}));
