# github_transfer.ps1

# --- 1. Navigate to Project Root ---
# The script assumes it lives in the 'scripts' folder, so this moves up one level.
#Set-Location .. 

# --- 2. Define Repository URL ---
$RepositoryUrl = "https://github.com/arussell1271/lifebuddy-app"

# --- 3. Check and Initialize Git Repository (If needed) ---
if (-not (Test-Path -Path ".git" -PathType Container)) {
    Write-Host "--- Initializing new Git repository ---"
    git init
    
    # Set the remote origin only if 'git init' was just run
    git remote add origin $RepositoryUrl

    # IMPORTANT: Ensure your identity is set for the first commit
    # Git requires a username and email to make commits
    # You will need to customize these lines before the first run on a new machine
    # git config user.email "your.email@example.com"
    # git config user.name "Your Name"
}

# --- 4. Define Dynamic Commit Message ---
$MachineName = $env:COMPUTERNAME
$CommitDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$CommitMessage = "Updated from $($MachineName) on the $($CommitDate)"

# --- 5. Stage, Commit, and Push Changes ---
Write-Host "--- Staging and committing changes ---"
git add .
git commit -m $CommitMessage

# Check if the commit succeeded before pushing
if ($LASTEXITCODE -eq 0) {
    # Check if this is the initial commit (first time the branch is created)
    # The default branch may be 'master', so we rename it to 'main' for GitHub compatibility
    git branch -M main

    Write-Host "--- Pulling remote changes before pushing ---"
    # PULL any remote changes first to prevent 'rejected' error
    git pull origin main
    
    Write-Host "--- Pushing changes to GitHub ---"
    git push -u origin main
}
else {
    Write-Host "No changes detected. Nothing to commit or push." -ForegroundColor Yellow
}
# --- END OF SCRIPT ---