import assert from "node:assert/strict";
import { test } from "node:test";

import { initGlobalAlertDismissal } from "../../src/scripts/global-alert.js";

function setup(cookie, settings = true, canWrite = true) {
  let click;
  let changePreference;
  let removed = false;
  let writtenCookie;
  const button = {
    hidden: true,
    value: "456",
    addEventListener(event, callback) {
      assert.equal(event, "click");
      click = callback;
    },
    closest() {
      return { remove: () => (removed = true) };
    },
  };
  const cookies = {
    preference: () => settings,
    on(event, callback) {
      assert.equal(event, "changePreference");
      changePreference = callback;
    },
    set(...args) {
      writtenCookie = args;
    },
    get() {
      return canWrite ? writtenCookie?.[1] : undefined;
    },
  };
  globalThis.document = {
    cookie,
    querySelector: () => button,
  };
  initGlobalAlertDismissal(cookies);
  return {
    button,
    click: () => click(),
    changeSettings(value) {
      settings = value;
      changePreference({ settings: value });
    },
    get removed() {
      return removed;
    },
    get writtenCookie() {
      return writtenCookie;
    },
  };
}

test("dismissal merges existing cookies and writes catalogue-compatible IDs", () => {
  const state = setup(
    "dismissed_notifications=%5B%22123%22%5D; dismissed_notifications=%5B789%5D",
  );
  assert.equal(state.button.hidden, false);
  state.click();
  assert.equal(state.removed, true);
  assert.deepEqual(state.writtenCookie, [
    "dismissed_notifications",
    "[123,789,456]",
    { session: true },
  ]);
  assert.equal(
    document.cookie,
    "dismissed_notifications=; Path=/; Max-Age=0; SameSite=Lax",
  );
});

test("dismissal requires settings cookie consent", () => {
  const state = setup("", false);
  assert.equal(state.button.hidden, true);
  state.click();
  assert.equal(state.writtenCookie, undefined);
  assert.equal(state.removed, false);

  state.changeSettings(true);
  assert.equal(state.button.hidden, false);
  state.click();
  assert.deepEqual(state.writtenCookie, [
    "dismissed_notifications",
    "[456]",
    { session: true },
  ]);
});

test("failed cookie writes keep the alert and restore previous dismissals", (t) => {
  const error = t.mock.method(console, "error", () => {});
  const state = setup("dismissed_notifications=%5B123%5D", true, false);

  state.click();

  assert.equal(state.removed, false);
  assert.equal(error.mock.callCount(), 1);
  assert.equal(
    document.cookie,
    "dismissed_notifications=%5B123%5D; Path=/; SameSite=Lax",
  );
});
