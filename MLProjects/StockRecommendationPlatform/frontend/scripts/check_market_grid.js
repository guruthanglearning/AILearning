const { chromium } = require('@playwright/test');
(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();

  await page.goto('http://localhost:3010/market-grid', { waitUntil: 'domcontentloaded' });

  // Wait for rows to appear first
  await page.waitForFunction(
    () => document.querySelectorAll('tbody tr').length >= 10,
    null, { timeout: 30000 }
  );

  // Then wait for market cap data to populate (4.xxx T or xxx B pattern)
  try {
    await page.waitForFunction(
      () => /[\d.]+T|[\d.]+B/.test(document.querySelector('tbody')?.innerText || ''),
      null, { timeout: 30000 }
    );
    console.log('✅ Market cap data populated');
  } catch (e) {
    console.log('⚠️  Market cap still not visible after 30s');
  }

  await page.waitForTimeout(1000);

  const totalRows = await page.evaluate(() => document.querySelectorAll('tbody tr').length);
  console.log('Total rows:', totalRows);

  // Count filled cells per column
  const colStats = await page.evaluate(() => {
    const rows = Array.from(document.querySelectorAll('tbody tr'));
    const numCols = rows[0]?.querySelectorAll('td').length || 0;
    const stats = [];
    for (let ci = 0; ci < numCols; ci++) {
      let filled = 0, sample = '';
      rows.forEach(row => {
        const cell = row.querySelectorAll('td')[ci];
        if (!cell) return;
        const t = cell.innerText.trim();
        if (t && t !== '--' && t !== '—') { filled++; if (!sample) sample = t.slice(0, 20); }
      });
      stats.push({ col: ci, filled, total: rows.length, sample });
    }
    return stats;
  });

  console.log('\nColumn fill rates:');
  const headers = ['Symbol','30d','Pre Price','Pre Chg','Last','Change','Post Price','Post Chg','Earnings','Mkt Cap','Div','Exchange','52H','52L','Shares'];
  colStats.forEach(({ col, filled, total, sample }) => {
    const pct = Math.round(filled/total*100);
    const h = headers[col] || `Col${col}`;
    const status = pct >= 70 ? '✅' : pct >= 30 ? '⚠️ ' : '❌';
    console.log(`  ${status} [${col}] ${h.padEnd(12)} ${filled}/${total} (${pct}%) ${sample ? '| e.g. '+sample : ''}`);
  });

  // Show first 3 rows raw text
  console.log('\nFirst 3 rows:');
  const rows3 = await page.evaluate(() =>
    Array.from(document.querySelectorAll('tbody tr')).slice(0, 3).map(row =>
      Array.from(row.querySelectorAll('td')).map(td => td.innerText.trim().slice(0, 15))
    )
  );
  rows3.forEach((r, i) => console.log(`  Row ${i}:`, r));

  await page.screenshot({ path: 'scripts/market_grid_check.png', fullPage: false });
  await browser.close();
  console.log('\nDone. Screenshot saved.');
})().catch(e => { console.error('Error:', e.message); process.exit(1); });
