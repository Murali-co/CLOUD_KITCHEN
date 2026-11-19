const fs = require('fs');
const path = require('path');
const puppeteer = require('./node_modules/puppeteer');

async function renderSvgToPng(svgPath, pngPath, targetWidth = 4000) {
  console.log(`[SVG->PNG] Loading ${svgPath}...`);
  const svg = fs.readFileSync(svgPath, 'utf8');

  // Match viewBox or width/height
  const vbMatch = svg.match(/viewBox="([^"]*)"/);
  let vbWidth = 3000, vbHeight = 2000;
  if (vbMatch) {
    const parts = vbMatch[1].trim().split(/\s+/).map(Number);
    vbWidth = parts[2];
    vbHeight = parts[3];
  } else {
    const wMatch = svg.match(/width="(\d+)"/);
    const hMatch = svg.match(/height="(\d+)"/);
    if (wMatch && hMatch) {
      vbWidth = parseInt(wMatch[1], 10);
      vbHeight = parseInt(hMatch[1], 10);
    }
  }

  // Calculate target dimensions
  let scale = 1.0;
  if (vbWidth > 0) {
    scale = targetWidth / vbWidth;
  }
  const renderWidth = Math.round(vbWidth * scale);
  const renderHeight = Math.round(vbHeight * scale);

  console.log(`[SVG->PNG] Dimensions: ${vbWidth}x${vbHeight} -> ${renderWidth}x${renderHeight} px`);

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({
      width: renderWidth + 40,
      height: renderHeight + 40,
      deviceScaleFactor: 1
    });

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
    #container {
      width: ${renderWidth}px;
      height: ${renderHeight}px;
      display: block;
    }
    svg {
      width: 100%;
      height: 100%;
      display: block;
    }
  </style>
</head>
<body>
  <div id="container">
    ${svg}
  </div>
</body>
</html>`;

    await page.setContent(html, { waitUntil: 'networkidle0' });
    const container = await page.$('#container');
    await container.screenshot({ path: pngPath, omitBackground: false });

    const stats = fs.statSync(pngPath);
    console.log(`[SVG->PNG] Success: ${pngPath} (${(stats.size / 1024).toFixed(1)} KB)`);
  } finally {
    await browser.close();
  }
}

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 2) {
    console.error('Usage: node render_svg_to_png.js <input.svg> <output.png> [targetWidth]');
    process.exit(1);
  }
  const [svgPath, pngPath, widthStr] = args;
  const targetWidth = widthStr ? parseInt(widthStr, 10) : 4000;
  await renderSvgToPng(svgPath, pngPath, targetWidth);
}

if (require.main === module) {
  main().catch(err => {
    console.error('[SVG->PNG Error]', err);
    process.exit(1);
  });
}

module.exports = { renderSvgToPng };
