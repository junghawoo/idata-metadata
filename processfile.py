#!/usr/bin/env python
# Pop msg off queue, extract metadata, send to Solr 

from __future__ import print_function
import sys, os
import json
import pika
import sys, os
from extract import raster, vector
from index import index

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

	msgfile = open(LOG_PATH,'a')
	msgfile.write(" [x] Received %r" % body)

	data    = json.loads(body)
	outdata = {}
	outstr  = ''
	key     = UNSPEC_KEY

	for path in data['paths']:

		if path['objtype'] == 'PARENT':
			continue

		filename = os.path.normpath(
			os.path.join(data['cwd'],path['name'])
		)
 
		outdata['oper']     = path['objtype']
		outdata['filename'] = filename
		fileext             = os.path.splitext(filename)[1]
        
                if fileext in raster.extensions:
                        metadata = raster.getMetadata(filepath) 
                        index.newFile(metadata)
                elif fileext in VECTOR_EXT:
                        metadata = vector.getMetadata(filepath)
                        index.newFile(metadata)

		outstr += json.dumps(outdata)

	print(' [x] Msg:',outstr) # TODO For debug. Remove?

	# TODO Send metadata to Solr

	msgfile.write(" [x] Done")
	msgfile.close()
	ch.basic_ack(delivery_tag=method.delivery_tag)

if __name__ == "__main__":

	# Connect to our queue in RabbitMQ
	connection = pika.BlockingConnection(
		pika.ConnectionParameters(
			host        =RMQ_HOST
			,credentials=pika.PlainCredentials(
				RMQ_USER
				,RMQ_PASS
			)
		)
	 )
	channel    = connection.channel()
	result     = channel.queue_declare(
		queue=RMQ_QUEUE
		,durable=True
	)

	# Set our callback function, wait for msgs
	channel.basic_qos(prefetch_count=1)
	channel.basic_consume(callback,queue=result.method.queue)
	channel.start_consuming()
	print(' [*] Waiting for messages. To exit press CTRL+C')
