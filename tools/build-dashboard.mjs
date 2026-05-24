// Precompiles the Command Center JSX to plain browser JS so the dashboard no
// longer pays for in-browser @babel/standalone transpilation on every visit.
//
// Run:  node tools/build-dashboard.mjs
//
// Source of truth = the *.jsx files in components/ plus the inline app block in
// screens/dashboard.html (auto-extracted to components/dashboard-app.jsx).
// Output = matching *.js files (committed + bundled into the Cloud Run image).
//
// Each file is wrapped in an IIFE to reproduce Babel-standalone's per-script
// isolation: top-level `const`s stay local (no cross-file collisions) and the
// public API each file needs is shared via `Object.assign(window, {...})`.

import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { transformSync } from '@babel/core';
import presetReact from '@babel/preset-react';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const compDir = join(root, 'components');

// 1. Extract the inline app block from dashboard.html → components/dashboard-app.jsx
const dashPath = join(root, 'screens', 'dashboard.html');
let dashHtml = readFileSync(dashPath, 'utf8');
const inlineRe = /<script type="text\/babel">(?![^>]*\bsrc=)([\s\S]*?)<\/script>/g;
const inlineBlocks = [...dashHtml.matchAll(inlineRe)].map(m => m[1]);
if (inlineBlocks.length !== 1) {
  throw new Error(`Expected exactly 1 inline text/babel block in dashboard.html, found ${inlineBlocks.length}`);
}
const appHeader = `// =============================================
// DASHBOARD-APP.JSX — Command Center React app (auto-extracted from
// screens/dashboard.html by tools/build-dashboard.mjs). Edit there or here,
// then re-run the build. Do not edit dashboard-app.js by hand.
// =============================================
`;
writeFileSync(join(compDir, 'dashboard-app.jsx'), appHeader + inlineBlocks[0].trim() + '\n');

// 2. Compile each JSX (in load order) → IIFE-wrapped .js
const files = ['data', 'incident-card', 'charts', 'voice-orb', 'dashboard-app'];
for (const name of files) {
  const src = readFileSync(join(compDir, `${name}.jsx`), 'utf8');
  const { code } = transformSync(src, {
    presets: [[presetReact, { runtime: 'classic', pragma: 'React.createElement', pragmaFrag: 'React.Fragment' }]],
    filename: `${name}.jsx`,
    comments: true,
    compact: false,
  });
  const out = `// AUTO-GENERATED from ${name}.jsx by tools/build-dashboard.mjs — do not edit.\n(function () {\n${code}\n})();\n`;
  writeFileSync(join(compDir, `${name}.js`), out);
  console.log(`compiled components/${name}.js`);
}
console.log('done');
