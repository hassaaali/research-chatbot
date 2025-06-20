import { defineConfig } from "eslint/config";
import js from "@eslint/js";

export default defineConfig([
  js.configs.recommended,
  {
    files: ["**/*.js"],
    languageOptions: {
      globals: {
        window: "readonly",
        document: "readonly",
        console: "readonly",
        XMLHttpRequest: "readonly",
        fetch: "readonly",
        setTimeout: "readonly",
        localStorage: "readonly",
      },
    },
    rules: {
      // Offload noise
      "no-unused-vars": "off",
      "no-console": "off",

      // Keep runtime-relevant errors
      "no-undef": "error",
      "no-unexpected-multiline": "error",
      "no-unreachable": "error",
      "no-dupe-keys": "error",
      "no-func-assign": "error",
      "no-const-assign": "error",
      "no-import-assign": "error",
    },
  },
]);