from rest_framework import serializers
from .models import ServiceButton, ServiceGroup, Environment, SubGroup, CodeBase, CodeBaseDependency, ServiceButtonLink
from devopspanel.users.models import Role, CustomUser

class ServiceGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceGroup
        fields = ['id', 'name', 'environment']

class SubGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubGroup
        fields = ['id', 'name', 'group']

class ServiceButtonLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceButtonLink
        fields = ['id', 'name', 'url', 'location']

class CodeBaseDependencySerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeBaseDependency
        fields = ['id', 'name', 'url', 'dependencies']

class CodeBaseSerializer(serializers.ModelSerializer):
    dependencies = CodeBaseDependencySerializer(many=True, read_only=True)

    class Meta:
        model = CodeBase
        fields = ['id', 'name', 'url', 'dependencies']

class ServiceButtonSerializer(serializers.ModelSerializer):
    groups = ServiceGroupSerializer(many=True, read_only=True)
    subgroup = SubGroupSerializer(read_only=True)
    links = ServiceButtonLinkSerializer(many=True, read_only=True)
    code_base = CodeBaseSerializer(read_only=True)
    tags = serializers.StringRelatedField(many=True)

    class Meta:
        model = ServiceButton
        fields = [
            'id', 'name', 'description', 'url', 'tags', 'groups',
            'subgroup', 'environment', 'links', 'executive', 'ip',
            'port', 'version', 'location', 'is_multi_link', 'has_code_base',
            'code_base', 'connections',
        ]

class EnvironmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Environment
        fields = ['id', 'name']
