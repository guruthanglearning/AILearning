# Schedule Log Cleanup Task
#
# This script creates a scheduled task to run the clean_workspace.py script
# to clean up old log files on a regular basis.
#
# Run this script with administrator privileges

# Define the project root and script paths
$projectRoot = "D:\Study\AILearning\MLProjects\creditcardfrauddetection"
$cleanScriptPath = Join-Path $projectRoot "scripts\utility\clean_workspace.py"
$pythonExe = "python"

# Create the action to run the script
$action = New-ScheduledTaskAction -Execute $pythonExe -Argument "$cleanScriptPath --mode logs --days 30 --backup"

# Create a trigger to run the task weekly on Sunday at 1:00 AM
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 1am

# Set the settings for the task
$settings = New-ScheduledTaskSettingsSet -RunOnlyIfNetworkAvailable -WakeToRun -StartWhenAvailable

# Register the task
$taskName = "CreditCardFraudDetection_LogCleanup"
$description = "Weekly cleanup of old log files for the Credit Card Fraud Detection project"

# Check if the task already exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "Task '$taskName' already exists. Removing existing task..."
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

try {
    Register-ScheduledTask -Action $action -Trigger $trigger -Settings $settings `
        -TaskName $taskName -Description $description `
        -User "SYSTEM" -RunLevel Highest

    Write-Host "Task '$taskName' created successfully."
    Write-Host "The log cleanup script will run every Sunday at 1:00 AM."
} catch {
    Write-Host "Error creating scheduled task: $_" -ForegroundColor Red
    Write-Host "Please make sure you're running this script with administrator privileges."
}

# Display information about the created task
Get-ScheduledTask -TaskName $taskName | Format-List
