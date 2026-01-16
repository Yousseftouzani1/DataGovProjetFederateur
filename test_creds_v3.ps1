$vmIp = "192.168.110.131"
$users = @("admin", "raj_ops", "atlas", "rangeradmin", "holger_gov", "ambari_admin")
$passwords = @("admin", "admin123", "hadoop", "raj_ops", "atlas", "rangeradmin", "holger_gov", "password", "ensias2025")

$ambariUrl = "http://$vmIp:8080/api/v1/clusters"
$rangerUrl = "http://$vmIp:6080/service/public/v2/api/service/definitions"

function Test-Auth-Curl($url, $u, $p, $service) {
    # Using curl.exe directly
    $output = & curl.exe -s -o /dev/null -w "%{http_code}" -u "$u:$p" --connect-timeout 3 $url
    if ($output -eq "200") {
        Write-Host "SUCCESS: $service works with $u : $p"
        return $true
    }
    return $false
}

Write-Host "--- Testing Apache Ambari (Port 8080) ---"
$foundAmbari = $false
foreach ($u in $users) {
    foreach ($p in $passwords) {
        if (Test-Auth-Curl $ambariUrl $u $p "Ambari") { $foundAmbari = $true; break }
    }
    if ($foundAmbari) { break }
}
if (-not $foundAmbari) { Write-Host "No common credentials worked for Ambari." }

Write-Host "`n--- Testing Apache Ranger (Port 6080) ---"
$foundRanger = $false
foreach ($u in $users) {
    foreach ($p in $passwords) {
        if (Test-Auth-Curl $rangerUrl $u $p "Ranger") { $foundRanger = $true; break }
    }
    if ($foundRanger) { break }
}
if (-not $foundRanger) { Write-Host "No common credentials worked for Ranger." }
