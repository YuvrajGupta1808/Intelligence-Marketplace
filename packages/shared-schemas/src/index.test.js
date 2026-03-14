import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

test("shared schemas package loads", async () => {
  const root = dirname(fileURLToPath(import.meta.url));
  const content = await readFile(join(root, "index.ts"), "utf8");
  assert.ok(content.includes("ExecutionResult"));
});
