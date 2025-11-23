from rest_framework import serializers
from .models import Device, Group


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    
    devices = serializers.HyperlinkedRelatedField(
        many  = True,
        read_only = True,
        view_name = 'device-detail'
    )

    devices_ids = serializers.PrimaryKeyRelatedField(
        many = True,
        write_only = True,
        queryset = Device.objects.all(),

    )

    class Meta:
        model = Group
        fields = ( 'url' ,'id' , 'name', 'devices', 'devices_ids')


    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
    

        

class DeviceSerializer(serializers.HyperlinkedModelSerializer):
    
    groups = serializers.HyperlinkedRelatedField(
        many = True,
        read_only=True,
        view_name="group-detail" 
    )

    groups_ids = serializers.PrimaryKeyRelatedField(
        many = True,
        write_only = True,
        queryset= Group.objects.all(),
        
    )

    class Meta:
        model = Device
        fields = ('url' , 'id' , 'mac', 'ip', 'hostname', 'groups', 'groups_ids')

        

