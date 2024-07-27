#!/usr/bin/env python
import dataset
import json
import pika
import shlex
import rc_util
from datetime import datetime
from subprocess import Popen, PIPE
from rc_rmq import RCRMQ
import rabbit_config as rcfg

task = "group_member"

args = rc_util.get_args()
logger = rc_util.get_logger(args)

# Initialize db
db = dataset.connect(f"sqlite:///{rcfg.db_path}/user_reg.db")
table = db["groups"]

# Instantiate rabbitmq object
rc_rmq = RCRMQ({"exchange": rcfg.Exchange, "exchange_type": "topic"})


def insert_db(operation, groupname, msg):
    if operation == "remove":
        op = 0
    elif operation == "add":
        op = 1

    # SQL insert
    table.insert(
        {
            "user": msg["username"],
            "group": groupname,
            "operation": op,
            "date": datetime.now(),
            "host": msg["host"],
            "updated_by": msg["updated_by"],
            "interface": msg.get("interface", ""),
        }
    )


def group_member(ch, method, properties, body):
    """
    Properties:
      correlation_id (str): The UUID for the request.
      reply_to       (str): The RabbitMQ queue name for reply to send to.

    Message(body):
      username    (str): The user to be added/removed from groups.
      groups     (dict): A dictionary with `add` or `remove` key.
        add      (list): A list of groups to be added for the user.
        remove   (list): A list of groups to be removed for the user.
      updated_by  (str): The user who request the change.
      host        (str): Hostname where the request comes from.
      interface   (str): whether it's from CLI or WebUI.

    Returns:
      status (bool): Whether or not the operation executed successfully.
      errmsg  (str): Detailed error message if operation failed.
      task    (str): The task name of the agent who handle the message.
    """
    msg = json.loads(body)
    username = msg["username"]
    msg["task"] = task

    try:
        if "remove" in msg["groups"]:
            for each_group in msg["groups"]["remove"]:
                logger.debug(
                    f"Removing user {username} from group {each_group}"
                )
                if str(rcfg.bright_cm_version).split(".")[0] == "8":
                    grp_remove_user_cmd = (
                        '/cm/local/apps/cmd/bin/cmsh -n -c "group; removefrom'
                        f' {each_group} groupmembers {username}; commit;"'
                    )
                else:
                    grp_remove_user_cmd = (
                        '/cm/local/apps/cmd/bin/cmsh -n -c "group; removefrom'
                        f' {each_group} members {username}; commit;"'
                    )

                logger.info(f"Running command: {grp_remove_user_cmd}")
                proc = Popen(
                    shlex.split(grp_remove_user_cmd), stdout=PIPE, stderr=PIPE
                )
                out, err = proc.communicate()
                logger.debug(f"Result: {err}")
                logger.info(
                    f"User {username} is removed from {each_group} group"
                )
                insert_db("remove", each_group, msg)

        if "add" in msg["groups"]:
            for each_group in msg["groups"]["add"]:
                logger.debug(f"Adding user {username} to group {each_group}")
                if str(rcfg.bright_cm_version).split(".")[0] == "8":
                    grp_add_user_cmd = (
                        '/cm/local/apps/cmd/bin/cmsh -n -c "group; append'
                        f' {each_group} groupmembers {username}; commit;"'
                    )
                else:
                    grp_add_user_cmd = (
                        '/cm/local/apps/cmd/bin/cmsh -n -c "group; append'
                        f' {each_group} members {username}; commit;"'
                    )

                logger.info(f"Running command: {grp_add_user_cmd}")
                proc = Popen(
                    shlex.split(grp_add_user_cmd), stdout=PIPE, stderr=PIPE
                )
                out, err = proc.communicate()
                logger.debug(f"Result: {err}")
                logger.info(f"User {username} is added to {each_group} group")
                insert_db("add", each_group, msg)

        msg["success"] = True

    except Exception:
        msg["success"] = False
        msg["errmsg"] = (
            "Exception raised, while adding user to group {groupname}, check"
            " the logs for stack trace"
        )
        logger.error("", exc_info=True)

    corr_id = properties.correlation_id
    reply_to = properties.reply_to

    logger.debug(f"corr_id: {corr_id} \n reply_to: {reply_to}")
    # send response to the callback queue
    if reply_to:
        props = pika.BasicProperties(correlation_id=corr_id)
        logger.debug("Sending confirmation back to reply_to")
        rc_rmq.publish_msg(
            {"routing_key": reply_to, "props": props, "msg": msg}
        )
    else:
        print("Error: no reply_to")

    logger.debug(f"User {username} confirmation sent from {task}")

    ch.basic_ack(delivery_tag=method.delivery_tag)


logger.info(f"Start listening to queue: {task}")
rc_rmq.bind_queue(queue=task, routing_key="group_member.*", durable=True)

rc_rmq.start_consume({"queue": task, "cb": group_member})

logger.info("Disconnected")
rc_rmq.disconnect()
