"""Interactive local-model setup: checks specs, then offers to install/start Ollama
and download a model. Everything is optional - the app falls back to cloud.

    python setup_local.py          # interactive
    python setup_local.py --check  # report only, no prompts
"""
import platform
import shutil
import subprocess
import sys

import config
import system_check as sc

def ask(q: str, default: bool = True) -> bool:
    hint = "[Y/n]" if default else "[y/N]"
    try:
        a = input(f"\n{q} {hint} ").strip().lower()
    except EOFError:
        return False
    return default if not a else a.startswith("y")


def print_specs(specs: dict, rec: dict) -> None:
    print("=== System ===")
    print(f"  OS        {specs['os']}")
    print(f"  CPU       {specs['cpu']} ({specs['cpu_cores']} cores)")
    print(f"  RAM       {specs['ram_gb']} GB total, {specs['ram_free_gb']} GB free")
    print(f"  Disk free {specs['disk_free_gb']} GB")
    print(f"  GPU       {', '.join(specs['gpus']) or 'none detected'}")
    if specs["battery_pct"] is not None:
        print(f"  Battery   {specs['battery_pct']}% {'(on battery)' if specs['on_battery'] else '(plugged in)'}")
    print(f"\n  Recommended local model: {rec['model'] or 'none'} - {rec['why']}")


def install_ollama() -> None:
    if platform.system() == "Windows" and shutil.which("winget"):
        if ask("Install Ollama with winget now?"):
            subprocess.run(["winget", "install", "-e", "--id", "Ollama.Ollama",
                            "--accept-source-agreements"])
            print("\nDone. Close this terminal, open a new one, and re-run: python setup_local.py")
            return
    print("\nInstall Ollama manually:")
    for step in sc.install_instructions():
        print(f"  - {step}")
    print("Then re-run: python setup_local.py")


def troubleshoot() -> None:
    print("""
Ollama didn't respond on {url}. Try, in order:
  1. Quit Ollama from the system tray (right-click the llama icon -> Quit),
     then in a terminal run:  ollama serve   and leave it open.
  2. If it says the address is in use, something else holds port 11434:
       netstat -ano | findstr 11434      (then end that PID in Task Manager)
  3. Check the log:  %LOCALAPPDATA%\\Ollama\\server.log
  4. Still stuck? Skip it - the app routes everything to the cloud automatically.""".format(url=config.OLLAMA_URL))


def main() -> None:
    check_only = "--check" in sys.argv
    specs = sc.system_specs()
    rec = sc.recommend_model(specs)
    print_specs(specs, rec)

    status = sc.ollama_status()
    print(f"\n=== Ollama ===\n  {status['message']}")
    if status["models"]:
        print(f"  Installed models: {', '.join(status['models'])}")
    if status["model_ready"] or check_only:
        return

    if rec["model"] is None:
        print("\nThis machine is below the local-model minimum. The app will use the cloud. Nothing to do.")
        return

    if rec["model"] != config.LOCAL_MODEL and ask(
            f"Use recommended model {rec['model']} instead of {config.LOCAL_MODEL}?"):
        sc.set_env("LOCAL_MODEL", rec["model"])
        config.LOCAL_MODEL = rec["model"]

    if not status["installed"]:
        if ask("No local model runtime found. Install Ollama (~1 GB) to run models on this device?"):
            install_ollama()
        else:
            print("\nOK - skipping. All requests will route to the cloud.")
        return

    if not status["running"]:
        if not ask("Ollama is installed but not running. Start it now?"):
            return
        print("Starting 'ollama serve' in the background...")
        if not sc.start_ollama(status["binary"]):
            troubleshoot()
            return

    if not sc.ollama_status()["model_ready"]:
        if not ask(f"Download {config.LOCAL_MODEL} (~{rec['size_gb']} GB)?"):
            return
        binary = status["binary"] or "ollama"
        if subprocess.run([binary, "pull", config.LOCAL_MODEL]).returncode != 0:
            print("Download failed - check your connection and re-run.")
            return

    print(f"\nAll set: {config.LOCAL_MODEL} is ready for local inference.")


if __name__ == "__main__":
    main()
