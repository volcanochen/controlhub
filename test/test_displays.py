import subprocess
import time

def get_display_info():
    """Get detailed display information using PowerShell"""
    ps_cmd = r"""
Add-Type -AssemblyName System.Windows.Forms
$screens = [System.Windows.Forms.Screen]::AllScreens
Write-Host "COUNT:$($screens.Count)"
foreach ($screen in $screens) {
    Write-Host "DEVICE:$($screen.DeviceName)"
    Write-Host "BOUNDS:$($screen.Bounds.X),$($screen.Bounds.Y)"
    Write-Host "PRIMARY:$($screen.Primary)"
    Write-Host "---"
}
"""
    result = subprocess.run(['powershell', '-Command', ps_cmd], 
                          capture_output=True, text=True, timeout=5)
    print("PowerShell Output:")
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    return result.stdout

print("=== Current Display Info ===")
get_display_info()

print("\n=== Switching to external only ===")
subprocess.run('DisplaySwitch.exe /external', shell=True)
time.sleep(6)

print("\n=== Display Info after switch ===")
get_display_info()

print("\n=== Switching back to internal only ===")
subprocess.run('DisplaySwitch.exe /internal', shell=True)
time.sleep(6)

print("\n=== Display Info after switch back ===")
get_display_info()
