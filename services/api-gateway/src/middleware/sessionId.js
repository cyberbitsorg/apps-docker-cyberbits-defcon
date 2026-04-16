const { v4: uuidv4 } = require("uuid");

module.exports = function sessionIdMiddleware(req, res, next) {
  const sessionId = req.headers["x-session-id"];
  if (sessionId && /^[0-9a-f-]{36}$/i.test(sessionId)) {
    req.sessionId = sessionId;
  } else {
    req.sessionId = uuidv4();
  }
  next();
};
