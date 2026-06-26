---
layout: post
title:  "Chasing a Password Through a MIPS Binary: PIC From First Principles"
date:   2026-06-26 00:00:01 +0530
categories: embedded mips reversing security
image:
  path: /assets/images/gdbserver/elf-hex-dump.png
  alt: Hex dump of the MIPS ELF binary
---
This post is the conceptual core of everything behind my [OSS India 2026 talk](https://ossindia2026.sched.com/event/3a9b6eb190a4da280b779d0e20474846) on the Alphion
ASEE-1447 router. Everything else I did — the [cross-compiled `gdbserver`, the live
debugging](/posts/gdbserver-build-and-deploy/), the binary patch — only makes sense once you understand how a stripped MIPS
PIC binary finds a hardcoded string like a password, with no symbol names and no
obvious "load this address" instruction anywhere in sight.

If you've only ever read x86 disassembly, MIPS will look bizarre at first. There's no
instruction that directly encodes a 32-bit address. Loading a string means a chain of
several instructions, an extra table in memory, and a register that has to be set up
correctly before any of it works. This post builds that chain from nothing.

The running example throughout is the actual function I found in `cli` — the router's
authentication binary — that checks a hardcoded password.

---

## 1. Why MIPS instructions can't just hold an address

MIPS instructions are a fixed 32 bits wide, always. Compare that to x86, where
instructions vary in length and can carry a full 32-bit or 64-bit immediate value
inline.

A MIPS instruction needs room for an opcode, register numbers, and — for the
instructions that take an immediate value — only 16 bits left over for that immediate.
This is the **I-type** instruction format:

```
 31      26 25     21 20     16 15                0
┌──────────┬─────────┬─────────┬──────────────────┐
│  opcode  │   rs    │   rt    │   16-bit immediate │
└──────────┴─────────┴─────────┴──────────────────┘
   6 bits     5 bits    5 bits        16 bits
```

A 16-bit signed immediate can only represent values from -32768 to +32767. A virtual
address like `0x4188d4` (the address of one of the router's hardcoded passwords) is
nowhere close to fitting in that.

So how does code ever get a 32-bit address into a register? Two instructions, each
contributing half:

```
lui   $reg, upper16        ; load upper 16 bits, shifted left 16, lower 16 zeroed
addiu $reg, $reg, lower16   ; add the lower 16 bits
```

`lui` (Load Upper Immediate) puts a 16-bit value into the top half of a register and
zeroes the bottom half. `addiu` (Add Immediate Unsigned, though the immediate itself is
sign-extended) adds a signed 16-bit value to whatever's already there. Together they
can construct any 32-bit value, two pieces at a time.

This pattern is everywhere in non-PIC MIPS code, where the linker can bake an absolute
address straight into a `lui`/`addiu` pair at link time. But `cli` isn't using that
pattern for its strings — and the reason why is the whole point of this post.

---

## 2. Why a MIPS executable needs PIC at all

PIC stands for **Position-Independent Code** — code that runs correctly no matter what
address it's loaded at. The classic justification is shared libraries: a `.so` file
gets mapped into many different processes, often at a different address in each one,
so it can't have absolute addresses baked into its instructions.

`cli` is not a shared library. It's a standalone executable, with its own dedicated
virtual address space — the usual justification for PIC doesn't apply. So why does it
have all the PIC machinery (GOT, `$gp`, PLT stubs) at all?

Two things converge here, specific to how this router's firmware is built:

**First — `cli` dynamically links against 14 shared libraries** (`librtk.so`,
`libssl.so`, `libcrypto.so`, and others). Those libraries get mapped at runtime, at
addresses `cli` can't know about at compile time. To call into them, `cli` needs the
same GOT-based indirection a `.so` file would need — regardless of whether `cli` itself
is PIC.

**Second — Realtek's IPC architecture uses `dlsym()`** to look up functions inside
`cli` by name at runtime, from other processes. For `dlsym()` to find a symbol inside an
*executable* (not a `.so`), that executable has to be linked with `--export-dynamic`,
which keeps the symbol table in `.dynsym` rather than discarding it. Once you're linked
that way, the whole PIC apparatus — GOT, PLT, the `$gp` discipline — comes along with
it, even for code that didn't strictly need position independence for its own sake.

This turns out to matter for the security analysis too: `strip` only removes
`.symtab`, never `.dynsym`. Because `--export-dynamic` forced function names into
`.dynsym`, stripping the binary didn't make it anonymous — function names for anything
called externally are still sitting right there in the binary, readable with
`readelf --dyn-syms`. The internal auth-checking function isn't exported this way (it's
never called via `dlsym`), so it has no name at all — but everything it calls into
*does* have a name, which is exactly the thread that let me trace into it.

---

## 3. The Global Offset Table (GOT)

The GOT is a table of pointers, sitting in the binary's data segment, filled in partly
by the linker (for things resolvable at link time) and partly by the dynamic linker at
process startup (for things resolved at runtime, like library function addresses).

Instead of an instruction saying "the string is at `0x4188d4`," PIC code says
"read whichever address is sitting in GOT slot N, then adjust by a small constant" —
and the small constant fits in that 16-bit immediate field.

For `cli`, the GOT lives at virtual address `0x432120`, confirmed with:

```sh
mips-linux-gnu-readelf -S cli | grep -A1 "\.got"
```

That's a table of `0x454` bytes — 277 four-byte slots, each holding a 32-bit address.

---

## 4. $gp: the register that anchors everything

`$gp` (register 28, the "global pointer") is the register MIPS PIC code uses to find
the GOT. Every GOT-relative load is of the form:

```
lw  $reg, offset($gp)
```

where `offset` is a signed 16-bit immediate. That's a strict requirement: any single
load instruction can only reach addresses within `±32KB` of wherever `$gp` currently
points.

### Why $gp sits in the *middle* of the GOT, not the start

If `$gp` pointed at the very start of the GOT, only positive offsets would make sense,
and you'd only be able to address the first 32KB of the table. By placing `$gp` near
the *middle* of the GOT, both positive and negative signed 16-bit offsets get used,
doubling the effective reach — up to 64KB of GOT can be addressed from a single `$gp`
value. For `cli`, the chosen midpoint is `0x43a110`.

### How $gp gets set — the PIC prologue

`$gp` is just a register — nothing sets it automatically. Every function in a MIPS PIC
binary has to compute it fresh, in its own prologue, using a three-instruction pattern:

```asm
lui   $gp, %hi(_gp_disp)
addiu $gp, $gp, %lo(_gp_disp)
addu  $gp, $gp, $t9
```

The first two instructions reconstruct a 32-bit constant called `_gp_disp` — the
**distance from this specific function's entry address to the GOT midpoint** — using
the same `lui`/`addiu` split described in Section 1. The third instruction adds `$t9`,
which by MIPS PIC calling convention must already hold **this function's own entry
address** at the moment the function starts executing.

Why does this work for every function in the binary, no matter where it's located?
Because the linker computes a *different* `_gp_disp` constant for each function — the
constant is always exactly `GOT_midpoint − this_function's_address`. Add the function's
own address back in, and the function's address term cancels out, leaving the same
`$gp = GOT_midpoint` regardless of which function you're in. The displacement is
function-relative; the result is binary-global.

This is also why `$t9` matters so much in MIPS PIC: the calling convention requires
every caller to load the callee's address into `$t9` before calling it (the `jalr $t9`
instruction does the jump while leaving that contract satisfied). If `$t9` doesn't hold
the right value when a function's prologue runs, the `addu $gp, $gp, $t9` step computes
garbage, and every GOT-relative load inside that function silently resolves to the
wrong address.

