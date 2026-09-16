param(
    [string]$Account = "",
    [string]$Contract = "contracts/AgentTrust.py",
    [string]$Owner = "",
    [ValidateSet("studionet", "testnet-bradbury")]
    [string]$Network = "testnet-bradbury",
    [string]$Rpc = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Account)) {
    Write-Error "Provide the GenLayer CLI account name: -Account <name>"
}

if ([string]::IsNullOrWhiteSpace($Owner)) {
    $accountOutput = genlayer account list | Out-String
    $line = $accountOutput -split "`r?`n" | Where-Object { $_ -match "(^|\s)$([regex]::Escape($Account))(\s|$)" } | Select-Object -First 1
    if (-not $line) {
        Write-Error "Account '$Account' was not found. Import or create it with 'genlayer account import', then retry."
    }
    $Owner = ([regex]::Match($line, "0x[0-9a-fA-F]{40}")).Value
}

if ([string]::IsNullOrWhiteSpace($Rpc)) {
    $Rpc = if ($Network -eq "studionet") {
        "https://studio.genlayer.com/api"
    } else {
        "https://rpc-bradbury.genlayer.com"
    }
}

Write-Host "Network: $Network"
Write-Host "RPC: $Rpc"
Write-Host "Account: $Account"
Write-Host "Contract: $Contract"
Write-Host "Deploying contract with the official GenLayer CLI..."

genlayer network set $Network
genlayer account use $Account
$deployArgs = @("--contract", $Contract, "--rpc", $Rpc)
& genlayer deploy @deployArgs
if ($LASTEXITCODE -ne 0) {
    throw "GenLayer CLI deployment failed with exit code $LASTEXITCODE"
}
