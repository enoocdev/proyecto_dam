
from rest_framework import serializers
from .models import Device, DeviceGroup

class DeviceGroupSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
            view_name='device-group-detail',
            lookup_field='pk',
            read_only=True
    )

    devices = serializers.HyperlinkedRelatedField(
        view_name = "device-detail",
        read_only= True,
        many  = True
    )

    devices_id = serializers.PrimaryKeyRelatedField(
        queryset = Device.objects.all(),
        source="devices",
        write_only=True,
        many=True,
        required=False
    )
    
    class Meta:
        model = DeviceGroup
        fields = ["url", 'id' , 'name', "devices", "devices_id"]


class DeviceSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
            view_name='device-detail',
            lookup_field='pk',
            read_only=True
    )

    groups = serializers.HyperlinkedRelatedField(
        view_name='device-group-detail',
        read_only=True,
        many = True
    )

    groups_id = serializers.PrimaryKeyRelatedField(
        queryset= DeviceGroup.objects.all(),
        source='groups',          
        write_only=True,
        many=True,
        required = False
    )

    class Meta:
        model = Device
        fields = ["url" ,'id' , 'mac', 'ip', 'hostname', "groups", "groups_id"]



