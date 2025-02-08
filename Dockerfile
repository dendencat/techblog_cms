# Create a non-root user with specific UID/GID
RUN addgroup --gid 1000 appgroup && \
    adduser --uid 1000 --gid 1000 --system --group appuser

# Set working directory and create logs directory
WORKDIR /app
RUN mkdir -p /app/logs && \
    chown -R appuser:appgroup /app && \
    chmod -R 755 /app

# Switch to non-root user
USER appuser:appgroup
