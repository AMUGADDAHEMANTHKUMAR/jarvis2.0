# import subprocess

# def run_powershell(cmd: str) -> str:
#     result = subprocess.run(
#         ["powershell", "-Command", cmd],
#         capture_output=True, text=True, timeout=10
#     )
#     return result.stdout.strip() or result.stderr.strip()

# def open_app(name: str) -> str:
#     return run_powershell(f"Start-Process '{name}'")

# def get_system_info() -> dict:
#     cpu = run_powershell("(Get-WmiObject Win32_Processor).LoadPercentage")
#     mem = run_powershell("(Get-WmiObject Win32_OperatingSystem).FreePhysicalMemory")
#     return {"cpu_pct": cpu, "free_ram_kb": mem}

import subprocess
import webbrowser

def run_powershell(cmd: str) -> str:
    try:
        result = subprocess.run(
            ["powershell", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout.strip() or result.stderr.strip()
    except Exception as e:
        return str(e)

def open_app(name: str) -> str:
    try:
        subprocess.Popen(name)
        return f"Opened {name}"
    except Exception as e:
        return str(e)

def browse(url: str) -> str:
    try:
        webbrowser.open(url)
        return f"Opened {url}"
    except Exception as e:
        return str(e)