import { writeFile } from "node:fs/promises";
import path from "node:path";

/** Run guest shell fixtures on macOS; Ubuntu CI uses the real Linux tools. */
export async function installLinuxCommandShims(bin: string): Promise<void> {
  if (process.platform !== "darwin") return;
  for (const [name, script] of Object.entries({
    setsid: '#!/bin/sh\nexec "$@"\n',
    base64:
      '#!/bin/sh\nif [ "$1" = -d ] && [ "$#" = 2 ]; then exec /usr/bin/base64 -d -i "$2"; fi\nexec /usr/bin/base64 "$@"\n',
    find: String.raw`#!/usr/bin/env node
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process');
const args=process.argv.slice(2),formatIndex=args.indexOf('-printf');
if(formatIndex<0){const r=cp.spawnSync('/usr/bin/find',args,{stdio:'inherit'});process.exit(r.status??1)}
if(args[formatIndex+1]!=='%y\\0%s\\0%n\\0%p\\0'){process.stderr.write('Unsupported find format\n');process.exit(2)}
function walk(dir){for(const name of fs.readdirSync(dir)){const file=path.join(dir,name),s=fs.lstatSync(file);const type=s.isDirectory()?'d':s.isFile()?'f':s.isSymbolicLink()?'l':'?';process.stdout.write([type,s.size,s.nlink,'./'+file].join(String.fromCharCode(0))+String.fromCharCode(0));if(type==='d')walk(file)}}
walk('.');
`,
    mv: `#!/bin/sh
exact=false
no_clobber=false
while [ "$#" -gt 0 ]; do
  case "$1" in
    -T) exact=true; shift ;;
    -n) no_clobber=true; shift ;;
    --) shift; break ;;
    *) break ;;
  esac
done
if [ "$exact" = true ] && [ -d "$2" ]; then exit 1; fi
if [ "$no_clobber" = true ]; then exec /bin/mv -n "$@"; fi
exec /bin/mv "$@"
`,
    ln: `#!/bin/sh
if [ "$1" = -T ]; then shift; fi
if [ "$1" = -- ]; then shift; fi
if [ -d "$2" ]; then exit 1; fi
exec /bin/ln "$@"
`,
    stat: `#!/bin/sh
if [ "$1" = -c ]; then
  format="$2"; shift 2
  if [ "$1" = -- ]; then shift; fi
  case "$format" in
    %a) exec /usr/bin/stat -f %Lp "$@" ;;
    %s) exec /usr/bin/stat -f %z "$@" ;;
    %h) exec /usr/bin/stat -f %l "$@" ;;
  esac
fi
exec /usr/bin/stat "$@"
`,
    sha256sum: '#!/bin/sh\nexec /usr/bin/shasum -a 256 "$@"\n',
  }))
    await writeFile(path.join(bin, name), script, { mode: 0o755 });
}