### Confirming this against the real binary

The auth-checking function in `cli` starts at `0x40af0c`. Its prologue:

```
40af0c:  3c1c0003  lui   gp, 0x3
40af10:  279cf204  addiu gp, gp, -3580
40af14:  0399e021  addu  gp, gp, t9
```

Worked out by hand:

```
lui  gp, 0x3        →  gp = 0x00030000
addiu gp, gp, -3580 →  gp = 0x0002f204
addu gp, gp, t9      →  gp = 0x0002f204 + 0x40af0c = 0x43a110
```

`0x2f204` is exactly `0x43a110 − 0x40af0c` — the GOT midpoint minus this function's own
address — split into the `lui`/`addiu` halves a linker would produce. The computed
result, `0x43a110`, matches the GOT midpoint independently confirmed from the section
layout in Section 3. Two completely different derivation paths landing on the same
number is about as solid a confirmation as static analysis gets.

I also decoded the raw instruction encoding by hand to double check, since I didn't
want to take any disassembler's word for it without being able to verify it myself.
Take `0x3c1c0003`:

```
0x3c1c0003 in binary:
  001111 00000 11100 0000000000000011
  └─op──┘└rs──┘└rt──┘└────imm───────┘
  op = 0x0f → LUI
  rt = 28   → $gp
  imm = 0x0003
```

