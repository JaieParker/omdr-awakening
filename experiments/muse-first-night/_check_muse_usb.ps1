# Look for anything Muse / Interaxon / Athena via Windows PnP enumeration
Write-Host "=== PnP devices matching muse/interaxon/athena ==="
Get-PnpDevice |
    Where-Object {
        $_.FriendlyName -match 'muse|interaxon|athena|MS-?03' -or
        $_.Manufacturer -match 'muse|interaxon'
    } |
    Select-Object Status, Class, FriendlyName, Manufacturer, InstanceId |
    Format-List

Write-Host ""
Write-Host "=== All USB-class devices currently present ==="
Get-PnpDevice -Class USB -PresentOnly |
    Where-Object { $_.Status -eq 'OK' } |
    Sort-Object FriendlyName |
    Select-Object FriendlyName, Manufacturer |
    Format-Table -AutoSize

Write-Host ""
Write-Host "=== USB Hub / device tree (recently connected USB stacks) ==="
Get-PnpDevice -PresentOnly |
    Where-Object {
        $_.InstanceId -like 'USB\*' -or $_.InstanceId -like 'BTHENUM\*'
    } |
    Select-Object Class, FriendlyName, InstanceId |
    Sort-Object Class, FriendlyName |
    Format-Table -AutoSize -Wrap

Write-Host ""
Write-Host "=== Bluetooth devices currently paired/visible ==="
Get-PnpDevice -PresentOnly |
    Where-Object { $_.Class -eq 'Bluetooth' -or $_.InstanceId -like 'BTHENUM\*' } |
    Select-Object FriendlyName, Status, InstanceId |
    Format-Table -AutoSize -Wrap
