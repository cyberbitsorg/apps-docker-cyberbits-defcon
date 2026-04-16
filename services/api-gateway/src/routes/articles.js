const { Router } = require("express");
const { getArticles, markArticleRead, markAllRead, getLastRefreshedAt } = require("../db/queries/articles");

const router = Router();

router.get("/", async (req, res, next) => {
  try {
    const limit = Math.min(parseInt(req.query.limit) || 20, 50);
    const offset = parseInt(req.query.offset) || 0;
    const source = req.query.source || null;
    const unreadOnly = req.query.unread_only === "true";
    const sessionId = req.sessionId;

    const articles = await getArticles({ limit, offset, source, unreadOnly, sessionId });
    const lastRefreshedAt = await getLastRefreshedAt();

    res.json({ articles, total: articles.length, last_refreshed_at: lastRefreshedAt });
  } catch (err) {
    next(err);
  }
});

router.patch("/read-all", async (req, res, next) => {
  try {
    const count = await markAllRead({ sessionId: req.sessionId });
    res.json({ marked_count: count });
  } catch (err) {
    next(err);
  }
});

router.patch("/:id/read", async (req, res, next) => {
  try {
    const articleId = req.params.id;
    const isRead = req.body?.is_read !== undefined ? Boolean(req.body.is_read) : true;

    if (!/^[0-9a-f-]{36}$/i.test(articleId)) {
      return res.status(400).json({ error: "Invalid article id" });
    }

    const row = await markArticleRead({ articleId, sessionId: req.sessionId, isRead });
    res.json({ id: articleId, is_read: row.is_read, read_at: row.read_at });
  } catch (err) {
    next(err);
  }
});

module.exports = router;
