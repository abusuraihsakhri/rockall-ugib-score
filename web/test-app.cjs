"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

const projectRoot = path.resolve(__dirname, "..");

function loadCalculator(file) {
  const html = fs.readFileSync(path.join(projectRoot, file), "utf8");
  const match = html.match(/<script>([\s\S]*?)<\/script>/);
  assert.ok(match, "The application must have an inline script");
  const elements = new Map();
  const get = (id) => {
    if (!elements.has(id)) {
      const listeners = {};
      elements.set(id, {
        value: "", checked: false, hidden: false, textContent: "",
        listeners, addEventListener(type, callback) { listeners[type] = callback; }
      });
    }
    return elements.get(id);
  };
  vm.runInNewContext(match[1], {document: {getElementById: get}}, {timeout: 2000});
  const set = (id, value) => { get(id).value = String(value); };
  const calculate = () => get("calculator").listeners.submit({preventDefault() {}});
  const endoscopy = (checked) => {
    get("endoscopy").checked = checked;
    get("endoscopy").listeners.change();
  };
  return {get, set, calculate, endoscopy, html};
}

for (const file of ["index.html", "docs/index.html", "web/index.html"]) {
  test(file + ": complete and clinical calculation", () => {
    const app = loadCalculator(file);
    const {get, set, calculate, endoscopy} = app;
    set("age", 65);
    set("hr", 100);
    set("sbp", 100);
    set("comorbidity", "cardiac");
    calculate();
    assert.equal(get("clinical-score").textContent, "4");
    assert.equal(get("mortality").textContent, "24.6%");
    assert.equal(get("rebleeding-row").hidden, true);
    assert.equal(get("complete-row").hidden, true);

    endoscopy(true);
    set("diagnosis", "other");
    set("stigmata", "blood");
    calculate();
    assert.equal(get("complete-score").textContent, "7");
    assert.equal(get("mortality").textContent, "27%");
    assert.equal(get("rebleeding").textContent, "43.8%");
    assert.equal(get("error").hidden, true);
  });

  test(file + ": maximum and grouped historical outcomes", () => {
    const {get, set, calculate, endoscopy} = loadCalculator(file);
    set("age", 85);
    set("hr", 120);
    set("sbp", 80);
    set("comorbidity", "major");
    endoscopy(true);
    set("diagnosis", "cancer");
    set("stigmata", "blood");
    calculate();
    assert.equal(get("clinical-score").textContent, "7");
    assert.equal(get("complete-score").textContent, "11");
    assert.equal(get("mortality").textContent, "41.1%");
    assert.equal(get("rebleeding").textContent, "41.8%");
  });

  test(file + ": detects inconsistent endoscopic findings", () => {
    const {get, set, calculate, endoscopy} = loadCalculator(file);
    set("age", 48);
    set("hr", 75);
    set("sbp", 122);
    set("comorbidity", "none");
    endoscopy(true);
    set("diagnosis", "none");
    set("stigmata", "blood");
    calculate();
    assert.equal(get("error").hidden, false);
    assert.equal(get("result").hidden, true);
  });

  test(file + ": no data transmission or fake telemetry", () => {
    const {html} = loadCalculator(file);
    assert.ok(!/fetch\s*\(/.test(html));
    assert.ok(!/HMAC_SHA256_|Air-Gapped Active|PHI Interceptions/.test(html));
    assert.ok(!/<script[^>]+src=/.test(html));
  });
}
