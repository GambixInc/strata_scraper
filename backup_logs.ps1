# Docker Logs Backup Script (PowerShell Version)
# Copies today's logs from running containers to a backup location

# Configuration
$BackupDir = "./logs/backup"
$Date = Get-Date -Format "yyyy-MM-dd"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ContainerName = "strata-scraper"

Write-Host "📋 Docker Logs Backup Script" -ForegroundColor Green
Write-Host "Date: $Date" -ForegroundColor Yellow
Write-Host "Timestamp: $Timestamp" -ForegroundColor Yellow
Write-Host ""

# Create backup directory if it doesn't exist
if (!(Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
}

# Check if container is running
$ContainerRunning = docker ps --format "table {{.Names}}" | Select-String "^$ContainerName$"
if (!$ContainerRunning) {
    Write-Host "❌ Container '$ContainerName' is not running" -ForegroundColor Red
    Write-Host "💡 Start the container first: docker-compose up -d" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Container '$ContainerName' is running" -ForegroundColor Green

# Create today's backup directory
$TodayBackupDir = "$BackupDir/$Date"
if (!(Test-Path $TodayBackupDir)) {
    New-Item -ItemType Directory -Path $TodayBackupDir -Force | Out-Null
}

Write-Host "📁 Creating backup directory: $TodayBackupDir" -ForegroundColor Cyan

# Function to backup logs with different time ranges
function Backup-Logs {
    param(
        [string]$TimeRange,
        [string]$Filename,
        [string]$Description
    )
    
    Write-Host "📄 Backing up $Description..." -ForegroundColor Yellow
    
    $LogFile = "$TodayBackupDir/$Filename"
    $Result = docker logs --since $TimeRange $ContainerName 2>&1 | Out-File -FilePath $LogFile -Encoding UTF8
    
    if (Test-Path $LogFile) {
        $LineCount = (Get-Content $LogFile | Measure-Object -Line).Lines
        Write-Host "   ✅ $Filename ($LineCount lines)" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Failed to backup $Filename" -ForegroundColor Red
    }
}

# Backup different time ranges
Backup-Logs -TimeRange "24h" -Filename "logs_24h_$Timestamp.txt" -Description "last 24 hours"
Backup-Logs -TimeRange "1h" -Filename "logs_1h_$Timestamp.txt" -Description "last 1 hour"
Backup-Logs -TimeRange "1d" -Filename "logs_today_$Timestamp.txt" -Description "today's logs"

# Also backup all logs (since container start)
Write-Host "📄 Backing up all logs since container start..." -ForegroundColor Yellow
$AllLogsFile = "$TodayBackupDir/logs_all_$Timestamp.txt"
$Result = docker logs $ContainerName 2>&1 | Out-File -FilePath $AllLogsFile -Encoding UTF8

if (Test-Path $AllLogsFile) {
    $LineCount = (Get-Content $AllLogsFile | Measure-Object -Line).Lines
    Write-Host "   ✅ logs_all_$Timestamp.txt ($LineCount lines)" -ForegroundColor Green
} else {
    Write-Host "   ❌ Failed to backup all logs" -ForegroundColor Red
}

# Create a summary file
$SummaryFile = "$TodayBackupDir/backup_summary_$Timestamp.txt"
$SummaryContent = @"
Docker Logs Backup Summary
=========================
Date: $Date
Timestamp: $Timestamp
Container: $ContainerName
Backup Directory: $TodayBackupDir

Files Created:
$((Get-ChildItem "$TodayBackupDir/*.txt" | ForEach-Object { "$($_.Name) ($($_.Length) bytes)" }) -join "`n")

Container Status:
$(docker ps --filter "name=$ContainerName" --format "table {{.Names}}	{{.Status}}	{{.Ports}}")

System Info:
$(systeminfo | Select-String "OS Name|OS Version")
$(docker --version)
"@

$SummaryContent | Out-File -FilePath $SummaryFile -Encoding UTF8

Write-Host ""
Write-Host "📊 Backup Summary:" -ForegroundColor Cyan
Write-Host "   📁 Backup location: $TodayBackupDir" -ForegroundColor Yellow
Write-Host "   📄 Files created:" -ForegroundColor Yellow
Get-ChildItem "$TodayBackupDir/*.txt" | ForEach-Object {
    Write-Host "      $($_.Name) ($($_.Length) bytes)" -ForegroundColor White
}
Write-Host "   📋 Summary file: backup_summary_$Timestamp.txt" -ForegroundColor Yellow

Write-Host ""
Write-Host "✅ Log backup completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "🔍 To view the logs:" -ForegroundColor Cyan
Write-Host "   Get-Content $TodayBackupDir/logs_24h_$Timestamp.txt" -ForegroundColor White
Write-Host "   Get-Content $TodayBackupDir/logs_1h_$Timestamp.txt" -ForegroundColor White
