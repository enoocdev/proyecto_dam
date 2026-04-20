# Serializadores de la API REST para dispositivos aulas y equipos de red
from rest_framework import serializers
from .models import Device, Classroom, NetworkDevice, AllowedHost

# Serializador de aulas con gestion de asignacion de dispositivos
class ClassroomSerializer(serializers.ModelSerializer):
    devices = serializers.PrimaryKeyRelatedField(
        source='device_set',
        many=True,
        queryset=Device.objects.all(),
        required=False,
    )

    class Meta:
        model = Classroom
        fields = ['id', 'name', 'devices', 'is_internet_blocked']
        extra_kwargs = {
            'is_internet_blocked': {'read_only': True},
        }

    def create(self, validated_data):
        devices = validated_data.pop('device_set', [])
        classroom = Classroom.objects.create(**validated_data)
        for device in devices:
            device.classroom = classroom
            device.save()
        return classroom

    def update(self, instance, validated_data):
        devices = validated_data.pop('device_set', None)
        instance.name = validated_data.get('name', instance.name)
        instance.save()

        if devices is not None:
    # Desasigna los dispositivos que ya no pertenecen a esta aula
            instance.device_set.exclude(pk__in=[d.pk for d in devices]).update(classroom=None)
            # Asigna los nuevos dispositivos a esta aula
            for device in devices:
                device.classroom = instance
                device.save()

        return instance


# Serializador de equipos de red con la contrasena oculta en respuestas
class NetworkDeviceSerializer(serializers.ModelSerializer):

    class Meta:
        model = NetworkDevice

        fields = ["id", "name", "ip_address", "username", "password", "api_port"]
        extra_kwargs = {
            'password': {'write_only': True},
            'api_port': {'required': False}, 
            
        }

# Serializador de dispositivos monitorizados con campos de solo lectura
class DeviceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Device
        fields = ['id', 'mac', 'ip',
                'hostname', 'classroom', 'connected_device',
                'switch_port', 'is_online', 'is_internet_blocked']
        extra_kwargs = {
            'mac': {'read_only': True},
            'hostname': {'read_only': True},
            'is_online': {'read_only': True},
            'is_internet_blocked': {'read_only': True},
            'switch_port': {'read_only': False},
        }
        

# Serializador simple de aulas con solo id y nombre para selectores
class ClassRoomSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classroom
        fields = ['id', 'name', 'is_internet_blocked']


# Serializador para peticiones de bloqueo de internet
# Acepta opcionalmente la IP del host al que se permite el acceso
class AllowedHostSerializer(serializers.ModelSerializer):
    classroom_name = serializers.CharField(source='classroom.name', read_only=True, default=None)

    class Meta:
        model = AllowedHost
        fields = ['id', 'ip_address', 'name', 'classroom', 'classroom_name']
