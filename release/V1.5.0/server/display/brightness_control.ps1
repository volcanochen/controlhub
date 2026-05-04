param(
    [Parameter(Mandatory=$true)]
    [ValidateRange(0, 100)]
    [int]$Brightness
)

$ErrorActionPreference = "SilentlyContinue"

$methodSuccess = $false

try {
    $monitors = Get-WmiObject -Namespace root/wmi -Class WmiMonitorBrightnessMethods -ErrorAction SilentlyContinue
    if ($monitors) {
        foreach ($monitor in $monitors) {
            $monitor.WmiSetBrightness(1, $Brightness)
        }
        Write-Output "OK:Brightness set to $Brightness% (WMI)"
        $methodSuccess = $true
    }
} catch {}

if (-not $methodSuccess) {
    try {
        $code = @'
using System;
using System.Runtime.InteropServices;

public class DDCMonitor {
    [DllImport("dxva2.dll", EntryPoint = "GetNumberOfPhysicalMonitorsFromHMONITOR")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetNumberOfPhysicalMonitorsFromHMONITOR(IntPtr hMonitor, ref uint pdwNumberOfPhysicalMonitors);

    [DllImport("dxva2.dll", EntryPoint = "GetPhysicalMonitorsFromHMONITOR")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetPhysicalMonitorsFromHMONITOR(IntPtr hMonitor, uint dwPhysicalMonitorArraySize, [Out] PHYSICAL_MONITOR[] pPhysicalMonitorArray);

    [DllImport("dxva2.dll", EntryPoint = "DestroyPhysicalMonitors")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool DestroyPhysicalMonitors(uint dwPhysicalMonitorArraySize, [In] PHYSICAL_MONITOR[] pPhysicalMonitorArray);

    [DllImport("dxva2.dll", EntryPoint = "SetMonitorBrightness")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool SetMonitorBrightness(IntPtr hMonitor, uint dwNewBrightness);

    [DllImport("dxva2.dll", EntryPoint = "GetMonitorBrightness")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetMonitorBrightness(IntPtr hMonitor, ref uint pdwMinimumBrightness, ref uint pdwCurrentBrightness, ref uint pdwMaximumBrightness);

    [DllImport("user32.dll")]
    private static extern bool EnumDisplayMonitors(IntPtr hdc, IntPtr lprcClip, EnumMonitorsDelegate lpfnEnum, IntPtr dwData);

    private delegate bool EnumMonitorsDelegate(IntPtr hMonitor, IntPtr hdcMonitor, ref RECT lprcMonitor, IntPtr dwData);

    [StructLayout(LayoutKind.Sequential)]
    private struct RECT { public int left; public int top; public int right; public int bottom; }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
    private struct PHYSICAL_MONITOR {
        public IntPtr hPhysicalMonitor;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 128)]
        public string szPhysicalMonitorDescription;
    }

    private static PHYSICAL_MONITOR[] physicalMonitors;
    private static uint monitorCount = 0;
    private static int targetBrightness = 0;
    private static bool success = false;

    public static bool SetBrightness(int brightness) {
        targetBrightness = brightness;
        success = false;
        monitorCount = 0;
        physicalMonitors = null;
        EnumDisplayMonitors(IntPtr.Zero, IntPtr.Zero, EnumCallback, IntPtr.Zero);
        
        if (monitorCount > 0 && physicalMonitors != null) {
            DestroyPhysicalMonitors(monitorCount, physicalMonitors);
        }
        return success;
    }
    
    private static bool EnumCallback(IntPtr hMonitor, IntPtr hdcMonitor, ref RECT lprcMonitor, IntPtr dwData) {
        uint count = 0;
        if (GetNumberOfPhysicalMonitorsFromHMONITOR(hMonitor, ref count) && count > 0) {
            monitorCount = count;
            physicalMonitors = new PHYSICAL_MONITOR[count];
            if (GetPhysicalMonitorsFromHMONITOR(hMonitor, count, physicalMonitors)) {
                for (int i = 0; i < count; i++) {
                    uint min = 0, current = 0, max = 100;
                    if (GetMonitorBrightness(physicalMonitors[i].hPhysicalMonitor, ref min, ref current, ref max)) {
                        uint newValue = (uint)(targetBrightness * max / 100);
                        if (SetMonitorBrightness(physicalMonitors[i].hPhysicalMonitor, newValue)) {
                            success = true;
                        }
                    }
                }
            }
        }
        return true;
    }
}
'@
        Add-Type -TypeDefinition $code -Language CSharp -ErrorAction SilentlyContinue
        $result = [DDCMonitor]::SetBrightness($Brightness)
        if ($result) {
            Write-Output "OK:Brightness set to $Brightness% (DDC/CI)"
            $methodSuccess = $true
        }
    } catch {}
}

if (-not $methodSuccess) {
    try {
        Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

public class MonitorBrightness {
    [DllImport("user32.dll")]
    public static extern IntPtr GetDC(IntPtr hWnd);

    [DllImport("gdi32.dll")]
    public static extern bool SetDeviceGammaRamp(IntPtr hDC, ref RAMP lpRamp);

    [DllImport("user32.dll")]
    public static extern int ReleaseDC(IntPtr hWnd, IntPtr hDC);

    [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
    public struct RAMP {
        [MarshalAs(UnmanagedType.ByValArray, SizeConst=256)]
        public UInt16[] Red;
        [MarshalAs(UnmanagedType.ByValArray, SizeConst=256)]
        public UInt16[] Green;
        [MarshalAs(UnmanagedType.ByValArray, SizeConst=256)]
        public UInt16[] Blue;
    }
    
    public static bool SetBrightness(int brightness) {
        RAMP ramp = new RAMP();
        ramp.Red = new UInt16[256];
        ramp.Green = new UInt16[256];
        ramp.Blue = new UInt16[256];
        
        double gamma = Math.Max(0.1, brightness / 100.0);
        
        for (int i = 0; i < 256; i++) {
            ushort value = (ushort)Math.Min(65535, Math.Max(0, Math.Floor(Math.Pow(i / 255.0, 1.0 / gamma) * 65535)));
            ramp.Red[i] = value;
            ramp.Green[i] = value;
            ramp.Blue[i] = value;
        }
        
        IntPtr dc = GetDC(IntPtr.Zero);
        bool result = SetDeviceGammaRamp(dc, ref ramp);
        ReleaseDC(IntPtr.Zero, dc);
        return result;
    }
}
"@

        $result = [MonitorBrightness]::SetBrightness($Brightness)
        if ($result) {
            Write-Output "OK:Brightness set to $Brightness% (Gamma)"
            $methodSuccess = $true
        }
    } catch {}
}

if (-not $methodSuccess) {
    Write-Output "ERROR:Failed to set brightness"
    exit 1
}
