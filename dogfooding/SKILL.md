---
name: dogfooding
description: Dogfood prototypes through realistic end-to-end use. Use when building a first usable version, replacing one prototype with another, or debugging and testing a product from the user's experience.
---

# Dogfooding

Ship the first usable vertical slice, then improve it by using it as its intended user would.

## Rules

- Pick one meaningful end-to-end journey and defer unrelated features.
- Treat prototype replacements as clean breaks. Update callers, tests, examples, and disposable state to the new model; add backward compatibility only when explicitly required.
- Exercise the documented setup and public interface with realistic input. Builder-only shortcuts and workarounds are product defects.
- Debug from the user-visible symptom. Capture expected versus observed behavior, reproduce it publicly, fix the cause, then replay the journey.
- Use focused tests for diagnosis, but require an end-to-end or manual check of the actual user experience.
- Prototype code is disposable; real user data, production state, and authorization boundaries are not.

## Dogfood loop

1. Define the user, their job, the smallest useful journey, and observable success.
2. Build the thinnest complete path through the real interface, including enough feedback and error handling to finish the job.
3. Run it from a clean or representative state without undocumented knowledge.
4. Fix blockers first, then material friction; defer expansion.
5. Replay until the journey succeeds through the public interface.

Finish only when the journey works end to end and report what was exercised, what changed, how it was verified, and any remaining user-visible limitation.
