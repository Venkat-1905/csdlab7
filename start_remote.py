"""Quick script to check and start the app on the remote server."""
import paramiko
import time

SSH_HOST = "10.1.75.51"
SSH_PORT = 2236
SSH_USER = "student"
SSH_PASS = "venkat19@"
REMOTE_DIR = "/home/student/csdlab7"
APP_PORT = 3000

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SSH_HOST, port=SSH_PORT, username=SSH_USER,
            password=SSH_PASS, timeout=15)

def run(cmd):
    _, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print(f"  {out}")
    if err: print(f"  [err] {err}")
    return out

# Check if already running
print("Checking if app is running...")
run(f"ss -tlnp | grep {APP_PORT}")
run("ps aux | grep 'python3.*app.py' | grep -v grep")

# Check server log
print("\nServer log:")
run(f"cat {REMOTE_DIR}/server.log 2>/dev/null | tail -10")

# If not running, start it
print(f"\nStarting app on port {APP_PORT}...")
# Use bash -c with disown to properly background it
transport = ssh.get_transport()
channel = transport.open_session()
channel.exec_command(
    f"cd {REMOTE_DIR} && "
    f"nohup python3 app.py > server.log 2>&1 & disown"
)
time.sleep(3)

# Verify
print("\nVerifying...")
run(f"ss -tlnp | grep {APP_PORT}")
run("ps aux | grep 'python3.*app.py' | grep -v grep")
print("\nServer log after start:")
run(f"cat {REMOTE_DIR}/server.log 2>/dev/null | tail -10")

ssh.close()
print(f"\nAccess locally at: http://127.0.0.1:{APP_PORT + 251}/search/")

