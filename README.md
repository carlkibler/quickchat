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

# Run server
  ```make run```
  or
  ```python server/server.py```

The server does not correctly expire usernames or rooms out of the redis backend (yet). To prevent becoming cluttered over time with obsolete data, *each time it is started it will flush the redis DB*. 

To prevent this flush-on-startup, add the parameter *-noclear* to the command line.




