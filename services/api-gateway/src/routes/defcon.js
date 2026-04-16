const { Router } = require("express");
const { getCurrentDefcon, getDefconHistory } = require("../db/queries/defcon");

const router = Router();

router.get("/", async (req, res, next) => {
  try {
    const data = await getCurrentDefcon();
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.get("/history", async (req, res, next) => {
  try {
    const hours = Math.min(parseInt(req.query.hours) || 24, 168);
    const history = await getDefconHistory(hours);
    res.json({ history });
  } catch (err) {
    next(err);
  }
});

module.exports = router;
