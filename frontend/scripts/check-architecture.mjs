import { readdir, readFile } from "node:fs/promises";
import { extname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import process from "node:process";

const root = fileURLToPath(new URL("../src/", import.meta.url));
const violations = [];

async function visit(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      await visit(path);
      continue;
    }
    if (![".ts", ".tsx"].includes(extname(entry.name))) continue;

    const source = await readFile(path, "utf8");
    const normalized = relative(root, path).replaceAll("\\", "/");
    if (source.includes("fetch(") && !normalized.startsWith("infrastructure/")) {
      violations.push(`${normalized}: fetch solo puede usarse en infraestructura.`);
    }
    if (normalized.startsWith("domain/") && /from ["'](?:react|.*(?:application|infrastructure|presentation))/.test(source)) {
      violations.push(`${normalized}: dominio no puede depender de capas externas.`);
    }
    if (normalized.startsWith("application/") && /from ["'](?:react|.*(?:infrastructure|presentation))/.test(source)) {
      violations.push(`${normalized}: aplicación no puede depender de infraestructura o presentación.`);
    }
    if (normalized.startsWith("presentation/") && /from ["'].*infrastructure/.test(source) && !normalized.endsWith("ApplicationContext.tsx")) {
      violations.push(`${normalized}: solo la raíz de composición puede importar infraestructura.`);
    }
  }
}

await visit(root);
if (violations.length) {
  console.error(violations.join("\n"));
  process.exit(1);
}
console.log("Arquitectura frontend: dependencias válidas.");
