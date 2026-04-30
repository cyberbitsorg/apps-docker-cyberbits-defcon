const { Router } = require("express");
const pool = require("../db/pool");
const { redis } = require("../cache/redis");
const config = require("../config");

const router = Router();

router.get("/", async (req, res) => {
  let ok = true;

  try {
    await pool.query("SELECT 1");
  } catch {
    ok = false;
  }

  try {
    await redis.ping();
  } catch {
    ok = false;
  }

  try {
    const resp = await fetch(`${config.aggregatorUrl}/health`, {
      signal: AbortSignal.timeout(3000),
    });
    if (!resp.ok) ok = false;
  } catch {
    ok = false;
  }

  res.status(ok ? 200 : 503).json({ status: ok ? "ok" : "degraded" });
});

module.exports = router;
