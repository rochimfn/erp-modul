from django.http import JsonResponse
from django.db import transaction
from rest.models import Inventory, InventoryHistory
from rest.serializers import InventorySerializer
from rest_framework.parsers import JSONParser
import json
import logging

logger = logging.getLogger(__name__)

class StockDepletedException(Exception):
    "Raised amount of sale is greater than available stock"
    pass


# Create your views here.
def index(request):
    for _ in range(3):
        try:
            logger.info('fetching inventory from database')
            inventories = Inventory.objects.all()
            serializer = InventorySerializer(inventories, many=True)
            return JsonResponse(data={'success': True, 'data': serializer.data}, safe=False, status=200)
        except Exception as e:
            logger.error('fetch inventory error' + str(e))
            continue
    return JsonResponse(data={'success': False, 'error': 'Error when fetching data from database' }, status=500)


def validate_body_sale(json_data):
    sales_id = json_data['sales_id']
    if not isinstance(sales_id, int) or sales_id < 1:
        raise Exception('sales_id is not valid')
    
    products = json_data['products']
    if not isinstance(products, list):
        raise Exception('products is not type list')
    
    for product in products:
        inventory_id = product['inventory_id']
        amount = product['amount']
        if not isinstance(inventory_id, int) or inventory_id < 1:
            raise Exception('inventory_id is not valid')
        elif not isinstance(amount, int) or amount < 1:
            raise Exception('amount is not valid')
        


def update_stock(json_data):
    sales_id = json_data['sales_id']
    products = json_data['products']
    with transaction.atomic():
        for product in products:
            inventory_id = product['inventory_id']
            amount = product['amount']
            product = Inventory.objects.select_for_update().get(pk=inventory_id)
            print(amount, product.stock, amount > product.stock)
            if amount > product.stock:
                raise StockDepletedException(f'Sale amount for product {product.product_name} cannot be fulfilled stock ={product.stock}')
            history = InventoryHistory(inventory=product)
            history.stock_before = product.stock
            product.stock = product.stock - amount
            history.stock_after = product.stock
            history.stock_diff = 0 - amount
            history.sales_id = sales_id
            history.price = product.price
            product.save()
            history.save()


@transaction.atomic
def sale(request):
    if request.method == 'POST':
        json_data = json.loads(request.body)
        print(json_data) # debug

        try:
            validate_body_sale(json_data=json_data)
        except Exception as e:
            logger.error('Error when validating body ' + str(e))
            return JsonResponse(data={'success': False, 'error': 'Error request body is malfored' }, status=400)
        
        for _ in range(3):
            try:
                update_stock(json_data)
                return JsonResponse(data={'success': True, 'message': 'Successfully claiming stock' }, status=200)
            except StockDepletedException:
                return JsonResponse(data={'success': False, 'error': 'Amount is greater than stock' }, status=400)
            except Exception as e:
                logger.error('Error when claiming stock ' + str(e))
                continue

        return JsonResponse(data={'success': False, 'error': 'Failed to claim the stock' }, status=500)
        
    
    else:
        return JsonResponse(data={'success': False, 'error': 'HTTP method not supported' }, status=500)

