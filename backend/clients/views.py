from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from clients.models import Client
from .serializers import ClientSerializer


class ClientViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for listing, creating, retrieving, updating,
    and deleting Client objects for the authenticated user.
    """

    serializer_class = ClientSerializer
    # permission_classes = [IsAuthenticated]
    # lookup_field = "pk"  # optional, default is "pk"

    def get_queryset(self):
        return Client.objects.all()
        # return Client.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
