from confluent_kafka import Producer
import socket
import json

conf = {'bootstrap.servers': 'localhost:19092',
        'client.id': socket.gethostname()}
topic = 'sales_quotation'

producer = Producer(conf)
message = json.dumps({
	"sales_id": 1,
	"products": [
		{"inventory_id": 1, "amount": 10}, 
		{"inventory_id": 2, "amount": 20}
	]
})
producer.produce(topic,  value=message)
producer.flush()