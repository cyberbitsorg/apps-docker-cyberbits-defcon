const { Pool } = require("pg");
const config = require("../config");

const pool = new Pool({
  connectionString: config.databaseUrl,
  max: 10,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
});

pool.on("error", (err) => {
  console.error("Unexpected Postgres error:", err.message);
});

module.exports = pool;
