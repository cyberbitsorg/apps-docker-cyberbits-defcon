const pool = require("../pool");

const SOURCE_DISPLAY = {
  hackread:              "HackRead",
  infosecurity_magazine: "Infosecurity Magazine",
  security_affairs:      "Security Affairs",
  techradar_security:    "TechRadar Security",
  the_register:          "The Register",
};

async function getArticles({ limit = 20, offset = 0, source, unreadOnly, userId, minScore, maxScore, search }) {
  const params = [limit, offset, userId];
  const conditions = ["a.is_deleted = FALSE"];

  if (source) {
    params.push(source);
    conditions.push(`a.source = $${params.length}`);
  }

  if (minScore != null) {
    params.push(minScore);
    conditions.push(`a.defcon_score >= $${params.length}`);
  }

  if (maxScore != null) {
    params.push(maxScore);
    conditions.push(`a.defcon_score <= $${params.length}`);
  }

  if (unreadOnly) {
    conditions.push(`(rs.is_read IS NULL OR rs.is_read = FALSE)`);
  }

  if (search) {
    params.push(`%${search}%`);
    conditions.push(`(a.title ILIKE $${params.length} OR a.summary ILIKE $${params.length})`);
  }

  const where = conditions.join(" AND ");

  const sql = `
    SELECT
      a.id,
      a.title,
      a.summary,
      a.url,
      a.source,
      a.published_at,
      a.fetched_at,
      a.raw_categories,
      a.defcon_score,
      COALESCE(rs.is_read, FALSE) AS is_read,
      rs.read_at,
      COUNT(*) OVER () AS total_count
    FROM articles a
    LEFT JOIN article_read_state rs
      ON rs.article_id = a.id AND rs.user_id = $3
    WHERE ${where}
    ORDER BY a.published_at DESC
    LIMIT $1 OFFSET $2
  `;

  const result = await pool.query(sql, params);
  const total = result.rows.length > 0 ? parseInt(result.rows[0].total_count, 10) : 0;
  const articles = result.rows.map((row) => ({
    ...row,
    id: row.id,
    source_display: SOURCE_DISPLAY[row.source] || row.source,
    categories: row.raw_categories || [],
    is_read: row.is_read === true,
  }));
  return { articles, total };
}

async function markArticleRead({ articleId, userId, isRead }) {
  const result = await pool.query(
    `
    INSERT INTO article_read_state (article_id, user_id, is_read, read_at)
    VALUES ($1, $2, $3, NOW())
    ON CONFLICT (article_id, user_id) DO UPDATE
      SET is_read = $3, read_at = NOW()
    RETURNING id, article_id, is_read, read_at
    `,
    [articleId, userId, isRead]
  );
  return result.rows[0];
}

async function markAllRead({ userId, isRead = true }) {
  const result = await pool.query(
    `
    INSERT INTO article_read_state (article_id, user_id, is_read, read_at)
    SELECT a.id, $1, $2, NOW()
    FROM articles a
    WHERE a.is_deleted = FALSE
    ON CONFLICT (article_id, user_id) DO UPDATE
      SET is_read = $2, read_at = NOW()
    `,
    [userId, isRead]
  );
  return result.rowCount;
}

async function getLastRefreshedAt() {
  const result = await pool.query(
    "SELECT refreshed_at FROM last_refresh WHERE id = 1"
  );
  return result.rows[0]?.refreshed_at || null;
}

module.exports = { getArticles, markArticleRead, markAllRead, getLastRefreshedAt };
