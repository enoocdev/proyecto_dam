
from rest_framework import serializers
from .models import Device, Classroom, NetworkDevice

class ClassroomSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
            view_name='classroom-detail',
            lookup_field='pk',
            read_only=True
    )

    class Meta:
        model = Classroom
        fields = ["url", 'id' , 'name']


class NetworkDeviceSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
            view_name='network-device-detail',
            lookup_field='pk',
            read_only=True
    )

    class Meta:
        model = NetworkDevice

        fields = ["url", "id", "name", "ip_address", "username", "password", "api_port"]
        extra_kwargs = {
            'password': {'write_only': True},
            'api_port': {'required': False}, 
            
        }

class DeviceSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
            view_name='device-detail',
            lookup_field='pk',
            read_only=True
    )

    classroom_url = serializers.HyperlinkedRelatedField(
        source='classroom',
        view_name = "classroom-detail",
        read_only= True,
    )

    network_device_url = serializers.HyperlinkedRelatedField(
        source='connected_device',
        view_name = "network-device-detail",
        read_only= True,
    )

    class Meta:
        model = Device
        fields = ["url" ,'id' , 'mac', 'ip', 
                'hostname', "classroom_url" , 'classroom', "network_device_url" ,"connected_device", 
                "switch_port", "is_online", "is_internet_blocked"]
        extra_kwargs = {
            'mac': {'read_only': True},
            "hostname" : {'read_only': True},
            'is_online': {'read_only': True},
            "is_internet_blocked" : {'read_only': True},
            'classroom': {'write_only': True},
            "connected_device" : {'write_only': True},
            'switch_port': {'read_only': False}, 
        }
        
