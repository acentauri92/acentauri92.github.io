---
layout: page
title: "Issues Along the Way: Building gdbserver for MIPS"
permalink: /notes/gdbserver-issues-along-the-way/
---

This is the companion to [Cross-Compiling gdbserver for a MIPS Router with
Buildroot](/posts/gdbserver-build-and-deploy/). That post shows the clean path. This one
covers what I tried first, why it didn't work, and why I ended up on GDB 13.2
specifically rather than something newer.

---

## Why I couldn't just download a prebuilt gdbserver

Before touching a cross-compiler, the obvious first move is: someone has probably
already built this. `gdbserver` for MIPS isn't exotic — surely a static binary exists
somewhere that I can just `wget` and run.

### First lead: guyush1/gdb-static

[guyush1/gdb-static](https://github.com/guyush1/gdb-static) is a GitHub project that
publishes static, musl-based builds of `gdb` and `gdbserver` for a range of
architectures, kept up to date with recent GDB releases. My laptop had `gdb-multiarch`
at version 15.1, so the natural move was to grab the matching `gdb-15.1-static` release
and look for a MIPS binary in its release assets.

It wasn't there. The release had binaries for several architectures, but no MIPS build
at all — not even little-endian, let alone the big-endian one this router needs.

### Second lead: a different prebuilt MIPS binary

I found a separately-sourced static `gdbserver` binary built against GDB 15.2 for MIPS.
Different GDB minor version, but the GDB remote serial protocol is stable across minor
releases, so a version mismatch with the 15.1 client wasn't expected to be a real
problem.

Running it on the router told a different story:

```
# ./gdbserver
Illegal instruction (core dumped)
# ./gdbserver --version
Illegal instruction (core dumped)
```

It crashed before even printing a version string — before argument parsing, before
anything resembling normal program logic runs. That's a strong signal: the fault isn't
in *what* the program does, it's in the raw machine code itself. Somewhere in the
binary's startup path (or possibly throughout it) there's an instruction the CPU
physically doesn't implement.

The router's CPU is a MIPS interAptiv core — a specific MIPS32 Release 2 implementation,
not a generic "MIPS" target. A binary built for a different MIPS32r2 variant, or for a
later MIPS revision the toolchain assumed was safe to target, will assemble and link
just fine on the build machine and then fault the instant it tries to execute on real
silicon that doesn't support whatever instruction it picked.

There was also a third option I considered and ruled out without testing:
[rapid7/embedded-tools](https://github.com/rapid7/embedded-tools) ships a prebuilt
`gdbserver.mipsbe`, but it's built against GDB 7.8 — old enough that I didn't want to
deal with potential remote-protocol differences from my much newer GDB client, on top of
already having one architecture-compatibility failure to chase down.

### The actual conclusion

Two prebuilt binaries, two different reasons they didn't work — one didn't exist for
the architecture at all, the other existed but targeted the wrong CPU variant within
that architecture. Between them, this ruled out "find a binary on the internet" as a
viable strategy entirely. interAptiv is specific enough that nothing generic-MIPS off
the shelf was going to reliably match it. The only remaining option was building from
source against a toolchain explicitly configured for that exact core — which is what
led to the Buildroot approach in the main post.

---

## Why GDB 13.2, and not something newer

This one doesn't have a clean technical justification — it's the result of working
backward through a build failure, and 13.2 is simply where that process landed.

The plan going into the build was to use whatever Buildroot offered as its newest GDB
package option — at the time, 15.2 — to stay close to the version of `gdb-multiarch`
already installed on my laptop (15.1). Buildroot can optionally build a full GDB as
part of its toolchain build, so the first attempt just took that default.

The build failed partway through, with the real error buried under a wall of configure
output:

```
make[2]: *** [Makefile:1029: all] Error 2
make[1]: *** [package/pkg-generic.mk:273: .../gdb-15.2/.stamp_built] Error 2
```

Digging past the noise (`make 2>&1 | tail -40` to get past the configure-stage chatter)
showed the real failure: a `static_assert` being used as if it were an array index
inside GDB's bundled `opcodes` library. `static_assert` in that position is valid under
older, looser compiler conformance, and GCC 15.x — which is what Buildroot's own host
build had used to build its host tools, including its GDB package — rejects it outright.

The natural next move was to try an older GDB release, on the assumption that an older
version predates whatever change introduced that pattern. I went down the version list
Buildroot offered:

- **15.2** → same `static_assert` failure.
- **14.x** → same failure again.
- **13.x**, the oldest version Buildroot's menuconfig offered → same failure.

Three GDB releases, all failing on the identical error. That ruled out "try an older
GDB version" as the fix — the problem was never about which GDB release I'd picked, it
was that Buildroot's *host* GCC (15.x) was simply too strict for the `opcodes` source
code in any GDB version available through Buildroot's package list.

At that point the right move was clear: stop trying to get Buildroot to build a full
GDB at all. The actual requirement was never "have GDB" — it was "have `gdbserver`."
Buildroot had already produced a perfectly good cross **compiler** before failing on
the unrelated GDB package, and that compiler could build `gdbserver` directly from
official GDB source, completely bypassing Buildroot's package system.

I had GDB 13.2 source already downloaded from working through the version list above,
so that's what got built. It works fine — the GDB remote protocol that `gdbserver` and
the client speak to each other has been stable for a very long time, so a gdbserver
built from 13.2 source talks to a 15.x `gdb-multiarch` client without any issue. If I
were doing this fresh today with no prior context, I'd probably still reach for
whatever GDB source version is convenient and stable, rather than chasing the newest
release — the protocol compatibility, not the version number, is what actually matters
here.
