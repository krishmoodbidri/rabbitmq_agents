#!/usr/bin/env python
import json
from rc_rmq import RCRMQ

task = "user_reg_event_log"

# Instantiate rabbitmq object
rc_rmq = RCRMQ({"exchange": "RegUsr", "exchange_type": "topic"})


# Define your callback function
def log_user_reg_events(ch, method, properties, body):
    # Retrieve message
    msg = json.loads(body)

    # Retrieve routing key
    routing_key = method.routing_key
    print(f"Got a message with routing key: {routing_key}")
    print(msg)

    # Acknowledge message
    ch.basic_ack(delivery_tag=method.delivery_tag)


print("Start listening to queue: {}".format(task))
rc_rmq.start_consume(
    {
        "queue": task,  # Define your Queue name
        "routing_key": "#",  # Define your routing key
        "cb": log_user_reg_events,  # Pass in callback function you just define
    }
)
