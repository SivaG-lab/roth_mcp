---
name: reverse-engineer
description: >
  Expert reverse engineer for binary analysis, disassembly, decompilation,
  and software analysis. Masters IDA Pro, Ghidra, radare2, x64dbg, and
  modern RE toolchains. Handles executable analysis, library inspection,
  protocol extraction, and vulnerability research. Use for authorized
  binary analysis, CTF challenges, security research, or understanding
  undocumented software. Triggers: reverse engineer, binary analysis,
  disassembly, decompile, ghidra, ida pro, ctf, malware analysis.
user-invokable: true
argument-hint: "<binary or RE task>"
metadata:
  model: opus
---

# Reverse Engineering

Expert guide for binary analysis, disassembly, decompilation, and software analysis for authorized purposes.

## When to Use

- Analyzing binaries for security research (with authorization)
- Solving CTF challenges
- Understanding closed-source libraries for interoperability
- Malware analysis for defensive purposes
- Protocol reverse engineering

## When NOT to Use

- Source code is available (just read it)
- No authorization for the target
- Creating malware or bypassing licensing

---

## RE Toolchain

| Tool | Purpose | Platform |
|------|---------|----------|
| **Ghidra** | Disassembly + decompilation (free) | Cross-platform |
| **IDA Pro** | Industry-standard disassembler | Windows/Linux/Mac |
| **radare2** | CLI disassembler + debugger | Cross-platform |
| **x64dbg** | Windows debugger | Windows |
| **GDB** | Linux/Mac debugger | Unix |
| **Frida** | Dynamic instrumentation | Cross-platform |
| **pwntools** | CTF exploitation toolkit | Python |
| **angr** | Symbolic execution | Python |
| **capstone** | Disassembly framework | Multi-language |

## Scripting Environments

- **IDAPython** — IDA Pro scripting
- **Ghidra** — Java/Python via Jython
- **r2pipe** — radare2 Python API
- **unicorn** — CPU emulator framework
- **Triton** — Dynamic binary analysis

---

## Analysis Methodology

### Phase 1: Reconnaissance

```bash
file target_binary          # File type, architecture
strings target_binary       # Readable strings
checksec --file=target      # Security features (NX, PIE, canary)
readelf -h target           # ELF header (Linux)
dumpbin /headers target.exe # PE header (Windows)
```

### Phase 2: Static Analysis

1. Load into disassembler (Ghidra/IDA)
2. Identify entry points (main, exports, callbacks)
3. Map program structure (functions, basic blocks, CFG)
4. Annotate code (rename functions, define structs)
5. Cross-reference analysis (data + code xrefs)

### Phase 3: Dynamic Analysis

1. Set up isolated environment (VM, network monitor)
2. Set breakpoints on entry points and API calls
3. Trace execution and record behavior
4. Manipulate inputs, observe behavior changes

### Phase 4: Documentation

1. Document function signatures and purposes
2. Map data structures and their layouts
3. Write pseudocode for key algorithms
4. Summarize findings and vulnerabilities

---

## Common Code Patterns

```c
// XOR string obfuscation
for (int i = 0; i < len; i++)
    str[i] ^= key;

// Anti-debugging (Windows)
if (IsDebuggerPresent())
    exit(1);

// API hashing (common in malware)
hash = 0;
while (*name)
    hash = ror(hash, 13) + *name++;

// Stack string construction
char s[8];
*(DWORD*)s = 0x6C6C6548;  // "Hell"
*(DWORD*)(s+4) = 0x6F;     // "o\0"
```

### Calling Conventions

| Convention | Args | Cleanup | Platform |
|-----------|------|---------|----------|
| **cdecl** | Stack | Caller | x86 |
| **stdcall** | Stack | Callee | x86 Win32 |
| **x64 Windows** | RCX,RDX,R8,R9 → stack | Caller | x64 Windows |
| **System V** | RDI,RSI,RDX,RCX,R8,R9 → stack | Caller | x64 Linux/Mac |
| **ARM** | R0-R3 → stack | Caller | ARM |

---

## CTF Quick Reference

```bash
# Binary challenge approach
file challenge && checksec --file=challenge

# GDB with pwndbg/GEF
gdb ./challenge
> break main
> run
> info registers
> x/20x $rsp

# Find password comparisons
strings challenge | grep -i pass
objdump -d challenge | grep -A5 "strcmp\|memcmp"

# Frida dynamic hook
frida -f ./challenge -l hook.js
```

---

## Security & Ethics

**Authorized Use Only:**
- Security research with proper authorization
- CTF competitions and educational challenges
- Malware analysis for defensive purposes
- Responsible vulnerability disclosure
- Interoperability research

**Never Assist With:**
- Unauthorized system access
- Malware creation for malicious purposes
- Software licensing bypass
- Intellectual property theft

---

## Checklist

- [ ] Authorization confirmed for target
- [ ] Analysis environment is isolated (VM)
- [ ] File type and architecture identified
- [ ] Static analysis completed (disassembly, strings, xrefs)
- [ ] Dynamic analysis performed (if needed)
- [ ] Key algorithms documented as pseudocode
- [ ] Findings summarized with evidence
