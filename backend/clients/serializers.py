from rest_framework import serializers
from clients.models import Client
from users.serializers import UserSerializer


class ClientSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Client
        fields = [
            "id",
            "name",
            "address",
            "city",
            "gstin",
            "aadhar",
            "panno",
            "pincode",
            "mobile",
            "email",
            "state",
            "statecode",
            "currency",
            "country",
            "user",
        ]
        read_only_fields = ("user",)

    def validate(self, attrs):
        if len(attrs["pincode"]) != 6:
            raise serializers.ValidationError("Plese enter a valid pincode.")
        return attrs


class ClientBillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ("name", "address", "city")
        read_only_fields = ("user",)

    def validate(self, attrs):
        if len(attrs["pincode"]) != 6:
            raise serializers.ValidationError("Plese enter a valid pincode.")
        return attrs
