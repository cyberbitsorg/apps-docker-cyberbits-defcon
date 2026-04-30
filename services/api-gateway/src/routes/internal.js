const { Router } = require("express");
const { invalidateArticlesCache } = require("../cache/redis");
const config = require("../config");

const router = Router();

router.use((req, res, next) => {
  const token = req.headers["x-internal-token"];
  if (!token || token !== config.internalSecret) {
    return res.status(401).json({ error: "Unauthorized" });
  }
  next();
});

router.post("/cache/invalidate", async (req, res) => {
  await invalidateArticlesCache();
  res.json({ invalidated: true });
});

module.exports = router;
