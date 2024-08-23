#!/bin/bash

user=$1
group_to=$2
rc=0

if [[ -z "${group_to}" ]]; then
  echo "Usage: $0 USER TARGET_GROUP"
  exit 1
elif [[ "${group_to}" != "gpfs4" && "${group_to}" != "gpfs5" ]]; then
  echo "Target group should be \"gpfs4\" or \"gpfs5\", got \"${group_to}\"."
  exit 1
fi

getent passwd "$user" > /dev/null 2&>1

if [[ $? -ne 0 ]]; then
  echo "The user $user does not exist"
  exit 1
fi

cd /cm/shared/rabbitmq_agents || exit
source venv/bin/activate

./account_manager.py "$user" hold

if [[ "$group_to" == "gpfs4" ]]; then
  group_from=gpfs5
else
  group_from=gpfs4
fi

if [[ -d "/$group_from/data/user/home/$user" ]]; then
  rsync -a --delete "/$group_from/data/user/home/$user/" "/$group_to/data/user/home/$user"

  ./group_manager.py "$user" -g "$group_to"
  ./group_manager.py "$user" -d -g "$group_from"
else
  echo User home directory does not exist.
  rc=1
fi

./account_manager.py "$user" ok
exit $rc
