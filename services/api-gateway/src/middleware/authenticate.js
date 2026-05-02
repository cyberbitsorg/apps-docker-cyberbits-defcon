const jwt = require("jsonwebtoken");
const { v4: uuidv4 } = require("uuid");
const config = require("../config");

module.exports = function authenticate(req, res, next) {
  const header = req.headers.authorization || "";
  const token = header.startsWith("Bearer ") ? header.slice(7) : null;
  if (!token) return res.status(401).json({ error: "Unauthorized" });
  try {
    const payload = jwt.verify(token, config.authSecret, { algorithms: ["HS256"] });
    req.userId = payload.sub || "admin";
    req.sessionId = payload.jti || uuidv4();
    next();
  } catch {
    res.status(401).json({ error: "Invalid or expired token" });
  }
};
