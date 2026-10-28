"""
Generates high-resolution terminal screenshots for the Docker Containerization Report.
Renders real command execution in a clean terminal window UI.
"""
import subprocess
import os
from PIL import Image, ImageDraw, ImageFont

font_path = '/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf'
font_bold_path = '/usr/share/fonts/truetype/ubuntu/UbuntuMono-B.ttf'

font = ImageFont.truetype(font_path, 15)
font_bold = ImageFont.truetype(font_bold_path, 15)
title_font = ImageFont.truetype(font_bold_path, 13)

CWD = '/home/venkat/Desktop/csdlab7'


def render_terminal(title, commands, output_filename, width=960, custom_outputs=None):
    content_lines = []
    
    for idx, cmd in enumerate(commands):
        content_lines.append(('prompt', f'venkat@personal-pc:~/Desktop/csdlab7$ {cmd}'))
        
        if custom_outputs and cmd in custom_outputs:
            out = custom_outputs[cmd]
        else:
            proc = subprocess.run(
                cmd,
                shell=True,
                executable='/bin/bash',
                capture_output=True,
                text=True,
                cwd=CWD
            )
            out = proc.stdout + proc.stderr
            
        for l in out.splitlines():
            # Truncate overly long lines for neat display
            if len(l) > 115:
                l = l[:112] + '...'
            content_lines.append(('text', l))
        content_lines.append(('text', ''))

    # Trim trailing blank lines
    while content_lines and content_lines[-1][1] == '':
        content_lines.pop()

    line_height = 20
    top_bar_height = 34
    padding = 14
    total_height = top_bar_height + padding * 2 + len(content_lines) * line_height

    img = Image.new('RGB', (width, total_height), color='#1e1e2e')
    draw = ImageDraw.Draw(img)

    # Title bar
    draw.rectangle([(0, 0), (width, top_bar_height)], fill='#181825')
    draw.ellipse([(14, 11), (24, 21)], fill='#f38ba8')  # Red
    draw.ellipse([(32, 11), (42, 21)], fill='#f9e2af')  # Yellow
    draw.ellipse([(50, 11), (60, 21)], fill='#a6e3a1')  # Green

    # Window Title
    title_w = draw.textlength(title, font=title_font)
    draw.text(((width - title_w) // 2, 9), title, fill='#cdd6f4', font=title_font)

    y = top_bar_height + padding
    for line_type, text in content_lines:
        if line_type == 'prompt':
            prompt_prefix = 'venkat@personal-pc:~/Desktop/csdlab7$ '
            draw.text((padding, y), prompt_prefix, fill='#a6e3a1', font=font_bold)
            prompt_len = draw.textlength(prompt_prefix, font=font_bold)
            draw.text((padding + prompt_len, y), text.split('$ ', 1)[1], fill='#89b4fa', font=font)
        else:
            color = '#cdd6f4'
            if any(k in text for k in ['SUCCESS', 'Healthy', 'healthy', 'Built', 'Created', 'Started', 'running', 'OK', 'PASSED']):
                color = '#a6e3a1'  # Green
            elif any(k in text for k in ['ERROR', 'failed', 'Error', 'Exception', '413', '500', 'invalid']):
                color = '#f38ba8'  # Red
            elif any(k in text for k in ['WARN', 'Waiting', 'Starting', 'Building', 'Step', 'PORTS', 'NAME']):
                color = '#f9e2af'  # Yellow
            elif text.startswith('=>') or text.startswith('[+]'):
                color = '#94e2d5'  # Cyan / Teal
            draw.text((padding + 8, y), text, fill=color, font=font)
        y += line_height

    img.save(os.path.join(CWD, output_filename), quality=95)
    print(f"Generated {output_filename} ({width}x{total_height})")


def main():
    print("Generating terminal screenshots for report...")

    # Screenshot 1: Docker Environment and Version Check
    render_terminal(
        "Terminal 1: Personal System Environment & Docker Daemon Verification",
        [
            "uname -s -m -r",
            "docker --version",
            "docker compose version",
            "docker info | grep -E 'Server Version|Operating System|CPUs|Total Memory'"
        ],
        "screenshot1_env_verify.png"
    )

    # Screenshot 2: Building Multi-Service Stack with Docker Compose
    render_terminal(
        "Terminal 2: Multi-Service Image Build & Optimization",
        [
            "docker compose build",
            "docker images | grep -E 'csdlab7|IMAGE'"
        ],
        "screenshot2_build_images.png"
    )

    # Screenshot 3: One-Command Startup and Health Monitoring
    render_terminal(
        "Terminal 3: Single-Command Full Stack Orchestration (docker compose up)",
        [
            "docker compose up -d",
            "docker compose ps",
            "docker network inspect proximity-net | grep -E '\"Name\"|\"IPv4Address\"'"
        ],
        "screenshot3_run_stack.png"
    )

    # Screenshot 4: End-to-End API Verification via Reverse Proxy
    render_terminal(
        "Terminal 4: Testing Reverse Proxy (:8080) & Direct API (:5000) with Linkage Data",
        [
            "curl -s http://localhost:8080/ | head -n 5",
            "curl -s -X POST http://localhost:8080/search/ -F 'lat=0.5' -F 'long=0.5' -F 'cat=bank' -F 'rad=0.15' -F 'link=@test_links.txt'",
            "curl -s -X POST http://localhost:8080/search/ -F 'lat=0.0' -F 'long=0.0' -F 'cat=store' -F 'rad=0.2' -F 'link=@link.txt'",
            "python3 test_docker.py"
        ],
        "screenshot4_api_testing.png"
    )

    # Screenshot 5: Container Logs, Volume Persistence & Teardown
    render_terminal(
        "Terminal 5: Logging, Volume Inspection & Lifecycle Teardown",
        [
            "docker compose logs --tail=5 api",
            "docker compose logs --tail=5 proxy",
            "docker volume ls | grep proximity",
            "docker compose down"
        ],
        "screenshot5_inspect_logs.png"
    )

    # Re-launch stack so it stays active
    subprocess.run("docker compose up -d", shell=True, cwd=CWD)
    print("Re-launched docker stack. All screenshots ready.")


if __name__ == "__main__":
    main()
