
from django.contrib.auth.models import Permission, Group
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name" ,"username", "password", "is_active", "groups"]
        extra_kwargs = {
            'password': {'write_only': True},
            'groups': {'required': False}, 
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


class UserPermisionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = "__all__"


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = "__all__"
