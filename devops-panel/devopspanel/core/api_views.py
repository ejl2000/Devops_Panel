from rest_framework import viewsets, permissions
from .models import ServiceButton, ServiceGroup, Environment, SubGroup
from .serializers import ServiceButtonSerializer, ServiceGroupSerializer, EnvironmentSerializer, SubGroupSerializer

class ServiceGroupViewSet(viewsets.ModelViewSet):
    queryset = ServiceGroup.objects.all()
    serializer_class = ServiceGroupSerializer
    permission_classes = [permissions.IsAuthenticated]

class SubGroupViewSet(viewsets.ModelViewSet):
    queryset = SubGroup.objects.all()
    serializer_class = SubGroupSerializer
    permission_classes = [permissions.IsAuthenticated]

class EnvironmentViewSet(viewsets.ModelViewSet):
    queryset = Environment.objects.all()
    serializer_class = EnvironmentSerializer
    permission_classes = [permissions.IsAuthenticated]

class ServiceButtonViewSet(viewsets.ModelViewSet):
    queryset = ServiceButton.objects.all()
    serializer_class = ServiceButtonSerializer
    permission_classes = [permissions.IsAuthenticated]
