"""
SBI 서버 실행: 사용 가능한 포트를 찾아 서버를 띄우고, 브라우저를 엽니다.
localhost가 안 될 때 127.0.0.1 로 열립니다.
"""
import os
import sys
import socket
import subprocess
import time
import webbrowser

def is_port_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)
    for port in [8000, 8001, 8050, 8051, 8080]:
        if is_port_free(port):
            break
    else:
        print("[오류] 8000, 8001, 8050, 8051, 8080 포트가 모두 사용 중입니다.")
        sys.exit(1)
    os.environ["PORT"] = str(port)
    url = f"http://127.0.0.1:{port}/"
    print(f"\n[SBI] 서버 주소: {url}")
    print("      브라우저가 곧 열립니다. (종료: Ctrl+C)\n")
    proc = subprocess.Popen(
        [sys.executable, "main.py"],
        env=os.environ,
        cwd=base_dir,
    )
    time.sleep(2.5)
    try:
        webbrowser.open(url)
    except Exception:
        print(f"브라우저를 수동으로 열어주세요: {url}")
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    main()
