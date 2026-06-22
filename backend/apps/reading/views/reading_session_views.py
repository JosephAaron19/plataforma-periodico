from decimal import Decimal
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.db import transaction, models
from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.core.exceptions import ValidationError

from apps.reading.models.sesion_lectura import SesionLectura
from apps.reading.models.progreso_lectura import ProgresoLectura
from apps.editions.models.edicion import Edicion
from apps.editions.models.edicion_pagina import EdicionPagina
from apps.access.services.access_service import can_user_read_edition, get_or_create_reading_access
from apps.files.services.storage_service import StorageService
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaModulo, AuditoriaAccion, AuditoriaResultado
from apps.audit.utils import get_client_ip, get_user_agent

READING_SESSION_DURATION = getattr(settings, 'READING_SESSION_DURATION', timedelta(hours=2))

class ReadingSessionCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, edi_id):
        """
        POST /api/v1/editions/{edi_id}/reading-session/
        Creates a new secure reading session for an edition if the user has access.
        """
        user = request.user
        ip_addr = get_client_ip(request)
        ua_str = get_user_agent(request)
        
        # 1. Fetch the edition (revalidate IDOR and state)
        try:
            edition = Edicion.objects.using('periodico_db').select_related('empresa').get(id=edi_id, eliminado=False)
        except Edicion.DoesNotExist:
            return Response(
                {"error": "La edición especificada no existe o fue eliminada."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 2. Check reading rights
        if not can_user_read_edition(user, edition):
            AuditService.record_event(
                usuario=user,
                emp_id=edition.empresa_id,
                modulo=AuditoriaModulo.M08,
                accion=AuditoriaAccion.ACCESO_LECTURA_DENEGADO,
                entidad="Edicion",
                entidad_id=str(edition.id),
                resultado=AuditoriaResultado.RECHAZADO,
                motivo="Usuario no tiene autorización de lectura para esta edición.",
                ip_address=ip_addr,
                user_agent=ua_str
            )
            return Response(
                {"error": "No tienes acceso a esta edición o el contenido no está disponible para lectura completa."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 3. Retrieve or create access record for trace
        try:
            with transaction.atomic(using='periodico_db'):
                access = get_or_create_reading_access(user, edition)
                
                # Truncate user agent to fit character varying(150)
                device_str = ua_str[:150] if ua_str else None

                # 4. Create reading session
                reading_session = SesionLectura.objects.using('periodico_db').create(
                    usuario=user,
                    edicion=edition,
                    acceso=access,
                    fecha_inicio=timezone.now(),
                    pagina_inicio=1,
                    dispositivo=device_str,
                    direccion_ip=ip_addr,
                    estado='ACTIVA'
                )
        except Exception as e:
            return Response(
                {"error": f"Error al iniciar sesión de lectura: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 5. Audit successful session creation
        AuditService.record_event(
            usuario=user,
            emp_id=edition.empresa_id,
            modulo=AuditoriaModulo.M08,
            accion=AuditoriaAccion.LECTURA_INICIADA,
            entidad="SesionLectura",
            entidad_id=str(reading_session.id),
            valores_nuevos={
                "id": str(reading_session.id),
                "edicion_id": edition.id,
                "acceso_id": access.id
            },
            resultado=AuditoriaResultado.EXITOSO,
            ip_address=ip_addr,
            user_agent=ua_str
        )

        expiration_time = reading_session.fecha_inicio + READING_SESSION_DURATION

        return Response({
            "session_id": str(reading_session.id),
            "edition_id": edition.id,
            "user_id": user.id,
            "fecha_inicio": reading_session.fecha_inicio.isoformat(),
            "expiration_time": expiration_time.isoformat(),
            "estado": reading_session.estado
        }, status=status.HTTP_201_CREATED)


class ReadingSessionPageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id, page_number):
        """
        GET /api/v1/reading-sessions/{session_id}/pages/{page_number}/
        Retrieves a protected edition page image binarily from private storage.
        Revalidates critical session status and permissions.
        """
        user = request.user
        ip_addr = get_client_ip(request)
        ua_str = get_user_agent(request)
        now = timezone.now()

        # 1. Fetch reading session
        try:
            session = SesionLectura.objects.using('periodico_db').select_related('edicion', 'edicion__empresa').get(id=session_id)
        except (SesionLectura.DoesNotExist, ValidationError):
            return Response(
                {"error": "Sesión de lectura inválida o inexistente."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 2. Prevent cross-user access (Anti-IDOR)
        if session.usuario_id != user.id:
            AuditService.record_event(
                usuario=user,
                emp_id=session.edicion.empresa_id,
                modulo=AuditoriaModulo.M08,
                accion=AuditoriaAccion.ACCESO_LECTURA_DENEGADO,
                entidad="SesionLectura",
                entidad_id=str(session.id),
                resultado=AuditoriaResultado.RECHAZADO,
                motivo="Intento de acceso a sesión de lectura de otro usuario.",
                ip_address=ip_addr,
                user_agent=ua_str
            )
            return Response(
                {"error": "Acceso denegado: esta sesión no te pertenece."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 3. Check if session has expired or is inactive
        if session.estado != 'ACTIVA':
            return Response(
                {"error": f"La sesión de lectura no está activa (Estado: {session.estado})."},
                status=status.HTTP_403_FORBIDDEN
            )

        if now - session.fecha_inicio > READING_SESSION_DURATION:
            # Set state to EXPIRADA
            with transaction.atomic(using='periodico_db'):
                session = SesionLectura.objects.using('periodico_db').select_for_update().get(id=session.id)
                session.estado = 'EXPIRADA'
                session.fecha_fin = now
                session.save(using='periodico_db')

            AuditService.record_event(
                usuario=user,
                emp_id=session.edicion.empresa_id,
                modulo=AuditoriaModulo.M08,
                accion=AuditoriaAccion.SESION_LECTURA_EXPIRADA,
                entidad="SesionLectura",
                entidad_id=str(session.id),
                resultado=AuditoriaResultado.RECHAZADO,
                motivo="La sesión de lectura ha expirado por tiempo transcurrido.",
                ip_address=ip_addr,
                user_agent=ua_str
            )
            return Response(
                {"error": "Tu sesión de lectura ha expirado. Por favor inicia otra sesión."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 4. Critical revalidation of user, edition and company status
        if not user.is_active:
            return Response(
                {"error": "Tu cuenta de usuario se encuentra suspendida o inactiva."},
                status=status.HTTP_403_FORBIDDEN
            )

        edition = session.edicion
        if edition.eliminado or edition.estado != 'PUBLICADA':
            return Response(
                {"error": "La edición ya no se encuentra publicada o fue eliminada."},
                status=status.HTTP_403_FORBIDDEN
            )

        company = edition.empresa
        if company.eliminado or company.estado != 'ACTIVA':
            return Response(
                {"error": "La empresa editora se encuentra inactiva o fue eliminada."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 5. Fetch page metadata and check it belongs to the edition
        try:
            page = EdicionPagina.objects.using('periodico_db').select_related('archivo').get(
                edicion=edition,
                edp_numero_pagina=page_number,
                edp_es_actual=True,
                edp_estado='GENERADA'
            )
        except EdicionPagina.DoesNotExist:
            return Response(
                {"error": f"La página {page_number} no existe en esta edición."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 5b. Validate that archivo belongs to the same company (cross-company IDOR protection)
        archivo = page.archivo
        if archivo.empresa_id is not None and archivo.empresa_id != edition.empresa_id:
            AuditService.record_event(
                usuario=user,
                emp_id=edition.empresa_id,
                modulo=AuditoriaModulo.M08,
                accion=AuditoriaAccion.ACCESO_LECTURA_DENEGADO,
                entidad="EdicionPagina",
                entidad_id=str(page.id),
                resultado=AuditoriaResultado.RECHAZADO,
                motivo="El archivo de la página pertenece a una empresa distinta a la de la edición.",
                ip_address=ip_addr,
                user_agent=ua_str
            )
            return Response(
                {"error": "El recurso solicitado no pertenece a esta edición."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 6. Deliver page image file protectedly using FileResponse from private storage
        try:
            file_path = StorageService.get_private_absolute_path(archivo.ruta_storage)
            if not file_path.exists() or not file_path.is_file():
                return Response(
                    {"error": "El archivo de imagen física no se encuentra disponible en el almacenamiento."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Record audit of serve action
            AuditService.record_event(
                usuario=user,
                emp_id=edition.empresa_id,
                modulo=AuditoriaModulo.M08,
                accion=AuditoriaAccion.PAGINA_SERVIDA,
                entidad="EdicionPagina",
                entidad_id=str(page.id),
                valores_nuevos={
                    "session_id": str(session.id),
                    "edicion_id": edition.id,
                    "numero_pagina": page_number
                },
                resultado=AuditoriaResultado.EXITOSO,
                ip_address=ip_addr,
                user_agent=ua_str
            )

            response = FileResponse(open(file_path, 'rb'), content_type='image/jpeg')
            return response
        except ValueError as e:
            # Raised by StorageService on path traversal attempts
            return Response(
                {"error": "Ruta de archivo inválida."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Error al recuperar el archivo protegido: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReadingSessionProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        """
        POST /api/v1/reading-sessions/{session_id}/progress/
        Input: { "page_number": 5 }
        Updates reading progress for the edition in the user context.
        """
        user = request.user
        ip_addr = get_client_ip(request)
        ua_str = get_user_agent(request)
        now = timezone.now()

        page_number = request.data.get('page_number')
        if page_number is None:
            return Response({"error": "Debe especificar el campo 'page_number'."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            page_number = int(page_number)
        except ValueError:
            return Response({"error": "El campo 'page_number' debe ser un número entero."}, status=status.HTTP_400_BAD_REQUEST)

        if page_number <= 0:
            return Response({"error": "El número de página debe ser mayor a 0."}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Fetch reading session
        try:
            session = SesionLectura.objects.using('periodico_db').select_related('edicion', 'edicion__empresa').get(id=session_id)
        except (SesionLectura.DoesNotExist, ValidationError):
            return Response(
                {"error": "Sesión de lectura inválida o inexistente."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 2. Prevent cross-user access
        if session.usuario_id != user.id:
            return Response(
                {"error": "Acceso denegado: esta sesión no te pertenece."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 3. Check session expiration
        if session.estado != 'ACTIVA':
            return Response(
                {"error": f"La sesión de lectura no está activa (Estado: {session.estado})."},
                status=status.HTTP_403_FORBIDDEN
            )

        if now - session.fecha_inicio > READING_SESSION_DURATION:
            with transaction.atomic(using='periodico_db'):
                session = SesionLectura.objects.using('periodico_db').select_for_update().get(id=session.id)
                session.estado = 'EXPIRADA'
                session.fecha_fin = now
                session.save(using='periodico_db')

            AuditService.record_event(
                usuario=user,
                emp_id=session.edicion.empresa_id,
                modulo=AuditoriaModulo.M08,
                accion=AuditoriaAccion.SESION_LECTURA_EXPIRADA,
                entidad="SesionLectura",
                entidad_id=str(session.id),
                resultado=AuditoriaResultado.RECHAZADO,
                motivo="La sesión de lectura ha expirado por tiempo transcurrido al registrar progreso.",
                ip_address=ip_addr,
                user_agent=ua_str
            )
            return Response(
                {"error": "Tu sesión de lectura ha expirado. Por favor inicia otra sesión."},
                status=status.HTTP_403_FORBIDDEN
            )

        edition = session.edicion
        total_pages = edition.numero_paginas or 0

        # Validate that page number does not exceed total pages
        if total_pages > 0 and page_number > total_pages:
            return Response(
                {"error": f"Número de página fuera de rango. La edición contiene {total_pages} páginas."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. Update or create ProgresoLectura record
        with transaction.atomic(using='periodico_db'):
            progreso, created = ProgresoLectura.objects.using('periodico_db').get_or_create(
                usuario=user,
                edicion=edition,
                defaults={
                    'ultima_pagina': page_number,
                    'porcentaje': Decimal(0),
                    'fecha_ultima_lectura': now
                }
            )

            # Prevent malicious page number regressions (only increase or keep same max read page)
            if not created:
                progreso.ultima_pagina = max(progreso.ultima_pagina, page_number)
            
            if total_pages > 0:
                progreso.porcentaje = (Decimal(progreso.ultima_pagina) / Decimal(total_pages)) * Decimal(100)
            else:
                progreso.porcentaje = Decimal(0)
                
            progreso.fecha_ultima_lectura = now
            progreso.fecha_actualizacion = now
            progreso.save(using='periodico_db')

            # Update session's last read page tracker
            session = SesionLectura.objects.using('periodico_db').select_for_update().get(id=session.id)
            session.pagina_fin = page_number
            session.save(using='periodico_db')

        # 5. Record progress audit log
        AuditService.record_event(
            usuario=user,
            emp_id=edition.empresa_id,
            modulo=AuditoriaModulo.M08,
            accion=AuditoriaAccion.PROGRESO_LECTURA_ACTUALIZADO,
            entidad="ProgresoLectura",
            entidad_id=str(progreso.id),
            valores_nuevos={
                "session_id": str(session.id),
                "edicion_id": edition.id,
                "ultima_pagina": progreso.ultima_pagina,
                "porcentaje": float(progreso.porcentaje)
            },
            resultado=AuditoriaResultado.EXITOSO,
            ip_address=ip_addr,
            user_agent=ua_str
        )

        return Response({
            "progreso_id": progreso.id,
            "edition_id": edition.id,
            "ultima_pagina": progreso.ultima_pagina,
            "porcentaje": float(progreso.porcentaje),
            "fecha_ultima_lectura": progreso.fecha_ultima_lectura.isoformat()
        }, status=status.HTTP_200_OK)
