module.exports = function errorHandler(err, req, res, next) {
  console.error(err.message, err.stack);
  const status = err.status || 500;
  res.status(status).json({
    error: status < 500 ? err.message : "Internal server error",
  });
};
