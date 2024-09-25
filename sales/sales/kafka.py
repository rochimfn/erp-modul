from confluent_kafka import Producer
import socket

conf = {'bootstrap.servers': 'localhost:19092',
        'client.id': socket.gethostname()}
topic = 'sales_quotation'

producer = Producer(conf)