# Celesto

Celesto gives AI agents disposable computers. This glossary fixes one word per
idea so the docs, the CLI, and the SDKs read the same way.

## Language

### Where things run

**Computer**:
An isolated, disposable virtual machine that Celesto starts for an agent, on
your machine or in Celesto Cloud.
_Avoid_: sandbox, box, VM, instance, environment, machine (for the computer
Celesto starts)

**Your machine**:
The laptop or server where you install and run Celesto.
_Avoid_: your computer, host, local box

**Local computer**:
A computer that runs on your machine.
_Avoid_: local sandbox, local VM

**Cloud computer**:
A computer that runs in Celesto Cloud.
_Avoid_: cloud sandbox, cloud VM, remote box

### What a computer can show

**Desktop**:
A visible graphical screen on a computer that you or an agent can watch and
operate. A computer without one is a **minimal computer**.
_Avoid_: Linux computer (as a separate kind of resource), desktop sandbox,
graphical sandbox

**Linux desktop computer**:
A computer created with `celesto computer create --desktop`. Open its desktop in
your browser with `celesto computer open`. In the CLI, `--desktop` flags refer
to this kind of computer. A macOS computer also has a desktop; open it with
`celesto computer desktop`.
_Avoid_: desktop computer (when you mean only this kind)

**Browser session**:
A Chromium browser in its own computer, for web-only automation. Its live view
is not a desktop.
_Avoid_: browser sandbox, browser computer, browser VM

### Starting and saving computers

**Image**:
The disk contents a computer starts from.
_Avoid_: rootfs, base box

**Snapshot**:
A saved copy of a computer's state that you can restore later.
_Avoid_: checkpoint, backup

## Older names you will still see

Some commands and API names predate this glossary. They mean **computer**:

- `celesto sandbox ...` is an alias for `celesto computer ...`.
- The TypeScript SDK's `celesto.sandboxes` creates minimal computers, and
  `celesto.computers` creates computers with a desktop.
- Fields such as `sandbox_id` and `vm_id` identify a computer.

Write "computer" in prose even when the code you show uses one of these names.
