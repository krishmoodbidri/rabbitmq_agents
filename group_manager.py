#!/usr/bin/env python3
import argparse
import grp
import os
import pwd
import sys


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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Group management script")
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
