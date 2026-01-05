# Kill process on port 8000
$conn = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($conn) {
    $pid = $conn.OwningProcess
    Write-Output "Killing process $pid on port 8000"
    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Start server
Set-Location C:\Users\ayrto\indexer-api
Start-Process -FilePath python -ArgumentList "-m","uvicorn","indexer_api.main:app","--host","0.0.0.0","--port","8000" -NoNewWindow
