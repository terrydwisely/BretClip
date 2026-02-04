Add-Type -AssemblyName System.Windows.Forms
$screens = [System.Windows.Forms.Screen]::AllScreens
Write-Host "Found $($screens.Count) screen(s):"
foreach ($screen in $screens) {
    Write-Host "  $($screen.DeviceName): $($screen.Bounds)"
    Write-Host "    Primary: $($screen.Primary)"
    Write-Host "    Working Area: $($screen.WorkingArea)"
}
