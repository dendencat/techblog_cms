# Create a non-root user
RUN addgroup --system appgroup && \
    adduser --system --group appuser && \
    adduser appuser appgroup

# Create logs directory with proper permissions
RUN mkdir -p /app/logs && \
    chown -R appuser:appgroup /app/logs && \
    chmod 775 /app/logs

# Switch to non-root user
USER appuser
