from confluent_kafka import Consumer, KafkaError, KafkaException
from multiprocessing import Process, Queue
from sqlalchemy import create_engine, text, Engine
import json
import logging
import sys
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


def claim_stock(value) -> bool:
    for _ in range(3):
        try:
            result = requests.post(url=URL, data=value)
            if result.status_code == 200:
                return True
            elif result.status_code != 200:
                logging.error('sales failed with error: ', result.json())
                raise Exception('failed claim with error: ', result.json())
        except Exception as e:
            logging.error('claim stock failed with error: ', str(e))
            continue

    return False

def processor(consumer_q: Queue, engine: Engine):
    logging.info('job processor started')
    while True:
        logging.info("job processor poll")
        item = consumer_q.get()
        if item == signal.SIGINT:
            return
        
        _ = item[0] # key not needed
        value = item[1]
        success_claim = claim_stock(value=value)
        obj = json.loads(value)
        for _ in range(3):
            try:
                with engine.connect() as conn:
                    update_stmt = text("UPDATE rest_sales SET status=:status,updated_at=now() WHERE id=:id")
                    result = conn.execute(update_stmt, parameters={'id': obj['sales_id'], 'status': 'PROCESSED' if success_claim else 'FAILED'})
                    conn.commit()
                    logging.info(result.rowcount)
            except Exception as e:
                logging.error(e)
                continue
            # ideally we sent email to the customer 


def main():
    engine = create_engine("postgresql+psycopg2://postgres:password@localhost/sales")

    s = Switch()
    consumer_q = Queue()

    consumer_process = Process(target=consumer, args=(consumer_q,s,))
    processor_process = Process(target=processor, args=(consumer_q,engine,))

    consumer_process.start()
    processor_process.start()

    consumer_process.join()
    processor_process.join()

    consumer_process.close()
    processor_process.close()

    logging.info('all done')


if __name__ == '__main__':
    main()