#Requires -Version 5.0
<#
.SYNOPSIS
    CI/CD integration utilities for Data Dictionary Agency
.DESCRIPTION
    Provides functionality for integrating test execution with CI/CD pipelines
.NOTES
    File Name      : CIIntegration.ps1
    Author         : Data Dictionary Agency
    Prerequisite   : PowerShell 5.0
#>

# Script configuration
$script:CONFIG = @{
    ExitCode = 0
    StatusFileName = "ci-status.json"
}

function Initialize-CIEnvironment {
    <#
    .SYNOPSIS
        Initializes the CI/CD environment
    .DESCRIPTION
        Sets up the necessary environment for CI/CD integration
    .OUTPUTS
        PSCustomObject with environment information
    #>
    [CmdletBinding()]
    param()
    
    # Create standard CI/CD environment
    Write-Host "Initializing CI environment" -ForegroundColor Cyan
    
    # Set environment variables if not already set
    if (-not $env:CI_BUILD_ID) {
        $env:CI_BUILD_ID = "local-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    }
    
    if (-not $env:CI_JOB_NAME) {
        $env:CI_JOB_NAME = "local-test-job"
    }
    
    # Create directories if they don't exist
    $reportsDir = Join-Path -Path (Split-Path -Parent -Path $PSScriptRoot) -ChildPath "test-reports"
    $junitDir = Join-Path -Path $reportsDir -ChildPath "junit"
    $htmlDir = Join-Path -Path $reportsDir -ChildPath "html"
    
    if (-not (Test-Path -Path $reportsDir)) {
        New-Item -Path $reportsDir -ItemType Directory -Force | Out-Null
    }
    
    if (-not (Test-Path -Path $junitDir)) {
        New-Item -Path $junitDir -ItemType Directory -Force | Out-Null
    }
    
    if (-not (Test-Path -Path $htmlDir)) {
        New-Item -Path $htmlDir -ItemType Directory -Force | Out-Null
    }
    
    # Return environment info
    return [PSCustomObject]@{
        BuildId = $env:CI_BUILD_ID
        JobName = $env:CI_JOB_NAME
        ReportsDirectory = $reportsDir
        JUnitDirectory = $junitDir
        HtmlDirectory = $htmlDir
        StartTime = Get-Date
    }
}

function Complete-CIExecution {
    <#
    .SYNOPSIS
        Completes the CI/CD execution
    .DESCRIPTION
        Sets the appropriate exit code and generates final status information
    .PARAMETER Results
        The test results object
    .OUTPUTS
        PSCustomObject with execution status information
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [PSCustomObject]$Results
    )
    
    # Determine overall status
    $overallStatus = $Results.summary.overallStatus
    
    # Set exit code
    $exitCode = switch ($overallStatus) {
        "PASS" { 0 }
        "FAIL" { 1 }
        "ERROR" { 2 }
        "IN_PROGRESS" { 3 }
        default { 99 }
    }
    
    # Save the exit code for the script
    $script:CONFIG.ExitCode = $exitCode
    
    # Generate status JSON
    $status = [PSCustomObject]@{
        BuildId = $env:CI_BUILD_ID
        JobName = $env:CI_JOB_NAME
        Status = $overallStatus
        ExitCode = $exitCode
        TotalSuites = $Results.summary.totalSuites
        PassingSuites = $Results.summary.passingSuites
        FailingSuites = $Results.summary.failingSuites
        CompletedSuites = $Results.summary.completedSuites
        CompletionTime = Get-Date
    }
    
    # Save status to file
    $statusJson = ConvertTo-Json -InputObject $status -Depth 10
    $statusFile = Join-Path -Path (Split-Path -Parent -Path $PSScriptRoot) -ChildPath $script:CONFIG.StatusFileName
    $statusJson | Set-Content -Path $statusFile -Encoding UTF8
    
    # Output status
    Write-Host ""
    Write-Host "CI Execution Completed" -ForegroundColor Cyan
    Write-Host "Status: $overallStatus" -ForegroundColor $(if ($overallStatus -eq "PASS") { "Green" } else { "Red" })
    Write-Host "Exit Code: $exitCode" -ForegroundColor $(if ($exitCode -eq 0) { "Green" } else { "Red" })
    Write-Host "Status file: $statusFile" -ForegroundColor Gray
    
    return $status
}

# Export functions if imported as a module
if ($MyInvocation.MyCommand.ScriptBlock.Module) {
    Export-ModuleMember -Function @(
        'Initialize-CIEnvironment',
        'Complete-CIExecution'
    )
}