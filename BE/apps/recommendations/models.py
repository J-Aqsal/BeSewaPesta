from django.db import models

class UpsellRelations(models.Model):
    source_product = models.ForeignKey('products.Products', models.DO_NOTHING, db_column='source_product_id', related_name='upsell_source')
    source_variant = models.ForeignKey('products.ProductVariantCombinations', models.DO_NOTHING, db_column='source_variant_id', related_name='upsell_source_variant', null=True, blank=True)
    target_product = models.ForeignKey('products.Products', models.DO_NOTHING, db_column='target_product_id', related_name='upsell_target')
    target_variant = models.ForeignKey('products.ProductVariantCombinations', models.DO_NOTHING, db_column='target_variant_id', related_name='upsell_target_variant', null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'upsell_relations'
