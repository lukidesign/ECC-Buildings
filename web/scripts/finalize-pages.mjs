import { copyFile, mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { join } from "node:path";

const output = fileURLToPath(new URL("../pages-dist/", import.meta.url));
const entry = join(output, "index.html");
const routes = [
  "buildings",
  "buildings/bt_appart",
  "buildings/bt_appart/bt_appart_el_room",
];

for (const route of routes) {
  const directory = join(output, route);
  await mkdir(directory, { recursive: true });
  await copyFile(entry, join(directory, "index.html"));
}
await copyFile(entry, join(output, "404.html"));
await writeFile(join(output, ".nojekyll"), "");
