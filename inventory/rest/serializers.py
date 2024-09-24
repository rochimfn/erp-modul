from rest_framework import serializers

class InventorySerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    product_name = serializers.CharField()
    product_type = serializers.CharField()
    stock = serializers.IntegerField()
    price = serializers.FloatField()