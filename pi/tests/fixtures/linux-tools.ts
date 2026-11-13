import { writeFile } from "node:fs/promises";
import path from "node:path";

/** Run guest shell fixtures on macOS; Ubuntu CI uses the real Linux tools. */
export async function installLinuxCommandShims(bin: string): Promise<void> {
  if (process.platform !== "darwin") return;
  for (const [name, script] of Object.entries({
    setsid: '#!/bin/sh\nexec "$@"\n',
    base64:
      '#!/bin/sh\nif [ "$1" = -d ] && [ "$#" = 2 ]; then exec /usr/bin/base64 -d -i "$2"; fi\nexec /usr/bin/base64 "$@"\n',
    stat: '#!/bin/sh\nif [ "$1" = -c ] && [ "$2" = %a ]; then exec /usr/bin/stat -f %Lp "$3"; fi\nexec /usr/bin/stat "$@"\n',
  }))
    await writeFile(path.join(bin, name), script, { mode: 0o755 });
}
