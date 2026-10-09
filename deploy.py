"""
Deploy the Flask application to the remote server via SSH.
Uses paramiko for SSH connection (no sshpass needed).
"""
import paramiko
import os
import sys
import time

# Remote server config
SSH_HOST = "10.1.75.51"
SSH_PORT = 2236
SSH_USER = "student"
SSH_PASS = "venkat19@"

# Local files to copy
LOCAL_DIR = os.path.dirname(os.path.abspath(__file__))
FILES_TO_COPY = ["app.py", "locations.csv"]

# Remote deployment directory
REMOTE_DIR = "/home/student/csdlab7"


def ssh_exec(ssh, cmd, print_output=True):
    """Execute a command over SSH and return output."""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    if print_output:
        if out:
            print(f"  [OUT] {out}")
        if err:
            print(f"  [ERR] {err}")
    return out, err


def find_available_port(ssh, start=3000, end=7000):
    """Find the first available port in the range."""
    # Check which ports are in use
    out, _ = ssh_exec(ssh,
        f"ss -tlnp 2>/dev/null | grep -oP ':{start}\\d*' || "
        f"netstat -tlnp 2>/dev/null | grep -oP ':{start}\\d*' || echo ''",
        print_output=False)

    # Get all ports in use
    out_full, _ = ssh_exec(ssh,
        "ss -tlnp 2>/dev/null | awk '{print $4}' | grep -oP '\\d+$' || "
        "netstat -tlnp 2>/dev/null | awk '{print $4}' | grep -oP '\\d+$' || echo ''",
        print_output=False)

    used_ports = set()
    for line in out_full.split("\n"):
        line = line.strip()
        if line.isdigit():
            used_ports.add(int(line))

    print(f"  Ports currently in use (in range): "
          f"{sorted(p for p in used_ports if start <= p <= end)}")

    for port in range(start, end + 1, 1000):
        if port not in used_ports:
            return port
    # Try every port
    for port in range(start, end + 1):
        if port not in used_ports:
            return port
    return None


def main():
    print("=" * 60)
    print("Deploying Flask API to remote server")
    print("=" * 60)

    # Connect
    print(f"\n[1] Connecting to {SSH_HOST}:{SSH_PORT}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SSH_HOST, port=SSH_PORT, username=SSH_USER,
                password=SSH_PASS, timeout=15)
    print("  Connected!")

    # Check Python and Flask
    print("\n[2] Checking remote environment...")
    ssh_exec(ssh, "python3 --version")
    ssh_exec(ssh, "python3 -c 'import flask; print(\"Flask available\")'")

    # Install flask if not available
    out, err = ssh_exec(ssh,
        "python3 -c 'import flask' 2>&1 || "
        "pip3 install flask --user --break-system-packages 2>&1 || "
        "pip3 install flask --user 2>&1",
        print_output=True)

    # Create remote directory
    print(f"\n[3] Creating remote directory {REMOTE_DIR}...")
    ssh_exec(ssh, f"mkdir -p {REMOTE_DIR}")

    # Copy files via SFTP
    print("\n[4] Copying files...")
    sftp = ssh.open_sftp()
    for fname in FILES_TO_COPY:
        local_path = os.path.join(LOCAL_DIR, fname)
        remote_path = f"{REMOTE_DIR}/{fname}"
        print(f"  Copying {fname}...")
        sftp.put(local_path, remote_path)
    sftp.close()
    print("  All files copied!")

    # Find available port
    print("\n[5] Finding available port (3000-7000)...")
    port = find_available_port(ssh)
    if port is None:
        print("  ERROR: No available ports found!")
        ssh.close()
        sys.exit(1)
    local_port = port + 251
    print(f"  Found available port: {port}")
    print(f"  Accessible locally at: http://127.0.0.1:{local_port}/search/")

    # Kill any existing instances
    print("\n[6] Stopping any existing instances...")
    ssh_exec(ssh, f"pkill -f 'python3.*app.py' 2>/dev/null || true")
    time.sleep(1)

    # Update the port in app.py remotely
    print(f"\n[7] Configuring app to use port {port}...")
    ssh_exec(ssh,
        f"sed -i 's/port=5000/port={port}/g' {REMOTE_DIR}/app.py")

    # Start the app with nohup
    print(f"\n[8] Starting Flask app on port {port}...")
    ssh_exec(ssh,
        f"cd {REMOTE_DIR} && "
        f"nohup python3 app.py > server.log 2>&1 &")
    time.sleep(2)

    # Verify it's running
    print("\n[9] Verifying deployment...")
    out, _ = ssh_exec(ssh, f"ss -tlnp 2>/dev/null | grep {port} || "
                           f"netstat -tlnp 2>/dev/null | grep {port}")
    out2, _ = ssh_exec(ssh, "ps aux | grep 'python3.*app.py' | grep -v grep")
    out3, _ = ssh_exec(ssh, f"cat {REMOTE_DIR}/server.log 2>/dev/null")

    ssh.close()

    print("\n" + "=" * 60)
    print("DEPLOYMENT COMPLETE!")
    print("=" * 60)
    print(f"  Remote port:  {port}")
    print(f"  Local access: http://127.0.0.1:{local_port}/search/")
    print(f"  Example test:")
    print(f"    curl -X POST http://127.0.0.1:{local_port}/search/ \\")
    print(f"      -F 'lat=0.5' -F 'long=0.5' -F 'cat=bank' \\")
    print(f"      -F 'rad=0.15' -F 'link=@test_links.txt'")
    print("=" * 60)


if __name__ == "__main__":
    main()

