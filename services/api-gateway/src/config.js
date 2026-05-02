const required = (name) => {
  const val = process.env[name];
  if (!val) throw new Error(`Missing required env var: ${name}`);
  return val;
};

module.exports = {
  port: parseInt(process.env.PORT || "4000", 10),
  nodeEnv: process.env.NODE_ENV || "development",
  databaseUrl: required("DATABASE_URL"),
  redisUrl: process.env.REDIS_URL || "redis://localhost:6379",
  aggregatorUrl: process.env.AGGREGATOR_URL || "http://news-aggregator:8000",
  corsOrigin: required("CORS_ORIGIN"),
  authSecret: required("AUTH_SECRET"),
  adminPassword: required("ADMIN_PASSWORD"),
  internalSecret: required("INTERNAL_SECRET"),
};
