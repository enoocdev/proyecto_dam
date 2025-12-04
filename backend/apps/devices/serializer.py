
from django.contrib.auth.models import Group
from rest_framework import serializers
from .models import Device, DeviceGroup
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name" ,"username", "password", "is_active", "groups"]
        extra_kwargs = {
            'password': {'write_only': True},
            'groups': {'required': False} 
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        groups_data = validated_data.pop('groups', [])
        user = User.objects.create_user(password=password, **validated_data)
        if groups_data:
            user.groups.set(groups_data)
        
        return user
    

    def update(self, instance, validated_data):

        password = validated_data.pop("passsword", None)
        if password:
            instance.set_password(password)

        if 'groups' in validated_data:
            groups_data = validated_data.pop('groups')
            instance.groups.set(groups_data)

        return super().update(instance, validated_data)


class UserGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["id", "name"]



class DeviceGroupSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
            view_name='device-group-detail',
            lookup_field='pk',
            read_only=True
    )
    
    class Meta:
        model = DeviceGroup
        fields = ["url", 'id' , 'name', "devices"]


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

    

    class Meta:
        model = Device
        fields = ["url" ,'id' , 'mac', 'ip', 'hostname', "groups"]



