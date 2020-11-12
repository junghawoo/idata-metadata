#!/usr/bin/env python
# Pop msg off queue, extract metadata, send to Solr 

from __future__ import print_function
import sys, os, time
import json
import pika
import sys, os
from extract import raster, vector, common
import solr.request
import preview.registerlayer
import subprocess

RMQ_HOST   = str(os.getenv('RMQ_HOST',"rabbitmq"))
RMQ_USER   = str(os.getenv('RMQ_USER',"rabbitmq"))
RMQ_PASS   = str(os.getenv('RMQ_PASS',"rabbitmq"))
RMQ_EXCHANGE = str(os.getenv('RMQ_EXCHANGE',"rabbitmq"))
RMQ_QUEUE  = str(os.getenv('RMQ_QUEUE',"geoedf-all"))

LOG_PATH   = '/tmp/messages.txt'

UNSPEC_KEY = 'unknown'
RASTER_KEY = 'raster'
SHAPE_KEY  = 'shape'

def requeue_message(ch, body):
    '''Requeue the same message for re-processing'''
    ch.basic_publish(
            exchange = RMQ_EXCHANGE,
            routing_key = 'geoedf',
            body = body)

# if indexing to Solr fails, the message will be requeued 
# so, whenever a message is processed, we need to make sure 
# the status of the filesystem is still the same
# for e.g. if processing a rename, ensure there is still a file 
# with this new name
def callback(ch, method, properties, body):
    '''React to message on queue'''

    requeued = False

    try:
        # binary message to string
        body = body.decode()
        # string to json
        data = json.loads(body)
        # print for debug
        with open(LOG_PATH,'a+') as logfile:
            logfile.write(json.dumps(data, indent=3))

        # determine if message is from CMS or AuditBeat
        cms_file = False

        if 'actor' in data:
            cms_file = True

        # index by item number
        paths = {}
        for item in data['paths']: 
            paths[int(item['item'])] = item['name']

        if data['action'] == 'rename' or data['action'] == 'renamed':
            with open(LOG_PATH,'a+') as logfile:
                logfile.write('action: rename...\n')
            source = os.path.join(paths[0], paths[2])
            destination = os.path.join(paths[1], paths[3])
            # only proceed if destination still exists as a file
            if os.path.isfile(destination):
                try:
                    solr.request.renameFile(source, destination)
                except:
                    # exception occurred when sending Solr request
                    # requeue for trying later
                    requeued = True
                    requeue_message(ch,body)
                    with open(LOG_PATH,'a+') as logfile:
                        logfile.write('requeued message')
            with open(LOG_PATH,'a+') as logfile:
                logfile.write("%s renamed to %s" % (source,destination))
        elif data['action'] == 'opened-file':
            with open(LOG_PATH,'a+') as logfile:
                logfile.write('action: opened-file...\n')
            if cms_file:
                filename = os.path.normpath(os.path.join(data['cwd'],paths[0]))
            else:
                filename = os.path.normpath(paths[1])
            # if this is no longer a valid file, skip
            # possibly out of date message that was requeued
            if os.path.isfile(filename):
                fileext = os.path.splitext(os.path.split(filename)[1])[1]
                with open(LOG_PATH,'a+') as logfile:
                    logfile.write('process file %s' % filename)
                # extract metadata based on filetype
                # assume that metadata extractor will not raise an exception
                # a basic dictionary will be returned in the worst case
                if fileext in raster.extensions:
                    metadata = raster.getMetadata(filename) 
                    with open(LOG_PATH,'a+') as logfile:
                        logfile.write('extracted metadata: %s' % metadata)
                    # register file for preview
                    with open(LOG_PATH,'a+') as logfile:
                        logfile.write('registering file for preview')
                    preview.registerlayer.update_qgs(filename)
                elif fileext in vector.extensions:
                    # if this is a shapefile and not all supporting files present,
                    # then requeue the message to wait until all files available
                    if fileext == '.shp':
                        if vector.shapefileComplete(filename):
                            metadata = vector.getMetadata(filename)
                            # register file for preview
                            preview.registerlayer.update_qgs(filename)
                        else:
                            # requeue message
                            requeued = True
                            requeue_message(ch,body)
                else:
                    metadata = common.basicData(filename)
                # index to Solr, unless requeuing
                try:
                    if not requeued:
                        # add the actor if known
                        if cms_file:
                            metadata['actor'] = data['actor']
                        solr.request.newFile(metadata)
                        with open(LOG_PATH,'a+') as logfile:
                            logfile.write("new file indexed to solr: %s" % json.dumps(metadata, indent=3))
                except:
                    requeued = True
                    requeue_message(ch,body)
                    with open(LOG_PATH,'a+') as logfile:
                        logfile.write('requeued message')
        elif data['action'] == 'deleted':
            with open(LOG_PATH,'a+') as logfile:
                logfile.write("action: deleted...")
            if cms_file:
                filename = os.path.normpath(os.path.join(paths[0],paths[1]))
            else:
                filename = os.path.normpath(path[1])
            # ensure file still does not exist
            if not os.path.isfile(filename):
                try:
                    solr.request.deleteFile(filename)
                    with open(LOG_PATH,'a+') as logfile:
                        logfile.write("%s deleted from solr" % filename)
                except:
                    requeued = True
                    requeue_message(ch,body)
                    with open(LOG_PATH,'a+') as logfile:
                        logfile.write("requeued message")

        # acknowledge this message
        ch.basic_ack(delivery_tag=method.delivery_tag)

    # some unexpected error occurred
    # no choice but to ack this message and move on
    except:
        ch.basic_ack(delivery_tag=method.delivery_tag)

if __name__ == "__main__":

    # Connect to our queue in RabbitMQ
    credentials = pika.PlainCredentials(RMQ_USER, RMQ_PASS)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RMQ_HOST, credentials=credentials))
    channel    = connection.channel()
    result     = channel.queue_declare(RMQ_QUEUE, durable=True)

    # Set our callback function, wait for msgs
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=RMQ_QUEUE, on_message_callback=callback)
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()
