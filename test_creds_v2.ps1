$vmIp = "192.168.110.131"
$users = @("admin", "raj_ops", "atlas", "rangeradmin", "holger_gov", "ambari_admin")
$passwords = @("admin", "admin123", "hadoop", "raj_ops", "atlas", "rangeradmin", "holger_gov", "password", "ensias2025")

$ambariUrl = "http://$vmIp:8080/api/v1/clusters"
$rangerUrl = "http://$vmIp:6080/service/public/v2/api/service/definitions"

function Test-Auth($url, $u, $p, $service) {
    $pair = "$($u):$($p)"
    $bytes = [System.Text.Encoding]::ASCII.GetBytes($pair)
    $base64 = [System.Convert]::ToBase64String($bytes)
    $headers = @{ "Authorization" = "Basic $base64" }
    
    try {
        $resp = Invoke-WebRequest -Uri $url -Headers $headers -Method Get -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($resp.StatusCode -eq 200) {
            Write-Host "SUCCESS: $service works with $u : $p"
            return $true
        } else {
             # Write-Host "$service : $u : $p -> $($resp.StatusCode)"
        }
    } catch {
        # Catch connection errors
    }
    return $false
}

Write-Host "--- Testing Apache Ambari ---"
foreach ($u in $users) {
    foreach ($p in $passwords) {
        if (Test-Auth $ambariUrl $u $p "Ambari") { break }
    }
}

Write-Host "`n--- Testing Apache Ranger ---"
foreach ($u in $users) {
    foreach ($p in $passwords) {
        if (Test-Auth $rangerUrl $u $p "Ranger") { break }
    }
}