Matches `lui $gp, 0x3` exactly.

This is also the three-instruction sequence you can watch execute live under
`gdbserver` — each `si` step in [the remote debugging session](/posts/gdbserver-build-and-deploy/#stepping-through-the-function-prologue----watching-gp-get-set-up)
updates the register pane and makes the calculation concrete.

### Why $gp gets saved and restored constantly

`$gp` is stable *within* a single function — once the prologue computes it, it stays
correct for that whole function, because the function never moves. But it has to be
saved before calling into another function and restored after, because the callee will
overwrite `$gp` with *its own* prologue computation (a different function-relative
displacement, recall, but resolving to the same absolute GOT midpoint — the value is
the same, but the call itself clobbers the register in the process, and a function
located in another shared object may compute a completely different `$gp`).

You can see this pattern repeating constantly in the disassembly:

```
sw  gp, 16(sp)     ; save gp on the stack before a call
...
jalr t9            ; call something
...
lw  gp, 16(sp)     ; restore gp after returning
```

---

## 5. Following an actual GOT load to a string

This is the part that ties everything together — actually finding where a specific
hardcoded value lives, using only the GOT and `$gp`, with no symbol table to lean on.

The target: the string `"masnb01012021#"` — one of two hardcoded passwords found in
`.rodata`. Its file offset (from `strings -t x`) converts to virtual address `0x4188d4`
once you add the binary's load base (`0x400000`).

The actual instructions that produce this address, from inside the auth function:

```
40af60:  lw    a1, -32740(gp)     ; a1 = GOT slot value
40af6c:  addiu a1, a1, -30508     ; a1 = that value + (-30508) = 0x4188d4
```

### Step 1 — find the GOT slot

`-32740` is the offset from `$gp`. Since `$gp = 0x43a110`:

```
slot_address = $gp + offset = 0x43a110 + (-32740) = 0x43212c
```

### Step 2 — read what's actually stored there

```sh
mips-linux-gnu-readelf -x .got cli
```

Slot `0x43212c` holds the value `0x420000`. This isn't the string's address — it's a
**GOT anchor**: a base value the linker chose specifically because the target string is
within signed-16-bit reach of it.

### Step 3 — confirm the final addiu closes the loop

```
0x420000 + (-30508) = 0x4188d4
```

Which is exactly the string's virtual address. The two values — the GOT slot's stored
base, and the `addiu` immediate baked into the instruction — only mean anything when
combined. Neither one alone tells you anything; searching the binary for the literal
bytes `4188d4` will never find this, because that 32-bit value never appears intact
anywhere in the instruction stream.

### The general method, stripped of this specific example

This is the deterministic way to find where *any* GOT-anchored value is loaded in PIC
MIPS code, without guessing:

1. Get the target virtual address (from `strings -t x` + load base, or wherever else
   you know the data lives).
2. Dump every GOT slot (`readelf -x .got`).
3. For each slot value `B`, check whether `target − B` fits in a signed 16-bit integer
   (`-32768` to `32767`). Slots where it does are candidate anchors.
4. For each candidate, compute the required `addiu` immediate and grep the disassembly
   for that exact immediate value following a `lw ... ($gp)` that reads that slot's
   offset.
5. Confirm by re-deriving the target address from the matched instructions.

I did this with a short script comparing every GOT slot's value against the target
address — small enough to write inline, but the logic above is exactly what it does. No
disassembler magic, no assumptions — every number traced back to something readable
directly off the binary.

---

## 6. Resolving a dynamic call: how `strcmp` gets found with no symbol name

The same auth function calls `strcmp` to compare the password. Since `cli` is stripped
and `strcmp` lives in a different shared library, the call doesn't go directly to a
known address — it goes through a **lazy-binding stub**.

```
40af64:  lw    t9, -32280(gp)    ; t9 = address of the stub
40af68:  jalr  t9                 ; call it
```

The GOT slot at offset `-32280` from `$gp` (i.e. `0x4322f8`) doesn't hold `strcmp`'s
real address — at least not until it's been resolved once. It holds the address of a
small stub. Disassembling that stub directly:

```
416a90:  lw    t9, -32752(gp)    ; t9 = dynamic linker's resolver
416a94:  move  t7, ra             ; save return address
416a98:  jalr  t9                 ; call the resolver
416a9c:  li    t8, 122            ; symbol index, sitting in the delay slot
```

The `li t8, 122` is the actual point of interest. MIPS lazy-binding stubs put the
**dynamic symbol table index** of the function being resolved directly into a register,
in the delay slot of the jump to the resolver. Look that index up:

```sh
mips-linux-gnu-readelf --dyn-syms cli | awk '$1 == "122:"'
```

`.dynsym[122]` is `strcmp@GLIBC_2.0`. That's how you can identify *any* dynamically
resolved call site in a stripped MIPS binary — find the stub, read the `li t8, N` in
its delay slot, and look up index `N` in `.dynsym`. No decompiler needed, and it works
even though the call site itself carries no symbol name whatsoever.

A quick note on terminology here, since "PLT" gets thrown around loosely: MIPS doesn't
implement the PLT the same way x86 does. The mechanism above — `.MIPS.stubs`, a GOT
slot per external function, and the symbol index embedded in the delay slot — is the
MIPS-specific equivalent, and it's worth being precise about that distinction if anyone
familiar with x86 PLT structure pushes back on the terminology.

---

## 7. Branch delay slots — the other MIPS gotcha

Every MIPS branch and jump instruction (`beq`, `bne`, `jr`, `jalr`, `j`, `jal`, and
their variants) is followed by exactly one instruction that **always executes**, even
when the branch is taken — this is the delay slot, and it exists because of MIPS's
pipelined instruction fetch design.

This shows up constantly in `cli`'s disassembly. For example, in the success path
after the password check:

```
40af70:  bnez  v0, 40af98     ; if strcmp result != 0, branch to fail path
40af74:  lw    gp, 16(sp)     ; delay slot — executes regardless of branch outcome
```

That `lw gp, 16(sp)` runs whether or not the branch is taken — it's not "the first
instruction of the not-taken path," it's unconditional. Reading MIPS disassembly
correctly means always checking the instruction right after a branch and asking "does
this need to run either way?"

This also explains a quirk worth knowing: `bnez reg, target` and
`bne reg, $zero, target` are the exact same instruction — `bnez` is a pseudo-mnemonic
the disassembler chooses to display, encoded identically to `bne` against the hardwired
`$zero` register. There's no separate "branch if not zero" opcode; it's just `bne`
against a register that's wired to always read 0.

---

## 8. The full picture: the password-check function

Putting every mechanism above together, here's the complete authentication function at
`0x40af0c`, annotated with what each line is actually doing:

```
40af0c:  lui   gp,0x3            ; PIC prologue: gp = 0x30000
40af10:  addiu gp,gp,-3580       ;   gp = 0x2f204
40af14:  addu  gp,gp,t9          ;   gp = 0x2f204 + entry_addr = 0x43a110
40af18:  addiu sp,sp,-32         ; allocate 32-byte stack frame
40af1c:  sw    ra,28(sp)         ; save return address

; ... (branch on a global flag, omitted for brevity) ...

; ============== PASSWORD PROMPT ==============
40af4c:  lw    t9,-31764(gp)     ; t9 = getpass (via GOT)
40af50:  jalr  t9                ; call getpass(...)
40af54:  addiu a0,a0,-30528      ; (delay slot) a0 = "Enter Password: "

40af58:  lw    gp,16(sp)         ; restore gp after the call
40af5c:  move  a0,v0             ; a0 = user input (getpass's return value)
40af60:  lw    a1,-32740(gp)     ; a1 = GOT anchor (0x420000)
40af64:  lw    t9,-32280(gp)     ; t9 = strcmp (via lazy-binding stub)
40af68:  jalr  t9                ; call strcmp(user_input, hardcoded_password)
40af6c:  addiu a1,a1,-30508      ; (delay slot) a1 = "masnb01012021#"

40af70:  bnez  v0,0x40af98       ; if strcmp != 0 -> fail path
40af74:  lw    gp,16(sp)         ; (delay slot) restore gp, always runs

; ============== PASSWORD CORRECT ==============
40af78:  lw    a0,-32740(gp)     ; a0 = GOT anchor again
40af7c:  lw    t9,-32168(gp)     ; t9 = va_cmd
40af80:  lw    ra,28(sp)         ; restore return address
40af84:  addiu a0,a0,-30536      ; a0 = "/bin/sh"
40af88:  move  a1,zero           ; a1 = NULL
40af8c:  li    a2,1              ; a2 = 1
40af90:  jr    t9                ; tail call: va_cmd("/bin/sh", NULL, 1)
40af94:  addiu sp,sp,32          ; (delay slot) deallocate stack — never returns here

; ============== PASSWORD WRONG ==============
40af98:  lw    ra,28(sp)         ; restore return address
40af9c:  jr    ra                ; return to caller
40afa0:  addiu sp,sp,32          ; (delay slot) deallocate stack
```

Every single GOT slot, every `addiu` immediate, and the `lui`/`addiu`/`addu` prologue —
all traced back to first principles rather than taken on a disassembler's word for it.

This is also the function I later patched (flipping `bnez` to `beqz` at `0x40af70`, a
single bit) and the one I attached [`gdbserver` to for the live remote-debugging
demo](/posts/gdbserver-build-and-deploy/) — everything downstream of this post builds on
the derivation above.

---

## What I haven't fully nailed down

A few things worth being upfront about, since "document everything" should include the
edges of what's solid:

- **The exact mapping of GOT slot to symbol for slots resolved at link time** (as
  opposed to the lazy-binding-stub mechanism in Section 6, which only applies to
  dynamically resolved external calls) hasn't been walked through with the same rigor.
  Some GOT entries are filled by the static linker directly rather than via a stub —
  worth a pass if a question comes up about *every* slot's origin, not just the ones
  behind stubs.
- **MIPS o32 ABI stack frame conventions** — why exactly 32 bytes are allocated when
  only 28 are actually used (the 16-byte "argument home area" mandated by the ABI even
  when arguments are passed in registers) was confirmed during the [GDB live-debugging
  session](/posts/gdbserver-build-and-deploy/) but isn't written up here in the same
  first-principles depth as the GOT/`$gp` material.
- **Relocation types** — I've talked about "the linker bakes in a constant," but the
  actual ELF relocation type names involved (`R_MIPS_HI16`, `R_MIPS_LO16`,
  `R_MIPS_GOT16`, `R_MIPS_CALL16`, etc.) haven't been explicitly identified against this
  binary's `.rel.dyn`/`.rela.dyn` section. Naming the actual relocation type at each
  step would tighten the connection between "the linker did this" and the concrete ELF
  mechanism responsible.
- **Why this function has no symbol name at all** is explained at the "internal,
  non-exported function" level in Section 2, but I haven't separately confirmed there's
  no other static reference to it (e.g. a function pointer table) that might still
  carry a name elsewhere in the binary worth checking before calling the naming story
  fully closed.

None of these gaps affect the correctness of anything demonstrated live — they're places
where the explanation could go one level deeper if pressed, not places where the
current understanding is shaky.
