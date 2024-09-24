from django.db import models

class Inventory(models.Model):
    id = models.BigAutoField(primary_key=True)
    product_name = models.CharField(max_length=255)
    product_type = models.CharField(max_length=255)
    stock = models.IntegerField()
    price = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class InventoryHistory(models.Model):
    id = models.BigAutoField(primary_key=True)
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    stock_before = models.IntegerField()
    stock_after  = models.IntegerField()
    stock_diff  = models.IntegerField()
    sales_id  = models.IntegerField(null=True)
    price  = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

