const { Router } = require("express");
const { adminLimiter } = require("../middleware/rateLimiter");
const config = require("../config");

const router = Router();

router.post("/refresh", adminLimiter, async (req, res, next) => {
  try {
    const response = await fetch(`${config.aggregatorUrl}/trigger`, { method: "POST" });
    if (!response.ok) {
      return res.status(502).json({ error: "Aggregator did not accept trigger" });
    }
    res.json({ triggered: true });
  } catch (err) {
    next(err);
  }
});

module.exports = router;
