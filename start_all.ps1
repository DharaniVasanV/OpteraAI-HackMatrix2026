# PowerShell Script to Start AgentOS and its 14 modular Agents
# Run this script to boot the entire ecosystem.

$AgentBasePath = "E:\AgentOS"
$CentralEnv = "$AgentBasePath\.env"
$Py = "$AgentBasePath\.venv\Scripts\python.exe"

if (-not (Test-Path -Path $CentralEnv)) {
    Write-Host "❌ Error: Cannot find central .env at $CentralEnv" -ForegroundColor Red
    Write-Host "Please ensure the .env file exists with all necessary configurations."
    exit 1
}

Write-Host "🧹 Stopping any previously running agent processes..." -ForegroundColor Yellow
$Ports = 8001..8013 + 9000
foreach ($port in $Ports) {
    try {
        $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        foreach ($conn in $conns) {
            $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
            if ($proc) {
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                Write-Host "  Stopped existing process $($proc.Id) on port $port" -ForegroundColor Gray
            }
        }
    } catch {}
}

Start-Sleep -Seconds 1

Write-Host "`n🚀 Booting AgentOS Ecosystem..." -ForegroundColor Cyan

# Define the list of agents with their directories and start commands
$Agents = @(
    @{ Name = "Watcher Agent";       Dir = ".";                              Cmd = "$Py -m uvicorn app.main:app --host 127.0.0.1 --port 8001" },
    @{ Name = "Research Agent";      Dir = "research_agent";                 Cmd = "$Py -m uvicorn app.main:app --host 127.0.0.1 --port 8002" },
    @{ Name = "Enrichment Agent";    Dir = "Enrichment_Agent\enrichment-agent"; Cmd = "$Py -m uvicorn app.main:app --host 127.0.0.1 --port 8003" },
    @{ Name = "Knowledge Ingestion"; Dir = "knowledge_agent\ingestion";       Cmd = "$Py -m uvicorn app.main:app --host 127.0.0.1 --port 8004" },
    @{ Name = "Knowledge Retrieval"; Dir = "knowledge_agent\retrieval";       Cmd = "$Py -m uvicorn app.main:app --host 127.0.0.1 --port 8005" },
    @{ Name = "Meeting Agent";       Dir = "meeting-agent";                  Cmd = "$Py -m uvicorn app.main:app --host 127.0.0.1 --port 8006" },
    @{ Name = "Filler Agent";        Dir = "Filler_Agent";                   Cmd = "$Py -m uvicorn app:app --host 127.0.0.1 --port 8007" },
    @{ Name = "Career Agent";        Dir = "career_agent";                   Cmd = "$Py -m uvicorn app.main:app --host 127.0.0.1 --port 8008" },
    @{ Name = "Learning Agent";      Dir = "learning_agent";                 Cmd = "$Py -m uvicorn app.main:app --host 127.0.0.1 --port 8009" },
    @{ Name = "Resume Extractor";   Dir = "Resume_Extractor";               Cmd = "$Py -m uvicorn src.resume_extractor.main:app --host 127.0.0.1 --port 8010" },
    @{ Name = "Calendar Agent";      Dir = "calender_agent\calendar_agent";  Cmd = "`$env:DATABASE_URL='postgresql+psycopg://postgres:vasan5707@localhost:5432/meeting_agent_new'; $Py -m uvicorn app.main:app --host 127.0.0.1 --port 8011" },
    @{ Name = "Notification Agent";  Dir = "notification_agent";            Cmd = "$Py -m uvicorn app.main:app --host 127.0.0.1 --port 8012" },
    @{ Name = "Analytics Agent";     Dir = "analytics_agent";                Cmd = "$Py -m uvicorn analytics_agent.app.main:app --host 127.0.0.1 --port 8013" },
    @{ Name = "AgentOS UI";          Dir = "ui";                             Cmd = "$Py -m uvicorn app:app --host 127.0.0.1 --port 9000 --reload" }
)

foreach ($Agent in $Agents) {
    $TargetDir = "$AgentBasePath\$($Agent.Dir)"
    if (-not (Test-Path $TargetDir)) {
        Write-Host "⚠️ Warning: Directory for $($Agent.Name) not found at $($Agent.Dir). Skipping..." -ForegroundColor Yellow
        continue
    }

    Write-Host "✅ Starting $($Agent.Name)..." -ForegroundColor Green
    
    $AgentCmd = $Agent.Cmd
    $CmdStr = "cd '$TargetDir'; `$env:PYTHONPATH='$TargetDir;$AgentBasePath'; $AgentCmd"
    Start-Process powershell -ArgumentList "-WindowStyle", "Minimized", "-NoExit", "-Command", $CmdStr
    
    Start-Sleep -Milliseconds 600
}

Write-Host "`n🎉 All Agents have been launched!" -ForegroundColor Cyan
Write-Host "👉 AgentOS Control Center (UI): http://localhost:9000" -ForegroundColor White
Write-Host "👉 Watcher Agent (Integration Root): http://localhost:8001" -ForegroundColor White
Write-Host "Use the dashboard to monitor system health and process emails."
