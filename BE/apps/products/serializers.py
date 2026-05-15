from rest_framework import serializers

from .models import Products

"""
serializers.py berisi kelas-kelas serializer yang digunakan 
untuk mengubah data model menjadi format yang dapat dikirim melalui API,
"""

class ProductCatalogSerializer(
    serializers.ModelSerializer
):

    image = serializers.CharField(
        source="photo"
    )

    stock = serializers.SerializerMethodField()

    class Meta:
        model = Products

        fields = [
            "id",
            "name",
            "image",
            "price",
            "price_unit",
            "stock"
        ]

    def get_stock(self, obj):

        stock_map = self.context.get(
            "stock_map",
            {}
        )

        return stock_map.get(obj.id, 0)