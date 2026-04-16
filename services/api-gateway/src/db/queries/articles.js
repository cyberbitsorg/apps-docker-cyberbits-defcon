const pool = require("../pool");

const SOURCE_DISPLAY = {
  the_hacker_news: "The Hacker News",
  bleeping_computer: "Bleeping Computer",
  dark_reading: "Dark Reading",
  reuters: "Reuters",
};

async function getArticles({ limit = 20, offset = 0, source, unreadOnly, sessionId }) {
  const params = [limit, offset, sessionId];
  const conditions = ["a.is_deleted = FALSE"];

  if (source) {
    params.push(source);
    conditions.push(`a.source = $${params.length}`);
  }

  if (unreadOnly) {
    conditions.push(`(rs.is_read IS NULL OR rs.is_read = FALSE)`);
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
      rs.read_at
    FROM articles a
    LEFT JOIN article_read_state rs
      ON rs.article_id = a.id AND rs.session_id = $3
    WHERE ${where}
    ORDER BY a.published_at DESC
    LIMIT $1 OFFSET $2
  `;

  const result = await pool.query(sql, params);
  return result.rows.map((row) => ({
    ...row,
    id: row.id,
    source_display: SOURCE_DISPLAY[row.source] || row.source,
    categories: row.raw_categories || [],
    is_read: row.is_read === true,
  }));
}

async function markArticleRead({ articleId, sessionId, isRead }) {
  const result = await pool.query(
    `
    INSERT INTO article_read_state (article_id, session_id, is_read, read_at)
    VALUES ($1, $2, $3, NOW())
    ON CONFLICT (article_id, session_id) DO UPDATE
      SET is_read = $3, read_at = NOW()
    RETURNING id, article_id, is_read, read_at
    `,
    [articleId, sessionId, isRead]
  );
  return result.rows[0];
}

async function markAllRead({ sessionId }) {
  const result = await pool.query(
    `
    INSERT INTO article_read_state (article_id, session_id, is_read, read_at)
    SELECT a.id, $1, TRUE, NOW()
    FROM articles a
    WHERE a.is_deleted = FALSE
    ON CONFLICT (article_id, session_id) DO UPDATE
      SET is_read = TRUE, read_at = NOW()
    `,
    [sessionId]
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
