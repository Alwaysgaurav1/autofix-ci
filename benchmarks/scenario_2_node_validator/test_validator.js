const assert = require("assert");
const { isValidEmail } = require("./validator");

try {
  assert.strictEqual(isValidEmail("user@example.com"), true, "Valid email should pass");
  assert.strictEqual(isValidEmail("invalid-email@"), false, "Missing domain should fail");
  console.log("All validator tests passed!");
  process.exit(0);
} catch (err) {
  console.error("FAIL test_validator.js");
  console.error(err.message);
  process.exit(1);
}
