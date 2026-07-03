const { chromium } = require('@playwright/test');

async function main() {
  const browser = await chromium.launch({ channel: 'msedge', headless: false });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();

  console.log('Navigating to home page...');
  await page.goto('http://localhost:3010/', { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(1500);

  const inputs = await page.locator('input').all();
  console.log(`Found ${inputs.length} input(s)`);
  for (const inp of inputs) {
    const ph = await inp.getAttribute('placeholder').catch(() => '');
    const type = await inp.getAttribute('type').catch(() => '');
    console.log(`  input: type="${type}" placeholder="${ph}"`);
  }

  const buttons = await page.locator('button').all();
  console.log(`Found ${buttons.length} button(s)`);
  for (const btn of buttons.slice(0, 10)) {
    const txt = (await btn.innerText().catch(() => '')).trim().slice(0, 50);
    console.log(`  button: "${txt}"`);
  }

  const textInput = page.locator('input').first();
  await textInput.fill('AAPL');
  console.log('Filled AAPL into first input');

  const analyzeBtn = page.locator('button').filter({ hasText: /analyz|run|submit|search/i }).first();
  const btnText = (await analyzeBtn.innerText().catch(() => 'unknown')).trim();
  console.log(`Clicking button: "${btnText}"`);
  await analyzeBtn.click();

  console.log('Waiting up to 90s for analysis result...');
  try {
    await page.waitForFunction(
      () => document.body.innerText.match(/BUY|SELL|HOLD|Verdict|verdict|STRONG/i),
      { timeout: 90000 }
    );
    console.log('✅ Analysis verdict appeared');
    await page.screenshot({ path: 'scripts/analysis_result.png', fullPage: false });
    console.log('Screenshot saved: scripts/analysis_result.png');
  } catch (e) {
    const snippet = (await page.locator('body').innerText()).slice(0, 500);
    console.log('❌ Verdict not found within 90s. Page snippet:');
    console.log(snippet);
    await page.screenshot({ path: 'scripts/analysis_timeout.png', fullPage: false });
  }

  await browser.close();
}

main().catch(e => { console.error(e); process.exit(1); });
