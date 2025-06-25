from rest_framework import serializers
from connections.models import Connection

class ConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Connection
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class ConnectionRequestSerializer(serializers.Serializer):
    mentor_id = serializers.IntegerField()