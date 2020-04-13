#!/usr/bin/env python
# Pop msg off queue, extract metadata, send to Solr 

from __future__ import print_function
import sys, os, time
import json
import pika
import sys, os
from extract import raster, vector, common
import solr.request
import subprocess

RMQ_HOST   = '127.0.0.1'
RMQ_USER   = 'rabbitmq'
RMQ_PASS   = 'rabbitmq'
RMQ_QUEUE  = 'geoedf-all'

LOG_PATH   = '/tmp/messages.txt'

UNSPEC_KEY = 'unknown'
RASTER_KEY = 'raster'
SHAPE_KEY  = 'shape'


def callback(ch, method, properties, body):
    '''React to message on queue'''

    # binary message to string
    body = body.decode()
    # string to json
    data = json.loads(body)
    # print for debug
    print(json.dumps(data, indent=3))

    # index by item number
    paths = {}
    for item in data['paths']: 
        paths[int(item['item'])] = item['name']

    if data['action'] == 'rename':
        print('action: rename...')
        source = os.path.join(paths[0], paths[2])
        destination = os.path.join(paths[1], paths[3])
        solr.request.renameFile(source, destination)
        print(source, " renamed to ", destination)
    elif data['action'] == 'opened-file':
        print('action: opened-file...')
        filename = os.path.normpath(os.path.join(data['cwd'],paths[0]))
        fileext = os.path.splitext(paths[0])[1]
        while(os.path.isfile(filename) is not True):
            time.sleep(2)
        if fileext in raster.extensions:
            metadata = raster.getMetadata(filename) 
            print("new file indexed to solr: ", json.dumps(metadata, indent=3))
            solr.request.newFile(metadata)
        elif fileext in vector.extensions:
            metadata = vector.getMetadata(filename)
            print("new file indexed to solr:  ", json.dumps(metadata, indent=3))
            solr.request.newFile(metadata)
        else:
            metadata = common.basicData(filename)
            solr.request.newFile(metadata)
            print("new file indexed to solr: ", json.dumps(metadata, indent=3))
    elif data['action'] == 'deleted':
        print("action: deleted...")
        filename = os.path.normpath(os.path.join(paths[0] ,paths[1]))
        solr.request.deleteFile(filename)
        print(filename, " deleted from solr")
        

if __name__ == "__main__":

    # Connect to our queue in RabbitMQ
    credentials = pika.PlainCredentials(RMQ_USER, RMQ_PASS)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RMQ_HOST, credentials=credentials))
    channel    = connection.channel()
    result     = channel.queue_declare(RMQ_QUEUE, durable=True)

    # Create exchange to distribute messages
    # channel.exchange_declare(exchange, exchange_type='direct')
    
    
    # Set our callback function, wait for msgs
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(result.method.queue, callback, auto_ack=True)
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()
