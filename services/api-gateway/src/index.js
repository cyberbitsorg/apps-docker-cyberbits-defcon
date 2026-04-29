const express = require("express");
const cors = require("cors");
const helmet = require("helmet");
const config = require("./config");
const sessionIdMiddleware = require("./middleware/sessionId");
const authenticate = require("./middleware/authenticate");
const errorHandler = require("./middleware/errorHandler");
const { loginLimiter } = require("./middleware/rateLimiter");

const authRouter = require("./routes/auth");
const articlesRouter = require("./routes/articles");
const defconRouter = require("./routes/defcon");
const adminRouter = require("./routes/admin");
const healthRouter = require("./routes/health");
const internalRouter = require("./routes/internal");

const app = express();

// Trust the Nginx reverse proxy sitting in front of this service
app.set("trust proxy", 1);

app.use(helmet());
app.use(cors({
  origin: config.corsOrigin,
  methods: ["GET", "POST", "PATCH"],
  allowedHeaders: ["Content-Type", "X-Session-ID", "Authorization"],
}));
app.use(express.json());
app.use(sessionIdMiddleware);

// Public routes
app.use("/api/v1/auth", loginLimiter, authRouter);
app.use("/api/v1/health", healthRouter);
app.use("/internal", internalRouter);

// All /api/v1/* routes below require a valid JWT
app.use("/api/v1", authenticate);
app.use("/api/v1/articles", articlesRouter);
app.use("/api/v1/defcon", defconRouter);
app.use("/api/v1/admin", adminRouter);

app.use(errorHandler);

app.listen(config.port, () => {
  console.log(`API gateway running on port ${config.port} [${config.nodeEnv}]`);
});
