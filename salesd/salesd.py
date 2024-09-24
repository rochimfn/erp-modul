from confluent_kafka import Consumer, KafkaError, KafkaException
from multiprocessing import Process, Queue
import logging
import sys
import json
import signal
import requests

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)

URL = 'http://localhost:8000/rest/sale/'

class Switch():
    is_active = True
    def __init__(self):
        signal.signal(signal.SIGINT, self.turn_off)
        signal.signal(signal.SIGTERM, self.turn_off)

    def turn_off(self, *_):
        self.is_active = False


def consumer(q: Queue, switch: Switch):
    logging.info("consumer started")
    consumer_topic = 'sales_quotation'
    conf = {'bootstrap.servers': 'localhost:19092',
                'group.id': 'salesd'}
    consumer = Consumer(conf)
    consumer.subscribe([consumer_topic])
    
    while switch.is_active:
        msg = consumer.poll(1.0)
        if msg is None: continue
        
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                sys.stderr.write('%% %s [%d] reached end at offset %d\n' % (msg.topic(), msg.partition(), msg.offset()))
            elif msg.error(): raise KafkaException(msg.error())
        else:
            q.put((msg.key(), msg.value()))

    logging.info("receiving signal")
    consumer.close()
    q.put(signal.SIGINT)


def processor(consumer_q: Queue):
    logging.info('job processor started')
    while True:
        logging.info("job processor poll")
        item = consumer_q.get()
        if item == signal.SIGINT:
            return
        
        _ = item[0] # value not needed
        value = item[1]
        for _ in range(3):
            try:
                result = requests.post(url=URL, data=value)
                print(result) # TODO: raise if not success
                break
            except:
                continue


def main():
    s = Switch()
    consumer_q = Queue()

    consumer_process = Process(target=consumer, args=(consumer_q,s,))
    transformer_process = Process(target=processor, args=(consumer_q,))

    consumer_process.start()
    transformer_process.start()

    consumer_process.join()
    transformer_process.join()

    consumer_process.close()
    transformer_process.close()

    logging.info('all done')


if __name__ == '__main__':
    main()