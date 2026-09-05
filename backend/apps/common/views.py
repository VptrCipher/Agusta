from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .metadata import build_resource_metadata


class ResourceMetadataView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({"resources": build_resource_metadata(user=request.user)})


class HealthView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({"status": "ok"})
