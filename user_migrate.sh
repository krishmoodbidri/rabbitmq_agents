#!/bin/bash

group_options=(gpfs4 gpfs5)
gpfs4_home="/gpfs4/data/user/home"
gpfs5_home="/gpfs5/data/user/home"

user=$1
group_to=$2

if [[ -z "${group_to}" ]]; then
  echo "Usage: $0 USER TARGET_GROUP"
  exit 1
elif [[ ! " ${group_options[*]} " =~ [[:space:]]${group_to}[[:space:]] ]]; then
  echo "Invalid target group"
  echo "Available options: ${group_options[*]}, got ${group_to}"
  exit 1
fi

if ! getent passwd "$user" > /dev/null 2>&1; then
  echo "The user $user does not exist"
  exit 1
fi

cd /cm/shared/rabbitmq_agents || exit
source venv/bin/activate

if [[ "$group_to" == "gpfs4" ]]; then
  group_from=gpfs5
  dir_from="$gpfs5_home/$user/"
  dir_to="$gpfs4_home/$user"
else
  group_from=gpfs4
  dir_from="$gpfs4_home/$user/"
  dir_to="$gpfs5_home/$user"
fi

if [[ -d "/$group_from/data/user/home/$user" ]]; then
  ./account_manager.py "$user" hold

  rsync -a --delete "$dir_from" "$dir_to"

  ./group_manager.py "$user" -g "$group_to"
  ./group_manager.py "$user" -d -g "$group_from"

  ./account_manager.py "$user" ok
else
  echo User home directory does not exist.
  exit 1
fi
