# Optional: removes duplicate backend/frontend from parent c:\NLP after copying into ME2026.
# The app already lives under ME2026\backend and ME2026\frontend — only run this to delete old copies.
# Run:  powershell -ExecutionPolicy Bypass -File .\organize-nlp-app.ps1

$ErrorActionPreference = "Stop"
$Me2026 = $PSScriptRoot
$NlpRoot = Split-Path $Me2026 -Parent

$folders = @("backend", "frontend")
foreach ($name in $folders) {
    $src = Join-Path $NlpRoot $name
    $dst = Join-Path $Me2026 $name
    if (-not (Test-Path $src)) {
        Write-Warning "Skip (not found): $src"
        continue
    }
    if (Test-Path $dst) {
        Write-Host "Already in ME2026: $name"
        continue
    }
    Write-Host "Moving $name -> ME2026\$name"
    Move-Item -Path $src -Destination $dst
}

$readmeSrc = Join-Path $NlpRoot "README.md"
$readmeDst = Join-Path $Me2026 "SENTIMENT_APP.md"
if ((Test-Path $readmeSrc) -and -not (Test-Path $readmeDst)) {
    Copy-Item $readmeSrc $readmeDst
    Write-Host "Copied README.md -> ME2026\SENTIMENT_APP.md"
}

Write-Host ""
Write-Host "Done. Next steps:"
Write-Host "  cd $Me2026"
Write-Host "  git status"
Write-Host "  git add backend frontend SENTIMENT_APP.md .gitignore"
Write-Host "  git commit -m ""Add NLP sentiment dashboard and API"""
Write-Host "  git push origin master"
