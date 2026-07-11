---
name: production-refinement
description: Use this skill automatically whenever writing, editing, refactoring, debugging, or optimizing ANY code — scripts, userscripts, CLI tools, backend logic, plugins, or UI — not only when the user explicitly says "optimize" or "refine." Trigger it any time the user wants robust, production-grade, scalable, polished, or "ultra premium" quality output, or when a normal one-shot code edit risks leaving bugs, unhandled edge cases, or rough UX/UI behind. Applies an iterative Define → Build → Run → Analyze → Optimize → Loop-back-until-success → Deploy cycle. Works for any language or project type (Tampermonkey userscripts, Python utilities, Obsidian CSS/JS plugins, web apps, APIs, etc.), and includes an "Ultra Premium UX/UI" bar for anything with a visible interface.
---

# Production Refinement

A general-purpose discipline for turning a working piece of code into a **production-grade, robust, and (where relevant) visually polished** deliverable — instead of stopping at the first version that runs.

This skill does not replace format-specific skills (docx/pptx/xlsx/pdf/frontend-design) — use those for their file types. This skill governs *how* Claude iterates on code quality regardless of format.

## Core loop

```
Define → Build → Run → Analyze → Optimize → Loop back until success → Deploy
```

Do not treat "it runs without erroring" as done. The loop is only complete when Analyze finds nothing worth fixing at the current effort level, or the user says stop.

### 1. Define
Before writing code, pin down in 1-3 sentences (inline, not asked aloud unless truly ambiguous):
- What does "done" look like functionally?
- What environment/constraints apply (browser DOM quirks, mobile runtime like Pydroid3/Colab, rate limits, existing file structure/version to preserve)?
- What's explicitly out of scope for this pass?

Check the conversation and any existing file/version history first — don't ask the user for things already stated or inferable (existing code style, versioning scheme, target platform).

### 2. Build
Write the implementation with production defaults, not prototype defaults:
- **Error handling**: wrap I/O, network calls, DOM queries, and parsing in guards; fail with a clear message instead of a silent crash or silent no-op.
- **Defensive selectors/inputs**: for scraping/userscript work, assume selectors, APIs, or input shapes can change or be missing — check existence before using, and log/flag when a fallback path is hit rather than failing silently.
- **Modularity**: small, named functions over monolithic blocks; avoid duplicated logic.
- **Config over hardcoding**: pull out magic numbers/strings/selectors that are likely to need tuning later.
- **Versioning discipline**: if editing an existing tool with a version number (e.g. `v3.1.0`), bump it consistently with the project's own convention and note what changed.

### 3. Run
Actually execute or trace through the code before calling it done:
- If Claude has code execution available, run it.
- If not (e.g. a Tampermonkey userscript that needs a live DOM), reason through it step by step against realistic sample input/output the user has provided or that's plausible for the target site, and say explicitly which parts were verified by execution vs. by inspection.

### 4. Analyze
Actively look for problems rather than waiting for the user to find them:
- Edge cases: empty input, missing fields, duplicate data, huge input, slow network, permission errors.
- Robustness: what happens when an external dependency (site DOM, API, file) changes shape?
- Security/privacy basics: no secrets hardcoded, no unsafe eval of untrusted content, no unbounded resource use.
- Readability: would another engineer (or future-you in six months) understand this without re-deriving it?
- For anything with a UI, also apply the **Ultra Premium UX/UI** bar below.

### 5. Optimize
Fix what Analyze found. Prefer the smallest change that fully closes the gap over a rewrite, unless the architecture itself is the problem — in which case say so and propose the upgrade rather than patching around it.

### 6. Loop back until success
After Optimize, re-run Analyze once more specifically against what was just changed. Only exit the loop when:
- The defined scope is functionally complete, and
- No known edge case in scope is left unhandled, and
- Further iteration would be speculative gold-plating rather than fixing a real gap.

If a real fix requires information Claude doesn't have (e.g. a live DOM sample, an actual error log), stop the loop and ask for exactly that — don't guess silently and call it done.

### 7. Deploy
- Summarize concretely what changed and why (not just "improved code").
- If it's a file deliverable, create/update the actual file and present it — don't just paste a wall of code inline for something meant to be run as a file.
- Call out anything still fragile or deferred, so the user isn't surprised later.

## Ultra Premium UX/UI bar

Apply this section only when the code has a visible interface (userscript UI injection, web app, Obsidian theme/plugin, CLI output formatting). Skip it for pure backend/logic/data code.

- Consistent spacing, alignment, and type scale — no ad hoc pixel values scattered through the code.
- Purposeful motion/feedback (loading states, hover/tap feedback, transitions) instead of instant jarring state changes — but nothing gratuitous.
- Mobile-aware by default: touch target sizes, responsive layout, no hover-only affordances, since much of this user's tooling runs on mobile (Pydroid3, Colab, mobile browsers).
- Respect the host environment's existing visual language (e.g. match an Obsidian theme's palette/tokens rather than introducing a clashing new one) unless the user is explicitly asking for a new look.
- Accessible contrast and legible defaults even under a "premium/dark" aesthetic.

## Architecture upgrade judgment

"Upgrade architecture" does not mean rewrite-by-default. Escalate scope only when one of these is true, and say so explicitly before doing it:
- The current structure can't support a requirement being added in this task.
- A recurring bug traces back to the structure itself (e.g. selector logic duplicated in five places instead of centralized).
- The user asked for a scalability/future-proofing pass specifically.

Otherwise, keep changes scoped to what Analyze actually flagged — a "production-grade" bar means *no rough edges left in scope*, not maximal rewriting.

## Communicating progress

Keep loop narration short. Don't narrate every micro-step of Define/Build/Run/Analyze/Optimize as separate messages — do the work, then report:
1. What was defined/assumed
2. What changed
3. What was tested/verified vs. reasoned through
4. What's still open, if anything

For long-running or multi-file work, a brief todo list is fine; avoid restating the full cycle name each time.