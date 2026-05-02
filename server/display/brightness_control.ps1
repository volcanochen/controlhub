param(
    [Parameter(Mandatory=$true)]
    [ValidateRange(0, 100)]
    [int]$Brightness
)

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
}
"@

$ramp = New-Object MonitorBrightness+RAMP
$ramp.Red = New-Object UInt16[] 256
$ramp.Green = New-Object UInt16[] 256
$ramp.Blue = New-Object UInt16[] 256

$gamma = [Math]::Max(0.1, $Brightness / 100.0)

for ($i = 0; $i -lt 256; $i++) {
    $value = [Math]::Min(65535, [Math]::Max(0, [Math]::Floor([Math]::Pow($i / 255.0, 1.0 / $gamma) * 65535)))
    $ramp.Red[$i] = $value
    $ramp.Green[$i] = $value
    $ramp.Blue[$i] = $value
}

$dc = [MonitorBrightness]::GetDC([IntPtr]::Zero)
$result = [MonitorBrightness]::SetDeviceGammaRamp($dc, [ref]$ramp)
[MonitorBrightness]::ReleaseDC([IntPtr]::Zero, $dc)

if ($result) {
    Write-Output "OK:Brightness set to $Brightness%"
} else {
    Write-Output "ERROR:Failed to set brightness"
}
