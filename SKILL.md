# skill.md
## Codex × Gemini × Claude Engineering Style

> Hybrid engineering standard focused on:
> - Codex-level execution speed
> - Gemini-scale systems reasoning
> - Claude-grade clarity, structure, and maintainability

---

# CORE PRINCIPLES

## 1. Think Before Coding
Never jump directly into implementation.

Always:
1. Analyze requirements
2. Identify constraints
3. Define architecture
4. Evaluate tradeoffs
5. Plan execution
6. Then write code

Output should reflect deliberate engineering, not autocomplete behavior.

---

## 2. Optimize for Longevity
Code must survive:
- scale
- maintenance
- refactors
- onboarding
- production incidents
- future feature expansion

Prefer:
- clarity over cleverness
- explicitness over magic
- composability over monoliths
- architecture over hacks

---

## 3. Production-First Mindset
Assume code will run:
- at scale
- under load
- in hostile environments
- with malformed input
- with unreliable networks
- with partial failures

Always design defensively.

---

# ENGINEERING STYLE

## Architecture Rules

### Prefer:
- Modular architecture
- Domain separation
- Pure functions where possible
- Stateless components
- Composition patterns
- Dependency injection
- Clear contracts/interfaces

### Avoid:
- Hidden side effects
- God objects
- Tight coupling
- Deep inheritance
- Massive files
- Context leakage
- Global mutable state

---

# CODE QUALITY STANDARD

## Every file should feel:
- intentional
- minimal
- readable
- scalable
- testable
- documented by design

---

## Naming Rules

### Names must be:
- descriptive
- unambiguous
- searchable
- domain-oriented

### Bad
```ts
const d = getData()

Good

const authenticatedUserProfile = await fetchUserProfile()


---

COMMENT PHILOSOPHY

Do NOT explain obvious code

Bad:

// increment i
i++

Explain:

WHY

tradeoffs

architectural decisions

non-obvious constraints

performance implications


Good:

// Using map for O(1) lookup because this path executes ~50k/min
const sessionIndex = new Map()


---

FILE DESIGN

Files should:

have one responsibility

be navigable quickly

minimize cognitive load


Prefer:

small focused modules

extracted utilities

isolated business logic


Avoid:

2000-line files

mixed concerns

UI + business logic coupling

duplicated logic



---

ERROR HANDLING

Never swallow errors

Bad:

try {
  await process()
} catch {}

Good:

try {
  await process()
} catch (error) {
  logger.error('Process failed', {
    error,
    requestId,
    userId,
  })

  throw new ProcessingError('Unable to complete request')
}


---

TYPES & VALIDATION

Treat external input as hostile

Always validate:

API payloads

user input

env vars

database responses

third-party data



---

Prefer strict typing

TypeScript

type CreateUserInput = {
  email: string
  username: string
}

Avoid:

any
unknown as any


---

PERFORMANCE MINDSET

Optimize intelligently

Do NOT micro-optimize blindly.

First:

1. Measure


2. Identify bottlenecks


3. Optimize critical paths




---

Always consider:

algorithmic complexity

memory usage

network round trips

render cost

cache strategy

concurrency

backpressure



---

SECURITY STANDARD

Default to secure-by-design

Always:

sanitize input

validate authorization

escape output

use parameterized queries

avoid secrets in code

apply least privilege

handle tokens securely


Never trust:

client input

headers

query params

uploaded files

external APIs



---

API DESIGN

APIs should be:

predictable

versionable

typed

documented

backward compatible



---

Response structure

{
  "success": true,
  "data": {},
  "meta": {},
  "error": null
}


---

DATABASE PRINCIPLES

Design for:

integrity

scalability

indexing

migration safety

transactional consistency



---

Avoid:

N+1 queries

unbounded scans

missing indexes

unsafe migrations



---

FRONTEND STANDARD

UI architecture should prioritize:

accessibility

responsiveness

state clarity

rendering efficiency

maintainability



---

Prefer:

server-driven data flow

isolated components

predictable state

optimistic UI carefully

skeleton loading

error boundaries



---

REACT/VUE/SVELTE STYLE

Components should:

do one thing well

minimize rerenders

avoid prop drilling

separate logic from presentation



---

Avoid:

giant stateful components

deeply nested effects

implicit state mutations



---

BACKEND STANDARD

Services should:

be observable

support retries

be idempotent where possible

degrade gracefully



---

Include:

structured logging

metrics

tracing

health checks

timeout handling

circuit breaking where needed



---

TESTING PHILOSOPHY

Tests should verify:

behavior

contracts

edge cases

failure paths


Not implementation details.


---

Prioritize:

1. integration tests


2. critical path tests


3. unit tests


4. e2e for business flows




---

GIT & VERSION CONTROL

Commits should be:

atomic

descriptive

reviewable


Good

feat(auth): add rotating refresh token support

Bad

fix stuff


---

DOCUMENTATION STYLE

Documentation must:

reduce onboarding time

explain architecture

clarify decisions

include examples

stay close to code



---

AI-ASSISTED CODING RULES

Never:

hallucinate APIs

invent libraries

assume behavior

ignore edge cases

skip validation

generate fake tests



---

Always:

verify assumptions

reason step-by-step

explain tradeoffs

identify risks

mention limitations

surface unknowns honestly



---

REFACTORING RULES

Refactoring should:

reduce complexity

improve readability

preserve behavior

improve modularity


Not merely "change style."


---

OUTPUT EXPECTATIONS

Responses should:

be structured

concise but complete

technically rigorous

implementation-oriented

free from fluff



---

DECISION HIERARCHY

Priority order:

1. Correctness


2. Security


3. Reliability


4. Maintainability


5. Performance


6. Developer Experience


7. Conciseness




---

ELITE EXECUTION MODE

Before finalizing any implementation:

Verify architecture

Review edge cases

Check scalability

Validate security

Consider failure modes

Reduce unnecessary complexity

Improve naming

Ensure consistency

Remove ambiguity

Polish developer ergonomics



---

FINAL STANDARD

The final result should feel:

engineered

scalable

intentional

elegant

maintainable

production-grade


Not AI-generated boilerplate.