#!/usr/bin/env node

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const render = path.join(__dirname, 'render.js');
const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'tex-render-test-'));

function run(args, input) {
  const result = spawnSync(process.execPath, [render, ...args], { encoding: 'utf8', input });
  assert.strictEqual(result.status, 0, result.stderr);
  return JSON.parse(result.stdout);
}

function assertFile(result, format, base) {
  assert.strictEqual(result[format], `${base}.${format}`);
  assert.ok(fs.statSync(result[format]).size > 100);
}

try {
  const pngBase = path.join(directory, 'equation');
  const png = run([pngBase], String.raw`\frac{F}{m}=a`);
  assert.ok(fs.statSync(png.svg).size > 100);
  assertFile(png, 'png', pngBase);
  assert.match(fs.readFileSync(png.svg, 'utf8'), /data-latex="\\frac\{F\}\{m\}=a"/);

  const svgBase = path.join(directory, 'vector');
  const svg = run(['--format', 'svg', 'E=mc^2', svgBase]);
  assert.match(fs.readFileSync(svg.svg, 'utf8'), /<svg/);

  for (const format of ['jpeg', 'webp', 'avif']) {
    const base = path.join(directory, format);
    assertFile(run(['--format', format, base], `x_{${format}}`), format, base);
  }

  const data = run(['--output', 'dataurl'], 'x^2+y^2=z^2');
  assert.match(data.dataurl, /^data:image\/png;base64,/);

  console.log('tex-render validation passed');
} finally {
  fs.rmSync(directory, { recursive: true, force: true });
}
