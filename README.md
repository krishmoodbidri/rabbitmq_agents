
# RabbitMQ User Registration Agents 

---

## Overview
This project automates user registration workflows at UAB using **RabbitMQ** to route tasks between systems like the web interface, CLI tools, databases, and email services. It ensures tasks like assigning user IDs, validating data, and sending notifications happen in sequence without manual intervention.  

---

## Key Components 
### 1. **The `RegUsr` Exchange** 
- **Type**: Topic exchange (routes messages using `routing_key` patterns).  
- **Purpose**: Acts as the central hub for all registration-related messages.  

### 2. **Core Scripts** 
- **`self_reg_app` (Web UI)**: Starts the process by sending a `request<queuename>` message with user data.  
- **`create_account.py` (CLI)**: Triggers backend tasks (e.g., UID/GID assignment, email subscriptions).  

### 3. **Queues & Their Jobs** 
| Queue Name               | What It Does                                                                 |  
|--------------------------|-----------------------------------------------------------------------------|  
| `get next uid gid`        | Reserves a unique UID/GID for the user (uses SQLite to track IDs).          |  
| `subscribe mail list`     | Adds the user’s email to mailing lists (e.g., department announcements).    |  
| `git commit`              | Logs configuration changes to Git (e.g., new user added).                   |  
| `notify user`             | Sends emails/SMS to users (e.g., "Your account is ready").                  |  
| `task_manager`            | Coordinates tasks like retrying failed steps or updating logs.              |  

### 4. **Data Flow** 
1. A user submits details via the **Web UI** (`self_reg_app`).  
2. A `request<queuename>` message is sent to `RegUsr` with fields:  
   ```json  
   { "username", "queuename", "email", "fullname", "reason" }  

3.  The system:
    
    -   Assigns UID/GID via SQLite (`get next uid gid`  queue).
        
    -   Validates data with a  `verify<queuename>`  message.
        
    -   Sends a  `completed<queuename>`  message with success/failure status.
        
    -   Notifies the user and logs the event.
        

----------

## Setup & Usage

### Prerequisites

-   macOS
    
-   Homebrew
    
-   Python 3.x

### Install and Setup RabbitMQ

```bash
brew update
brew install rabbitmq
```

### Add RabbitMQ to Your PATH

```
echo 'export PATH="/usr/local/sbin:$PATH"' >> ~/.zshrc
source ~/.zshrc  # Reload your shell to apply changes
```

### Start RabbitMQ
```
brew services start rabbitmq
```

### Check RabbitMQ Status
```
rabbitmqctl status
```

### ccess the Management UI

-   **URL**:  [http://localhost:15672](http://localhost:15672/)
    
-   **Credentials**:
    
    -   Username:  `guest`
        
    -   Password:  `guest`


### WIP Configuration Steps

1.  **Bind Queues to  `RegUsr`  Exchange**:  
    Use these routing keys:
    
    -   `request<queuename>`
        
    -   `completed<queuename>`
        
    -   `verify<queuename>`  
        _(Replace  `<queuename>`  with your queue’s name, e.g.,  `request_user_reg`)_
        
2.  **Deploy Agents**:
    
    -   Run the Web UI (`self_reg_app`) for user submissions.
        
    -   Execute  `create_account.py`  to process tasks (e.g., UID assignment).
        
3.  **Monitor Queues**:  
    Use RabbitMQ’s management UI or CLI tools to check:
    
    -   `task_manager`  for workflow progress.
        
    -   `notify user`  for delivery status of emails/SMS.
        

----------

## Error Handling

-   Failures (e.g., duplicate email) are reported in the  `completed<queuename>`  message’s  `errmsg`  field.
    
-   The  `user reg event logger`  tracks all registration attempts. Check logs at  `/var/log/user_reg.log`.
    

----------

## Example Workflow

**Scenario**: A researcher registers via the Web UI.

1.  Web UI sends  `request_researcher_reg`  with their details.
    
2.  System assigns UID/GID from SQLite.
    
3.  A  `verify_researcher_reg`  message ensures data is valid.
    
4.  On success:
    
    -   `completed_researcher_reg`  marks  `success: True`.
        
    -   `notify_researcher_reg`  triggers a confirmation email.
        
5.  On failure:
    
    -   `errmsg`  lists issues (e.g., "Email already exists").
        

----------
