const { chromium } = require('@playwright/test');

async function main() {
  const browser = await chromium.launch({ channel: 'msedge', headless: false });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();

  const errors = [];
  const responses = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('response', r => {
    if (r.url().includes('stockresearch'))
      responses.push(`[${new Date().toISOString().slice(11,19)}] ${r.status()} ${r.url()}`);
  });

  console.log('Navigating to analysis page...');
  await page.goto('http://app.stockresearch.local/', { waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForTimeout(1500);

  await page.locator('input').first().fill('AAPL');
  await page.locator('button:has-text("Run Analysis")').click();
  console.log(`[${new Date().toISOString().slice(11,19)}] Clicked Run Analysis`);

  // Wait and sample every 10s for 120s
  for (let i = 0; i < 12; i++) {
    await page.waitForTimeout(10000);
    const body = await page.locator('body').innerText();
    const hasVerdict = /BUY|SELL|HOLD|STRONG/i.test(body);
    const statusSnippet = body.match(/Stage \d|Analyzing|agent|verdict|error|failed/gi) || [];
    console.log(`[+${(i+1)*10}s] has verdict: ${hasVerdict}, status: ${[...new Set(statusSnippet)].join(', ')}`);
    if (hasVerdict) {
      const v = (body.match(/\b(STRONG BUY|BUY|STRONG SELL|SELL|HOLD)\b/i) || [])[0];
      console.log(`✅ Verdict: ${v?.toUpperCase()}`);
      break;
    }
  }

  console.log('\nNetwork responses during analysis:');
  responses.filter(r => r.includes('analysis')).forEach(r => console.log('  ' + r));
  if (errors.length) { console.log('\nConsole errors:'); errors.forEach(e => console.log('  ' + e)); }

  await page.screenshot({ path: 'scripts/debug_analysis_k8s.png' });
  await ctx.close();
  await browser.close();
}

main().catch(e => { console.error(e); process.exit(1); });
