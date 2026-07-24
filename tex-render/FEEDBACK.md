# TeX Render Skill — Hermes/OpenClaw Compatibility Feedback

## Evaluation date

2026-07-24

## Verdict

The skill is conceptually compatible with both Hermes Agent and OpenClaw, but it is not currently drop-in reliable for a clean installation. The renderer itself works after dependencies are installed with a workaround.

## Verified behavior

- `SKILL.md` has valid minimal skill frontmatter:
  - `name: tex-render`
  - `description` present
  - non-empty body
- The skill does not depend on OpenClaw-specific APIs.
- The skill does not depend on Hermes-specific tool calls.
- The renderer uses ordinary Node.js and shell commands.
- The renderer returns JSON containing absolute artifact paths.
- Runtime validation passed after installing dependencies with legacy peer resolution:

```text
tex-render validation passed
```

- SVG and PNG rendering of a TeX expression succeeded.

## Issue 1: clean npm installation fails

A normal dependency installation fails with npm's peer-dependency resolver:

```text
npm install --omit=dev
```

Failure:

```text
ERESOLVE could not resolve
```

Dependency conflict:

```text
@svg-fns/svg2img@0.2.0
  peerOptional sharp "^0.34.4"

package.json
  sharp "^0.35.3"
```

The following workaround succeeds:

```bash
npm install --omit=dev --legacy-peer-deps
npm test
```

### Recommended fix

Align the `sharp` dependency with the peer requirement of `@svg-fns/svg2img@0.2.0`, preferably using a compatible 0.34.x release. Then regenerate and commit `package-lock.json`.

Avoid requiring users to rely on `--legacy-peer-deps` unless there is no compatible dependency combination.

## Issue 2: stdin examples do not match the argument parser

The skill documents this pattern:

```bash
printf '%s' 'E=mc^2' | node <skill-dir>/scripts/render.js ./out/formula
```

However, the current parser treats `./out/formula` as the TeX positional argument. It does not treat it as the output path when TeX is supplied through stdin.

The currently working form is:

```bash
printf '%s' 'E=mc^2' |
  node <skill-dir>/scripts/render.js '' ./out/formula
```

### Recommended fix

Either:

1. Update all documentation to include the empty TeX positional argument; or
2. Improve `parseArgs()` so that when stdin is non-interactive and exactly one positional argument is supplied, that argument is interpreted as `outBase`.

The second option is more ergonomic but should be documented because it creates an intentional ambiguity between piped TeX and positional TeX.

Add a regression test covering stdin plus an explicit output path.

## Issue 3: skill-directory resolution is vague

The skill says:

```text
Resolve this skill's directory using the host agent's skill location mechanism.
```

This is conceptually portable but not directly actionable in every host.

### Recommended fix

Document that the agent must use the absolute directory containing the loaded `SKILL.md`, then invoke:

```bash
node <skill-dir>/scripts/render.js
```

For Hermes, installation should preserve this structure:

```text
~/.hermes/skills/tex-render/SKILL.md
~/.hermes/skills/tex-render/package.json
~/.hermes/skills/tex-render/package-lock.json
~/.hermes/skills/tex-render/scripts/render.js
~/.hermes/skills/tex-render/scripts/validate.js
~/.hermes/skills/tex-render/node_modules/
```

For OpenClaw, use the equivalent skill directory while preserving the relative `scripts/` and dependency layout.

## Agent compatibility assessment

### Hermes Agent

Compatible after dependencies are installed. Hermes can load the procedural instructions and use its terminal/file-delivery capabilities. The renderer's JSON output is suitable for Hermes to parse and then attach using its native media-delivery mechanism.

Potential operational requirement: the host must allow dependency installation into the skill directory, or the skill must ship with dependencies already installed.

### OpenClaw

Compatible in principle because the skill has no OpenClaw-specific runtime dependencies. It requires:

- Node.js 18 or newer
- npm
- permission to install dependencies
- shell/command execution
- a file attachment or file-path delivery mechanism

The host-specific part is only resolving the skill directory and delivering the generated artifact.

## Security observations

- TeX processing is local after dependencies are installed.
- The renderer does not perform runtime network fetches for expressions.
- Dependency installation does execute npm package lifecycle scripts, so installation should follow the host's normal approval policy.
- Generated files should be treated as temporary unless the user specifies a durable destination.

## Recommended pre-release checklist

- [ ] Resolve the `sharp` peer-dependency conflict.
- [ ] Regenerate and validate `package-lock.json`.
- [ ] Fix or clarify stdin plus output-path argument handling.
- [ ] Add a regression test for stdin and an explicit output path.
- [ ] Clarify host-independent skill-directory resolution.
- [ ] Run `npm install --omit=dev` without flags.
- [ ] Run `npm test` on a clean dependency installation.
- [ ] Test SVG, PNG, JPEG, WebP, AVIF, and data-URL output.
- [ ] Test both positional TeX input and stdin input.
- [ ] Test delivery through the target host's attachment mechanism.
