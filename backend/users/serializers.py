from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from users.models import Account


class LoginUsersSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = [
            "id",
            "email",
            "username",
            "company_name",
            "logo",
            "salogan",
            "address",
            "city",
            "gstin",
            "pan",
            "pincode",
            "mobile",
            "state",
            "statecode",
            "bank_name",
            "bank_account",
            "bank_ifsc",
            "swift_code",
            "permissions",
        ]

    def get_permissions(self, obj):
        return obj.get_all_permissions()

    # def to_representation(self, instance):
    #     data = super(LoginUsersSerializer, self).to_representation(instance)
    #     return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = [
            "id",
            "email",
            "username",
            "company_name",
            "logo",
            "salogan",
            "address",
            "city",
            "gstin",
            "pan",
            "pincode",
            "mobile",
            "state",
            "statecode",
            "bank_name",
            "bank_account",
            "bank_ifsc",
            "swift_code",
        ]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    new_password2 = serializers.CharField(required=True)

    def validate_new_password(self, new_password):
        validate_password(new_password)
        return new_password
