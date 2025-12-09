
from django.contrib.auth.models import Permission, Group
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password_validator = serializers.CharField(write_only=True, required=False)
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name" ,"username", "password", "password_validator", "is_active", "groups"]
        extra_kwargs = {
            'password': {'write_only': True},
            'groups': {'required': False}, 
        }


    def validate(self, data):

        if 'password' in data:
            password = data.get('password')
            password_validator = data.get('password_validator')

            if not password_validator:
                raise serializers.ValidationError({"password_validator": "Este campo es obligatorio si cambias la contraseña."})

            if password != password_validator:
                raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})

        if 'password_validator' in data:
            del data['password_validator']

        return data
    


    def create(self, validated_data):
        password = validated_data.pop('password')
        groups_data = validated_data.pop('groups', [])
        user = User.objects.create_user(password=password, **validated_data)
        if groups_data:
            user.groups.set(groups_data)
        
        return user
    

    def update(self, instance, validated_data):
        request_user = self.context['request'].user

        
        if not request_user.is_staff:
            validated_data.pop('groups', None) 
            validated_data.pop('is_active', None)  


        password = validated_data.pop("password", None)
        if password:
            instance.set_password(password)
            instance.save() 

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




class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        
        token['username'] = user.username
        token['is_superuser'] = user.is_superuser
        return token

    def validate(self, attrs):

        data = super().validate(attrs)
        data['is_superuser'] = self.user.is_superuser
        data['permissions'] = list(self.user.get_all_permissions())
        data['username'] = self.user.username

        return data
