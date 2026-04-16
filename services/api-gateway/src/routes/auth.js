const { Router } = require("express");
const jwt = require("jsonwebtoken");
const config = require("../config");

const router = Router();

router.post("/login", (req, res) => {
  const { password } = req.body;
  if (!password || password !== config.adminPassword) {
    return res.status(401).json({ error: "Invalid password" });
  }
  const token = jwt.sign({ sub: "admin" }, config.authSecret, { expiresIn: "12h" });
  res.json({ token });
});

module.exports = router;
