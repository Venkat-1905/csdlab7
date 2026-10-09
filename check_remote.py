"""Check remote server log for errors."""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.1.75.51", port=2236, username="student",
            password="venkat19@", timeout=15)

_, stdout, _ = ssh.exec_command("cat /home/student/csdlab7/server.log 2>/dev/null")
print(stdout.read().decode())

print("---")
_, stdout, _ = ssh.exec_command("ls -la /home/student/csdlab7/")
print(stdout.read().decode())

print("---")
_, stdout, _ = ssh.exec_command("cat /home/student/csdlab7/app.py | head -10")
print(stdout.read().decode())

print("---PORT in app.py---")
_, stdout, _ = ssh.exec_command("grep 'port=' /home/student/csdlab7/app.py")
print(stdout.read().decode())

ssh.close()

