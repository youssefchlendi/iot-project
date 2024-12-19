# Define paths
$backendPath = "object-detection-app/";
$frontendPath = "object-detection-app/frontend"
$detectionPath = "detection"

# Step 1: Run Backend Server
Write-Host "Setting up and starting the backend server..." -ForegroundColor Green
Set-Location $backendPath

Start-Process -FilePath "node" -ArgumentList "server.js"
Start-Sleep -Seconds 3

# Step 2: Run Frontend App
Write-Host "Setting up and starting the frontend app..." -ForegroundColor Green
Set-Location "..\$frontendPath"

Start-Process -FilePath "npm" -ArgumentList "run dev"
Start-Sleep -Seconds 3

# Step 3: Run MQTT Subscriber
Write-Host "Starting MQTT Subscriber..." -ForegroundColor Green
Set-Location "..\..\$detectionPath"
Start-Process -FilePath "python" -ArgumentList "mqtt_subscriber.py"

# # Step 4: Run Command Subscriber
# Write-Host "Starting Command Subscriber..." -ForegroundColor Green
# Start-Process -FilePath "python" -ArgumentList "command_subscriber.py"

# Step 5: Start YOLO Detection
Write-Host "Starting YOLO Real-Time Detection..." -ForegroundColor Green
Start-Process -FilePath "python" -ArgumentList "yolo_home_security.py"

Write-Host "All components are running. Press Ctrl+C to stop them."
