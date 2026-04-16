const Redis = require("ioredis");
const config = require("../config");

const redis = new Redis(config.redisUrl, {
  lazyConnect: true,
  retryStrategy: (times) => Math.min(times * 100, 3000),
  maxRetriesPerRequest: 3,
});

redis.on("error", (err) => {
  console.error("Redis error:", err.message);
});

const ARTICLES_CACHE_KEY = "articles:latest";
const ARTICLES_CACHE_TTL = 600; // 10 minutes

async function getCachedArticles() {
  try {
    const data = await redis.get(ARTICLES_CACHE_KEY);
    return data ? JSON.parse(data) : null;
  } catch {
    return null;
  }
}

async function setCachedArticles(articles) {
  try {
    await redis.set(ARTICLES_CACHE_KEY, JSON.stringify(articles), "EX", ARTICLES_CACHE_TTL);
  } catch {
    // cache is best-effort
  }
}

async function invalidateArticlesCache() {
  try {
    await redis.del(ARTICLES_CACHE_KEY);
  } catch {
    // ignore
  }
}

// Subscribe to cache invalidation signals from the aggregator
async function subscribeToInvalidation() {
  const sub = new Redis(config.redisUrl);
  sub.on("error", (err) => console.error("Redis sub error:", err.message));

  sub.subscribe("channel:articles:updated", (err) => {
    if (err) console.error("Subscribe error:", err.message);
    else console.log("Subscribed to cache invalidation channel");
  });

  sub.on("message", (channel, message) => {
    if (channel === "channel:articles:updated") {
      console.log("Cache invalidation received — flushing articles cache");
      invalidateArticlesCache().catch(() => {});
    }
  });
}

module.exports = {
  redis,
  getCachedArticles,
  setCachedArticles,
  invalidateArticlesCache,
  subscribeToInvalidation,
};
