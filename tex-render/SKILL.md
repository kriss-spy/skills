---
name: tex-render
description: Render TeX or LaTeX equations as SVG, PNG, JPEG, WebP, or AVIF. Use when a user asks for a formula as an image, needs math artwork for a document or UI, or when another skill needs a portable equation asset.
---

# TeX Render

Turn TeX math into reusable image files through the bundled command-line renderer. The workflow is agent-neutral: use whatever shell execution and file-delivery capabilities the current environment provides.

## Render

1. Set `<skill-dir>` to the absolute directory containing this loaded `SKILL.md`. Preserve `SKILL.md`, `package.json`, `package-lock.json`, and `scripts/` together when installing the skill in any host.
2. Check that `<skill-dir>/node_modules` exists. If it does not, follow the host's approval policy for npm lifecycle scripts, then run `npm install --omit=dev` in `<skill-dir>`.
3. Pass TeX through stdin. This avoids shell interpolation and quoting errors:

   ```sh
   printf '%s' 'E = mc^2' | node <skill-dir>/scripts/render.js
   ```

4. Parse the single JSON object printed to stdout. It contains absolute paths such as `{"svg":"...","png":"..."}`.
5. Deliver the requested artifact using the host's strongest available mechanism:
   - Attach or embed the generated file when file/image delivery is supported.
   - Use `--output dataurl` when the host explicitly supports data URLs.
   - Otherwise provide the absolute output path.
6. Confirm that every requested expression was rendered and delivered in the requested order.

Render only when requested or when image output is clearly required. Preserve raw TeX alongside the image when it is useful for editing or accessibility.

## Options

Run `node <skill-dir>/scripts/render.js --help` for the complete interface.

```sh
# Explicit output path (extension is added)
printf '%s' '\frac{F}{m}=a' | node <skill-dir>/scripts/render.js ./out/formula

# Alternate raster formats
printf '%s' 'x^2+y^2=z^2' | node <skill-dir>/scripts/render.js --format webp
printf '%s' 'E=mc^2' | node <skill-dir>/scripts/render.js --format jpeg --quality 85

# SVG only, inline style, dimensions, or data URL
printf '%s' '\int_0^\infty e^{-x^2}dx' | node <skill-dir>/scripts/render.js --format svg
printf '%s' 'a^2+b^2=c^2' | node <skill-dir>/scripts/render.js --inline
printf '%s' '\sum_{n=1}^\infty n^{-2}' | node <skill-dir>/scripts/render.js --width 1200
printf '%s' 'E=mc^2' | node <skill-dir>/scripts/render.js --output dataurl
```

Accepted delimiters include raw TeX, `$...$`, `$$...$$`, `\(...\)`, and `\[...\]`. The renderer strips one matching outer delimiter pair.

With piped input, one positional argument is the output path. Without piped input, the first positional argument is TeX and the optional second is the output path.

## Output Rules

- Default format: PNG plus the intermediate SVG.
- Default directory: `${TMPDIR:-<system-temp>}/tex-render`.
- Explicit relative paths resolve from the command's working directory.
- Repeated default renders of the same expression and options use deterministic names.
- JPEG uses a white background; alpha-capable formats retain transparency.
- Treat generated files as temporary unless the user supplied a durable destination.

## Failure Handling

- On a dependency error, run `npm install --omit=dev` in the skill directory and retry once.
- On invalid TeX, report the renderer's stderr and identify the failing expression.
- On unsupported attachment delivery, return the absolute path rather than claiming the image was sent.
- For untrusted TeX, keep processing local. The renderer performs no network fetches after dependencies are installed.

## Attribution

Adapted from `TheBigoranger/tex-render` (v1.1.x), using MathJax and Sharp. This version removes OpenClaw-specific paths and messaging conventions to provide a portable agent interface.
