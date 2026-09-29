# Run server in background and wait for it to be ready
cd C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main

$env:JWT_SECRET="test-secret-key-for-dev-only-32-bytes-minimum-length"
$env:MASTER_ENCRYPTION_KEY="MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="
$env:PII_PEPPER="test-pepper-32-bytes-long-secret"
$env:AUDIT_HMAC_KEY="dGVzdC1hdWRpdC1obWFjLWtleS10aXJ0eS1ieXRlcw=="
$env:ALLOWED_ORIGINS="http://localhost:8081,http://127.0.0.1:8081"
$env:GROQ_API_KEY="dummy"
$env:GOVT_API_KEY="dummy"

# Start server in background
$serverProcess = Start-Process -NoNewWindow "C:\Users\dishi\AppData\Local\Programs\Python\Python311\python.exe" -ArgumentList "-m uvicorn backend:app --port 8000 --host 127.0.0.1 --timeout-keep-alive 30 --log-level info" -PassThru

Write-Host "Server started with PID: $($serverProcess.Id)"
Write-Host "Waiting for server to be ready..."

# Wait for server to be ready by polling /chat endpoint
$maxAttempts = 60
$attempt = 0
$serverReady = $false

while ($attempt -lt $maxAttempts -and -not $serverReady) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/chat" -Method POST -Body '{"message":"test"}' -ContentType "application/json" -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 401 -or $response.StatusCode -eq 200) {
            $serverReady = $true
            Write-Host "Server is ready! Status: $($response.StatusCode)"
        }
    } catch {
        # Check if it's a 401 which means server is up
        if ($_.Exception.Response.StatusCode -eq 401) {
            $serverReady = $true
            Write-Host "Server is ready! Status: 401 (Unauthorized - correct)"
        }
    }
    
    if (-not $serverReady) {
        Start-Sleep -Seconds 2
        $attempt++
        Write-Host "Attempt $attempt/$maxAttempts - waiting for server..."
    }
}

if (-not $serverReady) {
    Write-Host "Server failed to start in time"
    Stop-Process -Id $serverProcess.Id -Force
    exit 1
}

Write-Host "Running security tests..."
$testResult = & C:\Users\dishi\AppData\Local\Programs\Python\Python311\python.exe C:\Users\dishi\Downloads\Asha_Vaani-main\Asha_Vaani-main\test_security.py

# Cleanup
Stop-Process -Id $serverProcess.Id -Force