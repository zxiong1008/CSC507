[CmdletBinding()]
param(
    [switch]$Shell,
    [switch]$Inventory,
    [int]$LocalPort = 2224
)

$ErrorActionPreference = 'Stop'
$namespace = 'unix-lab'
$vmName = 'ubuntu-lab'
$sshKey = Join-Path $HOME '.ssh\k8s-debian-mini'
$virtctl = Join-Path $env:LOCALAPPDATA 'Programs\virtctl\virtctl.exe'

$minikubeCommand = Get-Command minikube -ErrorAction SilentlyContinue
if (-not $minikubeCommand) {
    $minikubePath = Join-Path $env:LOCALAPPDATA 'Programs\Minikube\minikube.exe'
    if (Test-Path $minikubePath) {
        $minikubeCommand = Get-Command $minikubePath -ErrorAction Stop
    } else {
        throw 'Minikube was not found. Install it or add its folder to PATH.'
    }
}
$kubectlCommand = Get-Command kubectl -ErrorAction Stop
$sshCommand = Get-Command ssh -ErrorAction Stop

if (-not (Test-Path $virtctl)) { throw "virtctl was not found at $virtctl" }
if (-not (Test-Path $sshKey)) { throw "SSH private key was not found at $sshKey" }

function Test-LocalTcpPort {
    param([int]$Port)
    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $connection = $client.ConnectAsync('127.0.0.1', $Port)
        return $connection.Wait(500) -and $client.Connected
    } catch {
        return $false
    } finally {
        $client.Dispose()
    }
}

function Test-SshReady {
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $sshCommand.Source -i $sshKey -p $LocalPort -o BatchMode=yes `
            -o ConnectTimeout=2 -o StrictHostKeyChecking=accept-new `
            'student@127.0.0.1' 'true' 2>$null
        return $LASTEXITCODE -eq 0
    } finally {
        $ErrorActionPreference = $previousPreference
    }
}

$previousPreference = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
$minikubeStatus = & $minikubeCommand.Source status --format='{{.Host}}' 2>$null
$minikubeStatusExitCode = $LASTEXITCODE
$ErrorActionPreference = $previousPreference
Write-Host "[DEBUG] Minikube status: '$("$minikubeStatus".Trim())' (exit code $minikubeStatusExitCode)."
$vmNeedsStartupDelay = $false

if ($minikubeStatusExitCode -eq 0 -and "$minikubeStatus".Trim() -eq 'Running') {
    Write-Host 'Minikube is already running; leaving the cluster undisturbed.'
} else {
    Write-Host 'Starting Minikube...'
    & $minikubeCommand.Source start
    if ($LASTEXITCODE -ne 0) { throw 'Minikube failed to start.' }
    $vmNeedsStartupDelay = $true
}

Write-Host "Waiting for VM $vmName to become ready..."
$vmPhase = & $kubectlCommand.Source -n $namespace get "vmi/$vmName" -o 'jsonpath={.status.phase}' 2>$null
$getVmiExitCode = $LASTEXITCODE
Write-Host "[DEBUG] VMI phase: '$("$vmPhase".Trim())' (kubectl exit code $getVmiExitCode)."
if ($getVmiExitCode -eq 0 -and "$vmPhase".Trim() -eq 'Running') {
    Write-Host "VM $vmName is already running; skipping the startup wait."
} else {
    Write-Host "VM $vmName is not running yet; waiting for it to become Ready..."
    & $kubectlCommand.Source -n $namespace wait --for=condition=Ready "vmi/$vmName" --timeout=300s
    Write-Host "[DEBUG] Kubernetes readiness wait exit code: $LASTEXITCODE."
    if ($LASTEXITCODE -ne 0) { throw 'The Ubuntu VM did not become ready in time.' }
    $vmNeedsStartupDelay = $true
}

if ($vmNeedsStartupDelay) {
    Write-Host 'The Kubernetes VM has just become ready; waiting 5 minutes before starting the Linux connection...'
    Write-Host "[DEBUG] Ten-minute delay started at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')."
    Start-Sleep -Seconds 600
    Write-Host "[DEBUG] Ten-minute delay completed at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')."
}

