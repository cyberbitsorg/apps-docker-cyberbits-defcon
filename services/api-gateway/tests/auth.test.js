const { test } = require("node:test");
const assert = require("node:assert/strict");

const { timingSafeCompare } = require("../src/routes/auth");

test("equal strings return true", () => {
  assert.strictEqual(timingSafeCompare("correct-horse-battery", "correct-horse-battery"), true);
});

test("different strings return false", () => {
  assert.strictEqual(timingSafeCompare("correct-horse-battery", "wrong-password"), false);
});

test("different-length strings return false", () => {
  assert.strictEqual(timingSafeCompare("short", "much-longer-password"), false);
});

test("empty string does not equal non-empty", () => {
  assert.strictEqual(timingSafeCompare("", "password"), false);
});
