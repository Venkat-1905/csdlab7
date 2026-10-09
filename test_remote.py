"""Test the remote API directly from within the remote server."""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.1.75.51", port=2236, username="student",
            password="venkat19@", timeout=15)

# Create a small test link file on the remote
print("Creating test link file on remote...")
_, stdout, stderr = ssh.exec_command("""
python3 -c "
import random
random.seed(42)
links = []
for i in range(100):
    for j in range(100):
        nid = i * 100 + j + 1
        if j + 1 < 100 and random.random() < 0.85:
            links.append(f'{nid} {i * 100 + j + 2}')
        if i + 1 < 100 and random.random() < 0.85:
            links.append(f'{nid} {(i + 1) * 100 + j + 1}')
with open('/home/student/csdlab7/test_links.txt', 'w') as f:
    f.write(chr(10).join(links))
print(f'Generated {len(links)} links')
"
""")
print(stdout.read().decode())
print(stderr.read().decode())

# Test API from within the remote server
print("Testing API from remote...")
_, stdout, stderr = ssh.exec_command(
    'curl -s -X POST http://127.0.0.1:3000/search/ '
    '-F "lat=0.5" -F "long=0.5" -F "cat=bank" -F "rad=0.15" '
    '-F "link=@/home/student/csdlab7/test_links.txt"'
)
out = stdout.read().decode()
err = stderr.read().decode()
print(f"Response: {out}")
if err:
    print(f"Error: {err}")

# Check server log for any errors
print("\nServer log:")
_, stdout, _ = ssh.exec_command("cat /home/student/csdlab7/server.log | tail -20")
print(stdout.read().decode())

ssh.close()

