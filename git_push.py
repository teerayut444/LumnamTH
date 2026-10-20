import os
import sys
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

# ตั้งค่าให้ Terminal รองรับ UTF-8 (ป้องกันปัญหา Emoji หรือภาษาไทย error ใน Windows)
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

def wait_exit(code=0):
    if sys.stdin and sys.stdin.isatty():
        try:
            input("\nกด Enter เพื่อปิด...")
        except Exception:
            pass
    sys.exit(code)

# หา Path ของ git.exe อัตโนมัติ (รองรับแม้ไม่ได้ตั้งค่า PATH ใน Windows)
def find_git():
    git_cmd = shutil.which("git")
    if git_cmd:
        return git_cmd

    candidate_paths = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Git\cmd\git.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Git\bin\git.exe"),
        os.path.expandvars(r"%ProgramFiles%\Git\cmd\git.exe"),
        os.path.expandvars(r"%ProgramFiles%\Git\bin\git.exe"),
    ]
    for p in candidate_paths:
        if os.path.exists(p):
            return p
    return None

def run_git(git_path, args, cwd):
    cmd = [git_path] + args
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, encoding="utf-8", errors="replace")
    return result

def main():
    workspace = Path(__file__).parent.resolve()
    print("=" * 50)
    print("🚀 สคริปต์ Git Push อัตโนมัติ (LumnamTH)")
    print("=" * 50)

    # 1. ค้นหา Git
    git_path = find_git()
    if not git_path:
        print("❌ ไม่พบ Git ในเครื่อง กรุณาติดตั้ง Git หรือตรวจสอบ Path")
        wait_exit(1)

    print(f"✅ ใช้ Git จาก: {git_path}")

    # 2. ซิงค์ Lumnam-monitor.html ไปยัง index.html หากมีการแก้ไข
    src_file = workspace / "Lumnam-monitor.html"
    dst_file = workspace / "index.html"
    if src_file.exists():
        if not dst_file.exists() or src_file.stat().st_mtime > dst_file.stat().st_mtime:
            print("🔄 ตรวจพบการอัปเดต Lumnam-monitor.html -> กำลังคัดลอกไปยัง index.html...")
            shutil.copy2(src_file, dst_file)
            print("✅ ซิงค์ index.html เรียบร้อย")

    # 3. ตรวจสอบสถานะการเปลี่ยนแปลง
    status = run_git(git_path, ["status", "--porcelain"], cwd=workspace)
    if not status.stdout.strip():
        print("ℹ️ ไม่มีไฟล์ที่มีการแก้ไขหรือเปลี่ยนแปลง ไม่จำเป็นต้อง Push ครับ")
        wait_exit(0)

    print("\n📂 รายการไฟล์ที่มีการเปลี่ยนแปลง:")
    for line in status.stdout.strip().splitlines():
        print(f"   {line}")
    print()

    # 4. รับข้อความ Commit
    commit_msg = ""
    if len(sys.argv) > 1:
        commit_msg = " ".join(sys.argv[1:]).strip()
    else:
        try:
            user_input = input("💬 ใส่ข้อความ Commit (กด Enter เพื่อใช้วันที่เวลาปัจจุบัน): ").strip()
            if user_input:
                commit_msg = user_input
        except EOFError:
            pass

    if not commit_msg:
        commit_msg = f"Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    print(f"📝 Commit message: \"{commit_msg}\"")

    # 5. git add .
    print("\n⏳ กำลังเพิ่มไฟล์ (git add .)...")
    add_res = run_git(git_path, ["add", "."], cwd=workspace)
    if add_res.returncode != 0:
        print(f"❌ เกิดข้อผิดพลาดในการ git add:\n{add_res.stderr}")
        wait_exit(1)

    # 6. git commit
    print("⏳ กำลังบันทึกการเปลี่ยนแปลง (git commit)...")
    commit_res = run_git(git_path, ["commit", "-m", commit_msg], cwd=workspace)
    if commit_res.returncode != 0:
        # อาจเกิดกรณีไม่มีการเปลี่ยนแปลงหลัง add
        if "nothing to commit" in commit_res.stdout or "nothing to commit" in commit_res.stderr:
            print("ℹ️ ไม่มีอะไรต้อง commit เพิ่มเติม")
        else:
            print(f"❌ เกิดข้อผิดพลาดในการ commit:\n{commit_res.stderr or commit_res.stdout}")
            wait_exit(1)
    else:
        print("✅ Commit สำเร็จ!")

    # 7. git push
    print("⏳ กำลังส่งข้อมูลขึ้น GitHub (git push origin main)...")
    # รันแบบแสดงผล realtime
    push_process = subprocess.run([git_path, "push", "origin", "main"], cwd=workspace)
    if push_process.returncode == 0:
        print("\n🎉 ===========================================")
        print("✅ Deploy ขึ้น GitHub สำเร็จเรียบร้อยแล้ว!")
        print("🌐 เว็บไซต์: https://teerayut444.github.io/LumnamTH/")
        print("===========================================")
    else:
        print("\n❌ Git Push ไม่สำเร็จ กรุณาตรวจสอบการเชื่อมต่ออินเทอร์เน็ตหรือสิทธิ์ GitHub")

    wait_exit(0 if push_process.returncode == 0 else 1)

if __name__ == "__main__":
    main()
