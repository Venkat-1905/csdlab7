"""Check remote server log for 500 error details."""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.1.75.51", port=2236, username="student",
            password="venkat19@", timeout=15)

# Kill existing and restart with debug to see errors
print("Killing existing app...")
_, stdout, _ = ssh.exec_command("pkill -f 'python3.*app.py' 2>/dev/null; sleep 1; echo done")
print(stdout.read().decode())

# Update app.py to enable debug mode temporarily
print("Enabling debug mode for error details...")
_, stdout, _ = ssh.exec_command(
    "sed -i 's/debug=False/debug=True/' /home/student/csdlab7/app.py"
)
print(stdout.read().decode())

# Restart
print("Restarting app...")
transport = ssh.get_transport()
channel = transport.open_session()
channel.exec_command(
    "cd /home/student/csdlab7 && "
    "nohup python3 app.py > server.log 2>&1 & disown"
)

import time
time.sleep(3)

# Check it's running
_, stdout, _ = ssh.exec_command("ss -tlnp | grep 3000")
print(stdout.read().decode())

_, stdout, _ = ssh.exec_command("cat /home/student/csdlab7/server.log | tail -10")
print(stdout.read().decode())

ssh.close()
print("Done - now test from local with port-forwarded URL")

