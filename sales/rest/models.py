from django.db import models

class Sales(models.Model):
    id = models.BigAutoField(primary_key=True)
    customer_name = models.CharField(max_length=255) # customer must have dedicated table
    products = models.JSONField()
    status = models.CharField(max_length=255) # status should have dedicated table to show how the status progressed (timeline)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)