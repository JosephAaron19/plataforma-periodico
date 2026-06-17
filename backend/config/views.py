import redis
from django.db import connections
from django.db.utils import OperationalError
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

class HealthCheckView(APIView):
    """
    General health check endpoint.
    Verifies connections to PostgreSQL and Redis.
    """
    def get(self, request, *args, **kwargs):
        # Check PostgreSQL connection
        db_status = "connected"
        try:
            db_conn = connections['default']
            db_conn.ensure_connection()
            with db_conn.cursor() as cursor:
                cursor.execute("SELECT 1;")
        except OperationalError:
            db_status = "disconnected"
            logger.error("Database connection failure in general health check")

        # Check Redis connection
        redis_status = "connected"
        try:
            r = redis.Redis.from_url(settings.CELERY_BROKER_URL, socket_timeout=3)
            r.ping()
        except Exception as e:
            redis_status = "disconnected"
            logger.error(f"Redis connection failure in general health check: {e}")

        overall_status = "ok" if db_status == "connected" and redis_status == "connected" else "error"
        
        return Response({
            "status": overall_status,
            "service": "backend",
            "database": db_status,
            "redis": redis_status
        }, status=status.HTTP_200_OK if overall_status == "ok" else status.HTTP_500_INTERNAL_SERVER_ERROR)


class DatabaseHealthCheckView(APIView):
    """
    Specific database health check.
    """
    def get(self, request, *args, **kwargs):
        try:
            db_conn = connections['default']
            db_conn.ensure_connection()
            with db_conn.cursor() as cursor:
                cursor.execute("SELECT 1;")
            return Response({
                "status": "ok",
                "database": "connected"
            }, status=status.HTTP_200_OK)
        except OperationalError as e:
            logger.error(f"Database health check failed: {e}")
            return Response({
                "status": "error",
                "database": "disconnected"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RedisHealthCheckView(APIView):
    """
    Specific Redis health check.
    """
    def get(self, request, *args, **kwargs):
        try:
            r = redis.Redis.from_url(settings.CELERY_BROKER_URL, socket_timeout=3)
            r.ping()
            return Response({
                "status": "ok",
                "redis": "connected"
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return Response({
                "status": "error",
                "redis": "disconnected"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
