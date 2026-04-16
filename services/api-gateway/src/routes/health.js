const { Router } = require("express");
const pool = require("../db/pool");
const { redis } = require("../cache/redis");
const config = require("../config");

const router = Router();

router.get("/", async (req, res) => {
  const status = { status: "ok", version: "1.0.0", services: {} };

  try {
    await pool.query("SELECT 1");
    status.services.database = "ok";
  } catch {
    status.services.database = "error";
    status.status = "degraded";
  }

  try {
    await redis.ping();
    status.services.redis = "ok";
  } catch {
    status.services.redis = "error";
    status.status = "degraded";
  }

  try {
    const resp = await fetch(`${config.aggregatorUrl}/health`, { signal: AbortSignal.timeout(3000) });
    status.services.aggregator = resp.ok ? "ok" : "error";
  } catch {
    status.services.aggregator = "error";
  }

  const httpStatus = status.status === "ok" ? 200 : 503;
  res.status(httpStatus).json(status);
});

module.exports = router;
