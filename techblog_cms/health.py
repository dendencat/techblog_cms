"""
Health check views for monitoring
"""
import logging
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.views import View

logger = logging.getLogger(__name__)


class HealthCheckView(View):
    """Basic health check endpoint"""
    
    def get(self, request):
        return JsonResponse({
            'status': 'healthy',
            'service': 'techblog_cms'
        })


class ReadinessCheckView(View):
    """Readiness check - verifies all dependencies are accessible"""
    
    def get(self, request):
        checks = {
            'database': self._check_database(),
            'cache': self._check_cache(),
        }
        
        all_healthy = all(checks.values())
        status_code = 200 if all_healthy else 503
        
        return JsonResponse({
            'status': 'ready' if all_healthy else 'not_ready',
            'checks': checks
        }, status=status_code)
    
    def _check_database(self):
        """Check database connectivity"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def _check_cache(self):
        """Check cache connectivity"""
        try:
            cache.set('health_check', 'ok', 10)
            value = cache.get('health_check')
            return value == 'ok'
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return False