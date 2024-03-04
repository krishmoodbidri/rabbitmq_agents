#!/usr/bin/env python3
import argparse
import grp
import json
import os
import pika
import pwd
import rabbit_config as rcfg
import sys
import uuid
from rc_rmq import RCRMQ
from rc_util import timeout


# Instantiate rabbitmq object
rc_rmq = RCRMQ({"exchange": rcfg.Exchange, "exchange_type": "topic"})


def user_exists(username):
    try:
        pwd.getpwnam(username)
    except KeyError:
        return False
    return True


def group_exists(groupname):
    try:
        grp.getgrnam(groupname)
    except KeyError:
        return False
    return True


@timeout(rcfg.Function_timeout)
def manage_group(op, usernames, groupname, debug=False):
    callback_queue = rc_rmq.bind_queue(exclusive=True)
    rpc_queue = f"group_member.{op}"
    corr_id = str(uuid.uuid4())
    status = dict.fromkeys(usernames, False)
    response = 0

    def handler(ch, method, properties, body):
        if debug:
            print("Message received:")
            print(body)

        nonlocal corr_id
        nonlocal status
        nonlocal response
        msg = json.loads(body)
        username = msg["username"]

        if properties.correlation_id == corr_id:
            status[username] = msg["success"]
            response += 1
            if not msg["success"]:
                print("Something's wrong, please try again.")

        if len(status) == response:
            rc_rmq.stop_consume()
            rc_rmq.disconnect()

    if debug:
        print(f"Adding user(s) {', '.join(usernames)} to group {groupname}")
        print(f"Callback queue: {callback_queue}, correlation_id: {corr_id}")

    for user in usernames:
        rc_rmq.publish_msg(
            {
                "routing_key": rpc_queue,
                "props": pika.BasicProperties(
                    correlation_id=corr_id, reply_to=callback_queue
                ),
                "msg": {
                    "groups": {f"{op}": [f"{groupname}"]},
                    "username": user,
                },
            }
        )

    rc_rmq.start_consume(
        {
            "queue": callback_queue,
            "exclusive": True,
            "bind": False,
            "cb": handler,
        }
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Group management script")
    parser.add_argument("--debug", action="store_true", help="Debug mode")
    parser.add_argument(
        "-d",
        "--delete",
        action="store_true",
        help="Delete the user(s) from the group",
    )
    parser.add_argument(
        "-g", "--group", required=True, help="The Group to add the user(s)"
    )
    parser.add_argument(
        "users",
        metavar="USER",
        nargs="+",
        help="User(s) to be add to the group",
    )
    args = parser.parse_args()

    executed_by = os.getenv("USER")

    exist_users = []
    miss = False

    # Check if all of the users exist
    for user in args.users:
        if not user_exists(user):
            print(f"{user} does not exist.", file=sys.stderr)
            miss = True
        else:
            exist_users.append(user)

    # Check if the group exists
    if not group_exists(args.group):
        print(f"{args.group} does not exist.", file=sys.stderr)
        miss = True

    if miss:
        print("A user and/or group does not exist.", file=sys.stderr)
        print("Abort.", file=sys.stderr)
        exit(1)

    elif exist_users:
        op = "remove" if args.delete else "add"
        manage_group(op, exist_users, args.group, args.debug)
    else:
        print("No user to change", file=sys.stderr)
        print("Abort.", file=sys.stderr)
        sys.exit(1)
