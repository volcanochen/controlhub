$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms

# Get all screens
$screens = [System.Windows.Forms.Screen]::AllScreens

# Count active screens
$count = $screens.Count
Write-Host "ACTIVE_COUNT:$count"

# Get primary screen info
$primary = $screens | Where-Object { $_.Primary }
$primary_exists = ($primary -ne $null)
Write-Host "PRIMARY_EXISTS:$primary_exists"

# Get detailed info for each screen and extract display IDs
$display_ids = @()
for ($i = 0; $i -lt $count; $i++) {
    $screen = $screens[$i]
    Write-Host "SCREEN_$i`: Bounds=$($screen.Bounds.Width)x$($screen.Bounds.Height), Primary=$($screen.Primary), DeviceName=$($screen.DeviceName)"
    
    # Extract display ID from DeviceName (e.g., "\\.\DISPLAY1" -> 1)
    if ($screen.DeviceName -match 'DISPLAY(\d+)') {
        $id = [int]$matches[1]
        $display_ids += $id
        Write-Host "DISPLAY_ID:$id, Primary=$($screen.Primary)"
    }
}

# Output primary device name if exists
if ($primary_exists) {
    Write-Host "PRIMARY_DEVICE:$($primary.DeviceName)"
}

# Output all display IDs for analysis
Write-Host "ALL_IDS:$($display_ids -join ',')"
