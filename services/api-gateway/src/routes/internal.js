const { Router } = require("express");
const { invalidateArticlesCache } = require("../cache/redis");

const router = Router();

router.post("/cache/invalidate", async (req, res) => {
  await invalidateArticlesCache();
  res.json({ invalidated: true });
});

module.exports = router;
