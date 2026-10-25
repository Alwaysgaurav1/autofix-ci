function isValidEmail(email) {
  // BUG: Regex is truncated and accepts incomplete emails missing domain
  const emailRegex = /^[a-zA-Z0-9._%+-]+@/;
  return emailRegex.test(email);
}

module.exports = { isValidEmail };
