from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UserSerializer


class MeView(APIView):
    """
    GET /api/v1/auth/me/

    Returns the currently authenticated user's public profile.
    Requires authentication — unauthenticated requests receive 403.

    This endpoint is intentionally read-only.  No POST / PUT / PATCH /
    DELETE methods are defined.

    Note: APIView is synchronous; no async def needed here.  The ASGI
    server (Daphne) handles concurrency at the transport layer.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        serializer = UserSerializer(request.user)
        return Response(serializer.data)