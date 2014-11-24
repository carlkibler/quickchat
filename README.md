quickchat
=========

A redis-backed chat tool, to play with basic client-server architecture

# Install
1. Check out from github

2. Install packages into virtualenv
  ```
  mkvirtual quickchat
  pip install -r requirements.txt
  ````
3. Configure Redis instance
Edit file server/config.py to insert your redis host and password

# Run server
  ```python server/server.py```

# Connect to server
From an unlimited number of clients, telnet in to port 9399 (or whatever is configured in server/config.py).
```telnet 127.0.0.1 9399```

Exit out of the client by type _/quit_ or pressing control-]

The server does not correctly expire usernames or rooms out of the redis backend (yet). To prevent becoming cluttered over time with obsolete data, *each time it is started it will flush the redis DB*. 

To prevent this flush-on-startup, add the parameter *-noclear* to the command line.




