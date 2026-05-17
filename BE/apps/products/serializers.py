from rest_framework import serializers

from .models import ProductGalleries, Products, VariantOptions, VariantTypes, ProductSpecifications

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

class ProductGallerySerializer(
    serializers.ModelSerializer
):
    idGallery = serializers.IntegerField(source="id", read_only=True)
    urlGallery = serializers.CharField(source="image_url")
    
    class Meta:
        model = ProductGalleries
        fields = ["idGallery", "urlGallery"]


class OptionGallerySerializer(
    serializers.ModelSerializer
):
    idOptionGallery = serializers.IntegerField(source="id", read_only=True)
    urlOptionGallery = serializers.CharField(source="image_url")

    class Meta:
        model = ProductGalleries
        fields = ["idOptionGallery", "urlOptionGallery"]


class VariantOptionSerializer(
    serializers.ModelSerializer
):
    idOption = serializers.IntegerField(source="id", read_only=True)
    valueOption = serializers.CharField(source="value")
    priceModifier = serializers.SerializerMethodField()
    gallery = serializers.SerializerMethodField()
    stockVariantOption = serializers.SerializerMethodField()

    class Meta:
        model = VariantOptions
        fields = ["idOption", "valueOption", "priceModifier", "stockVariantOption", "gallery"]

    def get_priceModifier(self, obj):
        if obj.price_modifier is None:
            return None

        if obj.price_modifier == int(obj.price_modifier):
            return int(obj.price_modifier)

        return float(obj.price_modifier)

    def get_gallery(self, obj):
        galleries = obj.productgalleries_set.all().order_by("display_order", "id")
        return OptionGallerySerializer(galleries, many=True).data

    def get_stockVariantOption(self, obj):
        variant_stock_map = self.context.get("variant_stock_map", {})
        return variant_stock_map.get(obj.id, 0)


class VariantTypeSerializer(
    serializers.ModelSerializer
):
    idVariant = serializers.IntegerField(source="id", read_only=True)
    variantName = serializers.CharField(source="name")
    isRequired = serializers.BooleanField(source="is_required")
    options = serializers.SerializerMethodField()

    class Meta:
        model = VariantTypes
        fields = ["idVariant", "variantName", "isRequired", "options"]

    def get_options(self, obj):
        options = obj.variantoptions_set.all().order_by("id")
        return VariantOptionSerializer(options, many=True, context=self.context).data

class ProductDetailSerializer(
    serializers.ModelSerializer
):
    idProduct = serializers.CharField(source="id", read_only=True)
    productName = serializers.CharField(source="name")
    productDescription = serializers.CharField(source="description")
    productPrice = serializers.IntegerField(source="price")
    unitPrice = serializers.CharField(source="price_unit")
    thumbnail = serializers.CharField(source="photo")
    availableStock = serializers.SerializerMethodField()
    gallery = serializers.SerializerMethodField()
    variantTypes = serializers.SerializerMethodField()
    specifications = serializers.SerializerMethodField()
    
    class Meta:
        model = Products
        fields = [
            "idProduct",
            "productName",
            "productDescription",
            "productPrice",
            "unitPrice",
            "availableStock",
            "thumbnail",
            "gallery",
            "variantTypes",
            "specifications",
        ]

    def get_availableStock(self, obj):
        stock_map = self.context.get("stock_map", {})
        return stock_map.get(obj.id, obj.total_stock)

    def get_gallery(self, obj):
        galleries = obj.productgalleries_set.filter(variant_option__isnull=True).order_by("display_order", "id")
        return ProductGallerySerializer(galleries, many=True).data

    def get_variantTypes(self, obj):
        variant_types = obj.varianttypes_set.all().order_by("id")
        return VariantTypeSerializer(variant_types, many=True, context=self.context).data

    def get_specifications(self, obj):
        return list(
            ProductSpecifications.objects.filter(product_id=obj.id)
            .order_by("id")
            .values_list("specification", flat=True)
        )