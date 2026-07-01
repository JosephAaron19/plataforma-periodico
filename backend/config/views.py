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


from django.views import View
from django.http import FileResponse, Http404, HttpResponseForbidden
from pathlib import Path
from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
import mimetypes

class ServeMediaView(View):
    """
    Serves files from MEDIA_ROOT.
    Public files (like cover images/portadas) are served directly.
    Private files (like payment receipts/comprobantes) require a valid, non-expired temporary signature token.
    """
    def get(self, request, path):
        # 1. Clean and check physical file existence
        file_path = Path(settings.MEDIA_ROOT) / path
        if not file_path.exists() or not file_path.is_file():
            raise Http404("El archivo no existe.")

        # 2. Determine if the resource requires access protection (payment receipts, etc.)
        # Receipts contain 'comprobante' or 'pago' or 'receipt'
        path_lower = path.lower()
        is_private = 'pago' in path_lower or 'comprobante' in path_lower or 'receipt' in path_lower

        if is_private:
            token = request.GET.get('token')
            if not token:
                # If no token is provided, fall back to checking if the admin user is logged in
                if not request.user.is_authenticated:
                    return HttpResponseForbidden("Acceso denegado: Se requiere un token temporal válido o iniciar sesión.")
            else:
                signer = TimestampSigner()
                try:
                    # Validate signature, max_age of 2 hours (7200 seconds)
                    unsigned_path = signer.unsign(token, max_age=7200)
                    if unsigned_path != path:
                        return HttpResponseForbidden("Acceso denegado: El token no corresponde a este recurso.")
                except (SignatureExpired, BadSignature):
                    return HttpResponseForbidden("Acceso denegado: El token temporal ha expirado o es inválido.")

        # 3. Serve the file with proper MIME type
        content_type, _ = mimetypes.guess_type(str(file_path))
        if not content_type:
            content_type = 'application/octet-stream'

        try:
            return FileResponse(open(file_path, 'rb'), content_type=content_type)
        except Exception as e:
            logger.error(f"Error serving media file {path}: {e}")
            raise Http404("Error al acceder al archivo.")

