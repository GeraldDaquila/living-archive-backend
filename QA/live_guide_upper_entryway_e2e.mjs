import { chromium } from "playwright";

const GUIDE_URL = "https://geralddaquila.com/the-guide/";
const QUERY = "What does stewardship mean in everyday life, and why does it matter now more than ever?";
const API_PATTERN = /\/api\/query(?:\?|$)/;
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
page.setDefaultTimeout(8_000);
page.setDefaultNavigationTimeout(25_000);
const errors = [];
const consoleErrors = [];
const posts = [];
page.on("pageerror", e => errors.push(e.message));
page.on("console", m => { if (m.type() === "error") consoleErrors.push(m.text()); });
page.on("request", r => {
  if (r.method() === "POST" && API_PATTERN.test(new URL(r.url()).pathname)) posts.push({ url: r.url(), body: r.postData()?.slice(0,300) || "" });
});
try {
  await page.goto(GUIDE_URL, { waitUntil: "domcontentloaded", timeout: 25_000 });
  const entrywayInfo = await page.locator("form#archive-search-form").evaluateAll(forms => forms.map((form, index) => ({ index, woody: Boolean(form.closest('.archive-stage-wrapper[data-guide-instance="woody"]')), parent: form.parentElement?.id || form.parentElement?.className || form.parentElement?.tagName })));
  const upperIndex = entrywayInfo.findIndex(item => !item.woody);
  if (upperIndex < 0) throw new Error("No upper Custom HTML form found: " + JSON.stringify(entrywayInfo));
  const upper = page.locator("form#archive-search-form").nth(upperIndex);
  const input = upper.locator("#archive-query-input");
  const button = upper.locator("#archive-submit-btn");
  await input.waitFor({ state: "visible", timeout: 8_000 });
  await input.fill(QUERY);
  const waiter = page.waitForRequest(r => r.method() === "POST" && API_PATTERN.test(new URL(r.url()).pathname), { timeout: 12_000 }).catch(e => null);
  let clickError = null;
  try { await button.click({ timeout: 5_000 }); } catch (e) { clickError = e.message; }
  const request = await waiter;
  if (!request) throw new Error("Upper entryway produced no POST /api/query. " + JSON.stringify({
    clickError, posts,
    button: await button.evaluate(b => ({disabled:b.disabled,text:b.innerText,rect:(()=>{const r=b.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height}})()})),
    scripts: await page.locator("script[src]").evaluateAll(ss => ss.map(s=>s.src).filter(s=>/living-archive-guide|litespeed\/js/.test(s))),
    errors, consoleErrors
  }));
  const responseBox = page.locator("#archive-container-top #archive-response-box").first();
  await responseBox.waitFor({ state: "visible", timeout: 8_000 });
  await page.waitForFunction(() => {
    const root=document.querySelector("#archive-container-top");
    const t=root?.querySelector("#archive-response-text")?.innerText?.trim()||"";
    return t.length>=80 && !/Giving this question a little more room/i.test(t);
  }, null, { timeout: 60_000 });
  const answer = (await page.locator("#archive-container-top #archive-response-text").first().innerText()).trim();
  console.log(JSON.stringify({result:"UPPER_PASS",query:QUERY,requestCount:posts.length,requestUrl:request.url(),answerChars:answer.length,answerPreview:answer.slice(0,400),answerVisible:await responseBox.isVisible(),errors,consoleErrors}));
  if(posts.length!==1) throw new Error("Expected exactly one POST; observed "+posts.length);
  if(errors.length) throw new Error("Page errors: "+JSON.stringify(errors));
} catch(e) {
  console.error(JSON.stringify({result:"UPPER_FAIL",message:e.message,stack:e.stack,posts,errors,consoleErrors}));
  process.exitCode=1;
} finally { await browser.close(); }
