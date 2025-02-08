# Set working directory first
WORKDIR /app

# Create a non-root user with specific UID/GID
RUN addgroup --gid 1000 appgroup && \
    adduser --uid 1000 --gid 1000 --system --group appuser

# Create logs directory and set permissions
RUN mkdir -p /app/logs && \
    chown -R appuser:appgroup /app && \
    chmod -R 775 /app && \
    chmod g+s /app/logs

# Switch to non-root user
USER appuser:appgroup