$portForwardProcess = $null
$sshReady = Test-SshReady
Write-Host "[DEBUG] SSH available before port forwarding: $sshReady."
if (-not $sshReady) {
    $expectedCommand = "port-forward vm/$vmName ${LocalPort}:22 -n $namespace"
    $staleForwards = Get-CimInstance Win32_Process | Where-Object {
        $_.Name -ieq 'virtctl.exe' -and $_.CommandLine -and $_.CommandLine.Contains($expectedCommand)
    }
    foreach ($staleForward in $staleForwards) {
        Stop-Process -Id $staleForward.ProcessId -Force -ErrorAction SilentlyContinue
    }
    for ($attempt = 0; $attempt -lt 10 -and (Test-LocalTcpPort -Port $LocalPort); $attempt++) {
        Start-Sleep -Milliseconds 250
    }
    if (Test-LocalTcpPort -Port $LocalPort) {
        throw "Port $LocalPort is open but SSH is not responding. Close the other process using that port and retry."
    }

    $sshReady = $false
    for ($forwardAttempt = 1; $forwardAttempt -le 2 -and -not $sshReady; $forwardAttempt++) {
        if ($portForwardProcess -and -not $portForwardProcess.HasExited) {
            Stop-Process -Id $portForwardProcess.Id -Force -ErrorAction SilentlyContinue
            $portForwardProcess.WaitForExit()
        }

        for ($attempt = 0; $attempt -lt 10 -and (Test-LocalTcpPort -Port $LocalPort); $attempt++) {
            Start-Sleep -Milliseconds 250
        }
        if (Test-LocalTcpPort -Port $LocalPort) {
            throw "Port $LocalPort is still occupied; close the other process using it and retry."
        }

        Write-Host "Opening the SSH port forward in a separate PowerShell window on localhost:$LocalPort (attempt $forwardAttempt of 2)..."
        $portForwardProcess = Start-Process -FilePath $virtctl `
            -ArgumentList @('port-forward', "vm/$vmName", "${LocalPort}:22", '-n', $namespace) `
            -PassThru
        Write-Host "[DEBUG] Started virtctl port-forward process with PID $($portForwardProcess.Id)."

        for ($attempt = 0; $attempt -lt 60; $attempt++) {
            if (Test-SshReady) {
                $sshReady = $true
                Write-Host "[DEBUG] SSH became available after $($attempt + 1) readiness check(s)."
                break
            }
            if ($portForwardProcess.HasExited) {
                Write-Host "[DEBUG] Port-forward process exited with code $($portForwardProcess.ExitCode)."
                break
            }
            Start-Sleep -Milliseconds 500
        }

        if (-not $sshReady) {
            if ($portForwardProcess -and -not $portForwardProcess.HasExited) {
                Stop-Process -Id $portForwardProcess.Id -Force -ErrorAction SilentlyContinue
                $portForwardProcess.WaitForExit()
            }
            if ($forwardAttempt -lt 2) {
                Write-Host 'SSH is not reachable yet; restarting the port forward and retrying once...'
            }
        }
    }

    if (-not $sshReady) {
        throw "SSH did not become ready through the port forward on port $LocalPort."
    }
}

try {
    if (-not $Inventory -or $Shell) {
        Write-Host 'Opening an interactive Ubuntu shell. Type exit to return.'
        & $sshCommand.Source -i $sshKey -p $LocalPort 'student@127.0.0.1'
    } else {
        Write-Host 'Running the Linux inventory commands...'
        $remoteCommands = @'
printf '\n===== Processor =====\n'; lscpu
printf '\n===== Main memory =====\n'; free -h
printf '\n===== Detailed memory =====\n'; head -n 12 /proc/meminfo
printf '\n===== PCI devices =====\n'; lspci -nnk
printf '\n===== USB devices =====\n'; lsusb
printf '\n===== USB device tree =====\n'; lsusb -t
printf '\n===== Network interfaces =====\n'; ip -br link
printf '\n===== Block devices =====\n'; lsblk -o NAME,MODEL,SIZE,TYPE,FSTYPE,MOUNTPOINTS
printf '\n===== Filesystems =====\n'; df -hT
'@
    $remoteCommands = $remoteCommands -replace "`r", ''
        & $sshCommand.Source -i $sshKey -p $LocalPort 'student@127.0.0.1' $remoteCommands
    }
    if ($LASTEXITCODE -ne 0) { throw 'SSH or a remote Linux command failed.' }
} finally {
    if ($portForwardProcess -and -not $portForwardProcess.HasExited) {
        Stop-Process -Id $portForwardProcess.Id -Force
    }
}
