const fs = require('fs');
const path = require('path');
const { instance } = require('@viz-js/viz');
const puppeteer = require('puppeteer');

async function renderDotToPng(dotPath, pngPath, maxDim = 12000) {
  console.log(`[Renderer] Reading ${dotPath}...`);
  const dot = fs.readFileSync(dotPath, 'utf8');
  
  console.log(`[Renderer] Compiling Graphviz DOT to SVG via @viz-js/viz...`);
  const viz = await instance();
  const svg = viz.renderString(dot, { format: 'svg' });
  
  const svgPath = pngPath.replace(/\.png$/, '.svg');
  fs.writeFileSync(svgPath, svg, 'utf8');
  console.log(`[Renderer] Wrote intermediate SVG to ${svgPath} (${svg.length} bytes)`);

  // Extract SVG viewBox
  const vbMatch = svg.match(/viewBox="([^"]*)"/);
  if (!vbMatch) {
    throw new Error('Could not find viewBox attribute in generated SVG');
  }

  const [minX, minY, vbWidth, vbHeight] = vbMatch[1].split(/\s+/).map(Number);
  console.log(`[Renderer] Original SVG dimensions: ${vbWidth} x ${vbHeight} pt`);

  // Calculate target pixel dimensions (keeping aspect ratio, max dimension capped to maxDim for GPU texture safety)
  let targetWidth = vbWidth;
  let targetHeight = vbHeight;

  // Scale up or down to ensure crispness while staying safely within Chromium texture limits (< 14000px)
  const largest = Math.max(vbWidth, vbHeight);
  let scaleFactor = 1.0;
  if (largest > maxDim) {
    scaleFactor = maxDim / largest;
  } else if (largest < 4000) {
    scaleFactor = Math.min(2.5, 4000 / largest);
  }

  targetWidth = Math.round(vbWidth * scaleFactor);
  targetHeight = Math.round(vbHeight * scaleFactor);
  console.log(`[Renderer] Rasterizing SVG at ${targetWidth} x ${targetHeight} px (scale: ${scaleFactor.toFixed(2)}x)...`);

  console.log(`[Renderer] Launching headless browser for rasterization...`);
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({
      width: targetWidth + 40,
      height: targetHeight + 40,
      deviceScaleFactor: 1
    });
    
    // Inject clean styling and SVG into container
    const cleanSvg = svg
      .replace(/width="[^"]*"/, 'width="100%"')
      .replace(/height="[^"]*"/, 'height="100%"');

    const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {
      margin: 0;
      padding: 20px;
      background-color: #ffffff;
      display: inline-block;
    }
    #diagram-container {
      width: ${targetWidth}px;
      height: ${targetHeight}px;
      display: block;
    }
    svg {
      display: block;
      width: 100%;
      height: 100%;
    }
  </style>
</head>
<body>
  <div id="diagram-container">
    ${cleanSvg}
  </div>
</body>
</html>`;

    await page.setContent(html, { waitUntil: 'networkidle0' });
    
    const container = await page.$('#diagram-container');
    if (!container) {
      throw new Error('#diagram-container element not found in rendered page');
    }

    await container.screenshot({
      path: pngPath,
      omitBackground: false
    });

    const stat = fs.statSync(pngPath);
    console.log(`[Renderer] Successfully generated ${pngPath} (${(stat.size / 1024).toFixed(1)} KB)`);
  } finally {
    await browser.close();
  }
}

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 2) {
    console.error('Usage: node render_diagrams.js <input.dot> <output.png> [maxDimension]');
    process.exit(1);
  }
  const [dotPath, pngPath, maxDimStr] = args;
  const maxDim = maxDimStr ? parseInt(maxDimStr, 10) : 12000;
  await renderDotToPng(dotPath, pngPath, maxDim);
}

if (require.main === module) {
  main().catch(err => {
    console.error('[Renderer Error]', err);
    process.exit(1);
  });
}

module.exports = { renderDotToPng };
