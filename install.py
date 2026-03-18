import os
import sys
import subprocess
import platform

# --- 🛡️ 6372-Hybrid-AI-Sentinel: Universal Installer ---
# Author: myikgetzweb3

def run_cmd(cmd):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + cmd.split() + ["--break-system-packages"])
    except:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + cmd.split())
        except Exception as e:
            print(f"Error installing {cmd}: {e}")

def main():
    print("\033[96m\033[1m")
    print(" █████╗ ███████╗ ██████╗ ██╗███████╗")
    print("██╔══██╗██╔════╝██╔════╝ ██║██╔════╝")
    print("███████║█████╗  ██║  ███╗██║███████╗")
    print("██╔══██║██╔══╝  ██║   ██║██║╚════██║")
    print("██║  ██║███████╗╚██████╔╝██║███████║")
    print("╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝╚══════╝")
    print("      UNIVERSAL INSTALLER v2.0")
    print("\033[0m")

    # 1. Install Dependencies
    print("📦 Installing Python dependencies...")
    run_cmd("requests python-dotenv psutil plyer feedparser websocket-client google-generativeai")

    # 2. Setup Directories
    print("📂 Setting up directories...")
    os.makedirs("data", exist_ok=True)
    os.makedirs("config/locales", exist_ok=True)

    # 3. Handle Aliases (Linux/Mac)
    if platform.system().lower() != "windows":
        print("🔗 Setting up shell aliases...")
        home = os.path.expanduser("~")
        proj_dir = os.getcwd()
        for rc in [".bashrc", ".zshrc"]:
            rc_path = os.path.join(home, rc)
            if os.path.exists(rc_path):
                # Clean old aliases if they exist to avoid duplicates
                with open(rc_path, "r") as f: lines = f.readlines()
                with open(rc_path, "w") as f:
                    for line in lines:
                        if "alias 6372-" not in line and "alias crypto-" not in line:
                            f.write(line)
                    f.write(f"\nalias 6372-status='python3 {proj_dir}/src/ui/dashboard.py'\n")
                    f.write(f"alias 6372-monitor='python3 {proj_dir}/src/main.py'\n")
                    f.write(f"alias 6372-config='python3 {proj_dir}/src/ui/wizard.py'\n")
                    f.write(f"alias crypto-status='6372-status'\n")
                    f.write(f"alias crypto-monitor='6372-monitor'\n")
                    f.write(f"alias crypto-config='6372-config'\n")
        print("✅ Aliases added. Please run 'source ~/.bashrc' or restart terminal.")
    else:
        print("💻 Windows detected. Please run the tools directly using:")
        print("   python src/ui/dashboard.py")

    print("\n\033[92m✨ 6372-Hybrid-AI-Sentinel installation complete!\033[0m")

if __name__ == "__main__":
    main()
