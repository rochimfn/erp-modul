from django.http import JsonResponse, HttpResponse
from django.db import transaction
from rest.models import Sales
from sales.kafka import producer, topic
import json
import logging

logger = logging.getLogger(__name__)

def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

def validate_body_sale(json_data):
    customer_name = json_data['customer_name']
    if len(customer_name) == 0:
        raise Exception('customer_name is not valid')
    
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


def create_sales(json_data):
    customer_name = json_data['customer_name']
    products = json_data['products']
    
    with transaction.atomic():
        sale = Sales()
        sale.customer_name = customer_name
        sale.products = products
        sale.status = 'CREATED'
        sale.save()

    return sale.id


@transaction.atomic
def create_quote(request):
    if request.method == 'POST':
        json_data = json.loads(request.body)
        print(json_data) # debug

        try:
            validate_body_sale(json_data=json_data)
        except Exception as e:
            logger.error('Error when validating body ' + str(e))
            return JsonResponse(data={'success': False, 'error': 'Error request body is malfored' }, status=400)
        
        create_success = False
        for _ in range(3):
            try:
                sales_id = create_sales(json_data)
                create_success = True
                break
            except Exception as e:
                logger.error('Error when claiming stock ' + str(e))
                continue

        if create_success:
            for _ in range(3):
                try:
                    message = json.dumps({
                        "sales_id": sales_id,
                        "products": json_data['products']
                    })
                    producer.produce(topic,  value=message)
                    break
                except Exception:
                    logger.error('Error when sending event to kafka')
                    continue


            return JsonResponse(data={'success': True, 'message': 'Successfully create sales' }, status=200)
        else:
            return JsonResponse(data={'success': False, 'error': 'Failed to create sales' }, status=500)    
    
    else:
        return JsonResponse(data={'success': False, 'error': 'HTTP method not supported' }, status=500)

