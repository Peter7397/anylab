from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import User, Role, UserRole

User = get_user_model()


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model"""
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'permissions', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer for UserRole model"""
    role = RoleSerializer(read_only=True)
    assigned_by_username = serializers.CharField(source='assigned_by.username', read_only=True)
    
    class Meta:
        model = UserRole
        fields = ['id', 'user', 'role', 'assigned_by', 'assigned_by_username', 'assigned_at', 'is_active']
        read_only_fields = ['assigned_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    roles = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'employee_id', 'department', 'position', 'phone',
            'avatar', 'is_active', 'is_staff', 'is_superuser',
            'last_login_ip', 'created_at', 'updated_at', 'roles'
        ]
        read_only_fields = ['created_at', 'updated_at', 'last_login', 'date_joined']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False}
        }
    
    def get_roles(self, obj):
        """Get active roles for the user"""
        user_roles = UserRole.objects.filter(user=obj, is_active=True)
        return RoleSerializer([ur.role for ur in user_roles], many=True).data
    
    def create(self, validated_data):
        """Create a new user"""
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        """Update user"""
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users"""
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'first_name', 'last_name',
            'employee_id', 'department', 'position', 'phone'
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': True}
        }
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating users"""
    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'employee_id',
            'department', 'position', 'phone', 'avatar', 'is_active'
        ]

