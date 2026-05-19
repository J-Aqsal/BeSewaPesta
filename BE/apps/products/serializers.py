from rest_framework import serializers

from .models import (
    ProductGalleries,
    Products,
    VariantOptions,
    VariantTypes,
    ProductSpecifications,
    ProductVariantCombinationView,
    ProductVariantCombinations,
    ProductVariantCombinationOptions,
)
from .services import (
    calculate_available_stock_for_combinations,
    calculate_price_range,
)

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

    class Meta:
        model = VariantOptions
        fields = ["idOption", "valueOption"]

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

class VariantCombinationSerializer(serializers.ModelSerializer):
    idVariantCombination = serializers.IntegerField(source="id", read_only=True)
    stock = serializers.SerializerMethodField()
    options = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    gallery = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariantCombinations
        fields = ["idVariantCombination", "stock", "options", "price", "gallery"]

    def get_stock(self, obj):
        stock_map = self.context.get("variant_combination_stock_map", {})
        return stock_map.get(obj.id, 0)

    def get_options(self, obj):
        option_map = self.context.get("variant_combination_option_map", {})
        return option_map.get(obj.id, [])

    def get_price(self, obj):
        price_map = self.context.get("variant_combination_price_map", {})
        return price_map.get(obj.id)

    def get_gallery(self, obj):
        gallery_map = self.context.get("variant_combination_gallery_map", {})
        return gallery_map.get(obj.id, [])

class ProductDetailSerializer(
    serializers.ModelSerializer
):
    idProduct = serializers.CharField(source="id", read_only=True)
    productName = serializers.CharField(source="name")
    productDescription = serializers.CharField(source="description")
    priceRange = serializers.SerializerMethodField()
    unitPrice = serializers.CharField(source="price_unit")
    thumbnail = serializers.CharField(source="photo")
    availableStock = serializers.SerializerMethodField()
    gallery = serializers.SerializerMethodField()
    variantTypes = serializers.SerializerMethodField()
    variantCombinations = serializers.SerializerMethodField()
    specifications = serializers.SerializerMethodField()
    
    class Meta:
        model = Products
        fields = [
            "idProduct",
            "productName",
            "productDescription",
            "priceRange",
            "unitPrice",
            "availableStock",
            "thumbnail",
            "gallery",
            "variantTypes",
            "variantCombinations",
            "specifications",
        ]

    def get_availableStock(self, obj):
        stock_map = self.context.get("stock_map", {})
        return stock_map.get(obj.id, obj.total_stock)

    def get_gallery(self, obj):
        galleries = obj.productgalleries_set.filter(variant_option__isnull=True).order_by("display_order", "id")
        return [g.image_url for g in galleries]

    def _build_variant_combination_context(self, obj):
        if hasattr(self, "_variant_combinations_cache"):
            return

        queryset = obj.productvariantcombinations_set.all().order_by("id")
        combination_ids = list(queryset.values_list("id", flat=True))

        price_rows = ProductVariantCombinationView.objects.filter(
            product_id=obj.id,
            combination_id__in=combination_ids,
        ).values_list("combination_id", "price")

        price_map = {}
        price_values = []
        for combination_id, price in price_rows:
            normalized_price = None
            if price is not None:
                try:
                    numeric_price = float(price)
                    normalized_price = int(numeric_price) if numeric_price.is_integer() else numeric_price
                    price_values.append(numeric_price)
                except Exception:
                    normalized_price = price
            price_map[combination_id] = normalized_price

        option_rows = ProductVariantCombinationOptions.objects.filter(
            product_variant_combination_id__in=combination_ids
        ).values_list("product_variant_combination_id", "variant_option_id")

        option_map = {combination_id: [] for combination_id in combination_ids}
        all_option_ids = set()
        for combination_id, variant_option_id in option_rows:
            option_map.setdefault(combination_id, []).append(variant_option_id)
            all_option_ids.add(variant_option_id)

        gallery_rows = ProductGalleries.objects.filter(
            variant_option_id__in=all_option_ids
        ).order_by("display_order", "id").values_list("variant_option_id", "image_url")

        gallery_by_option = {}
        for variant_option_id, image_url in gallery_rows:
            gallery_by_option.setdefault(variant_option_id, []).append(image_url)

        gallery_map = {}
        for combination_id, option_ids in option_map.items():
            combination_galleries = []
            for variant_option_id in option_ids:
                combination_galleries.extend(gallery_by_option.get(variant_option_id, []))
            gallery_map[combination_id] = combination_galleries

        start_date = self.context.get("start_date")
        end_date = self.context.get("end_date")
        stock_map = calculate_available_stock_for_combinations(obj.id, combination_ids, start_date, end_date)

        serializer_context = {
            **self.context,
            "variant_combination_price_map": price_map,
            "variant_combination_option_map": option_map,
            "variant_combination_gallery_map": gallery_map,
            "variant_combination_stock_map": stock_map,
        }

        self._variant_combinations_cache = VariantCombinationSerializer(queryset, many=True, context=serializer_context).data
        self._cached_price_range = calculate_price_range(obj, price_values)

    def get_variantCombinations(self, obj):
        self._build_variant_combination_context(obj)
        return self._variant_combinations_cache

    def get_priceRange(self, obj):
        self._build_variant_combination_context(obj)
        return getattr(self, "_cached_price_range", calculate_price_range(obj, []))

    def get_variantTypes(self, obj):
        variant_types = obj.varianttypes_set.prefetch_related("variantoptions_set").all().order_by("id")
        return VariantTypeSerializer(variant_types, many=True, context=self.context).data

    def get_specifications(self, obj):
        return list(
            ProductSpecifications.objects.filter(product_id=obj.id)
            .order_by("id")
            .values_list("specification", flat=True)
        )