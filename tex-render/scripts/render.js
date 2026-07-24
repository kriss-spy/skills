#!/usr/bin/env node

const crypto = require('crypto');
const fs = require('fs');
const os = require('os');
const path = require('path');
const MathJax = require('mathjax');
const sharp = require('sharp');

const RASTER_FORMATS = new Set(['png', 'jpeg', 'jpg', 'webp', 'avif']);

function help() {
  return `tex-render: TeX/LaTeX to SVG or raster images

Usage:
  tex-render [OPTIONS] "<TeX>" [output_base_path]
  printf '%s' "<TeX>" | tex-render [OPTIONS] [output_base_path]

Options:
  -h, --help       Show this help
  --inline         Use inline math style
  --format FMT     svg, png (default), jpeg, webp, or avif
  --output MODE    file (default) or dataurl
  --quality N      JPEG/WebP/AVIF quality, 1-100 (default: 92)
  --width N        Output width in pixels
  --height N       Output height in pixels
  --zoom N         Scale factor

Default output directory: system temporary directory/tex-render
Output: one JSON object on stdout with absolute paths or a data URL.`;
}

function fail(message) {
  console.error(`tex-render: ${message}`);
  process.exit(1);
}

function takeValue(argv, index, option) {
  if (argv[index + 1] === undefined) fail(`${option} requires a value`);
  return argv[index + 1];
}

function parseArgs(argv) {
  const options = { format: 'png', output: 'file', quality: 92, inline: false };
  const positional = [];
  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '-h' || arg === '--help') return { help: true };
    if (arg === '--inline') options.inline = true;
    else if (arg === '--format') options.format = takeValue(argv, i++, arg).toLowerCase();
    else if (arg === '--output') options.output = takeValue(argv, i++, arg).toLowerCase();
    else if (arg === '--quality') options.quality = Number(takeValue(argv, i++, arg));
    else if (arg === '--width') options.width = Number(takeValue(argv, i++, arg));
    else if (arg === '--height') options.height = Number(takeValue(argv, i++, arg));
    else if (arg === '--zoom') options.zoom = Number(takeValue(argv, i++, arg));
    else if (arg.startsWith('-')) fail(`unknown option: ${arg}`);
    else positional.push(arg);
  }
  options.positional = positional;
  if (positional.length > 2) fail('too many positional arguments');
  return options;
}

function resolveInput(options, stdin) {
  const pipedTex = stdin.trim();
  if (pipedTex) {
    if (options.positional.length > 1) fail('piped input accepts at most one output path');
    return { tex: pipedTex, outBase: options.positional[0] || '' };
  }
  return { tex: options.positional[0] || '', outBase: options.positional[1] || '' };
}

function validate(options) {
  if (![...RASTER_FORMATS, 'svg'].includes(options.format)) fail(`unsupported format: ${options.format}`);
  if (!['file', 'dataurl'].includes(options.output)) fail(`unsupported output mode: ${options.output}`);
  if (!Number.isFinite(options.quality) || options.quality < 1 || options.quality > 100) fail('quality must be 1-100');
  for (const key of ['width', 'height', 'zoom']) {
    if (options[key] !== undefined && (!Number.isFinite(options[key]) || options[key] <= 0)) fail(`${key} must be positive`);
  }
}

function normalize(tex) {
  let value = String(tex).trim();
  const pairs = [
    [/^\$\$([\s\S]*)\$\$$/, '$1'],
    [/^\$([\s\S]*)\$$/, '$1'],
    [/^\\\[([\s\S]*)\\\]$/, '$1'],
    [/^\\\(([\s\S]*)\\\)$/, '$1'],
  ];
  for (const [pattern, replacement] of pairs) {
    if (pattern.test(value)) return value.replace(pattern, replacement).trim();
  }
  return value;
}

async function typeset(tex, inline) {
  await MathJax.init({ loader: { load: ['input/tex', 'output/svg'] } });
  const node = await MathJax.tex2svgPromise(tex, { display: !inline });
  const html = MathJax.startup.adaptor.outerHTML(node);
  const match = html.match(/<svg[\s\S]*?<\/svg>/i);
  if (!match) throw new Error('MathJax did not produce SVG');
  return match[0].includes('xmlns=')
    ? match[0]
    : match[0].replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"');
}

function outputBase(options, tex) {
  if (options.outBase) {
    const absolute = path.resolve(options.outBase);
    return path.join(path.dirname(absolute), path.basename(absolute, path.extname(absolute)));
  }
  const identity = JSON.stringify({ tex, inline: options.inline, format: options.format, width: options.width, height: options.height, zoom: options.zoom });
  const hash = crypto.createHash('sha256').update(identity).digest('hex').slice(0, 12);
  return path.join(os.tmpdir(), 'tex-render', `tex-${hash}`);
}

async function main() {
  const options = parseArgs(process.argv);
  if (options.help) return console.log(help());
  validate(options);

  let stdin = '';
  if (!process.stdin.isTTY) {
    const chunks = [];
    for await (const chunk of process.stdin) chunks.push(chunk);
    stdin = Buffer.concat(chunks).toString('utf8');
  }
  const input = resolveInput(options, stdin);
  let tex = input.tex;
  options.outBase = input.outBase;
  tex = normalize(tex);
  if (!tex) fail('TeX input is required');

  const base = outputBase(options, tex);
  const svgPath = `${base}.svg`;
  const svg = await typeset(tex, options.inline);
  fs.mkdirSync(path.dirname(base), { recursive: true });

  if (options.output === 'file' || options.format === 'svg') fs.writeFileSync(svgPath, svg, 'utf8');
  if (options.format === 'svg') return console.log(JSON.stringify({ svg: svgPath }));

  const format = options.format === 'jpg' ? 'jpeg' : options.format;
  let image = sharp(Buffer.from(svg));
  if (options.zoom) image = image.resize({ width: Math.round((await image.metadata()).width * options.zoom) });
  if (options.width || options.height) image = image.resize({ width: options.width, height: options.height, fit: 'contain' });
  if (format === 'jpeg') image = image.flatten({ background: '#fff' }).jpeg({ quality: options.quality });
  else if (format === 'webp') image = image.webp({ quality: options.quality });
  else if (format === 'avif') image = image.avif({ quality: options.quality });
  else image = image.png();

  const buffer = await image.toBuffer();
  if (options.output === 'dataurl') {
    return console.log(JSON.stringify({ dataurl: `data:image/${format};base64,${buffer.toString('base64')}` }));
  }

  const imagePath = `${base}.${format}`;
  fs.writeFileSync(imagePath, buffer);
  console.log(JSON.stringify({ svg: svgPath, [format]: imagePath }));
}

main().catch((error) => fail(error.message));
