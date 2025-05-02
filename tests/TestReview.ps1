#Requires -Version 5.0
<#
.SYNOPSIS
    Interactive test review system for Data Dictionary Agency
.DESCRIPTION
    Provides an interactive interface for browsing and analyzing test results
.NOTES
    File Name      : TestReview.ps1
    Author         : Data Dictionary Agency
    Prerequisite   : PowerShell 5.0
#>

# Script configuration
$script:CONFIG = @{
    LogFolder = Join-Path -Path (Split-Path -Parent -Path $PSScriptRoot) -ChildPath "test-logs"
    ReportsFolder = Join-Path -Path (Split-Path -Parent -Path $PSScriptRoot) -ChildPath "test-reports"
}

function Start-InteractiveReview {
    <#
    .SYNOPSIS
        Starts the interactive test review interface
    .DESCRIPTION
        Provides a menu-driven interface for reviewing test results
    #>
    [CmdletBinding()]
    param()
    
    # Import TestTracker if not already loaded
    $testTrackerPath = Join-Path -Path $PSScriptRoot -ChildPath "TestTracker.ps1"
    if (!(Get-Command -Name "Get-TestResults" -ErrorAction SilentlyContinue)) {
        . $testTrackerPath
    }
    
    # Import TestReporter if not already loaded
    $testReporterPath = Join-Path -Path $PSScriptRoot -ChildPath "TestReporter.ps1"
    if (!(Get-Command -Name "Export-HtmlReport" -ErrorAction SilentlyContinue)) {
        . $testReporterPath
    }
    
    $exit = $false
    
    while (-not $exit) {
        Show-MainMenu
        $selection = Read-Host "Please make a selection"
        
        switch ($selection) {
            '1' {
                # Browse Test Suites
                Show-TestSuitesBrowser
            }
            '2' {
                # View Failing Tests
                Show-FailingTests
            }
            '3' {
                # Search Test Results
                Show-TestSearch
            }
            '4' {
                # Browse Test Logs
                Show-LogBrowser
            }
            '5' {
                # Generate Reports
                Show-ReportGenerator
            }
            '6' {
                # Compare Test Runs
                Show-TestComparison
            }
            'Q' {
                $exit = $true
            }
            'q' {
                $exit = $true
            }
            default {
                Write-Host "Invalid selection." -ForegroundColor Red
                Start-Sleep -Seconds 1
            }
        }
    }
}

function Show-MainMenu {
    <#
    .SYNOPSIS
        Displays the main menu for the test review interface
    #>
    Clear-Host
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host "         Data Dictionary Agency               " -ForegroundColor Cyan
    Write-Host "        Interactive Test Review               " -ForegroundColor Cyan
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Get current test status
    $results = Get-TestResults
    $overallStatus = $results.summary.overallStatus
    $statusColor = switch ($overallStatus) {
        "PASS" { "Green" }
        "FAIL" { "Red" }
        "IN_PROGRESS" { "Yellow" }
        default { "White" }
    }
    
    Write-Host "Current Test Status: " -NoNewline
    Write-Host $overallStatus -ForegroundColor $statusColor
    Write-Host "Total Suites: $($results.summary.totalSuites)"
    Write-Host "Completed Suites: $($results.summary.completedSuites) / $($results.summary.totalSuites)"
    Write-Host "Passing Suites: $($results.summary.passingSuites)"
    Write-Host "Failing Suites: $($results.summary.failingSuites)"
    Write-Host "Last Updated: $($results.summary.lastUpdated)"
    Write-Host ""
    Write-Host "1: Browse Test Suites"
    Write-Host "2: View Failing Tests"
    Write-Host "3: Search Test Results"
    Write-Host "4: Browse Test Logs"
    Write-Host "5: Generate Reports"
    Write-Host "6: Compare Test Runs"
    Write-Host "Q: Quit"
    Write-Host ""
}

function Show-TestSuitesBrowser {
    <#
    .SYNOPSIS
        Displays a browser for test suites
    #>
    $results = Get-TestResults
    $exit = $false
    
    while (-not $exit) {
        Clear-Host
        Write-Host "===============================================" -ForegroundColor Cyan
        Write-Host "              Test Suites Browser              " -ForegroundColor Cyan
        Write-Host "===============================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Select Test Type:"
        Write-Host "1: Python Test Suites"
        Write-Host "2: JavaScript Test Suites"
        Write-Host "B: Back to Main Menu"
        Write-Host ""
        
        $selection = Read-Host "Please make a selection"
        
        switch ($selection) {
            '1' {
                # Python Test Suites
                Show-SuitesList -Type "python" -Results $results
            }
            '2' {
                # JavaScript Test Suites
                Show-SuitesList -Type "javascript" -Results $results
            }
            'B' {
                $exit = $true
            }
            'b' {
                $exit = $true
            }
            default {
                Write-Host "Invalid selection." -ForegroundColor Red
                Start-Sleep -Seconds 1
            }
        }
    }
}

function Show-SuitesList {
    <#
    .SYNOPSIS
        Shows a list of test suites of a specific type
    .PARAMETER Type
        The type of test suites to show (python or javascript)
    .PARAMETER Results
        The test results object
    #>
    param(
        [Parameter(Mandatory=$true)]
        [ValidateSet("python", "javascript")]
        [string]$Type,
        
        [Parameter(Mandatory=$true)]
        [PSCustomObject]$Results
    )
    
    if ($Type -eq "python") {
        $suitesList = $Results.testSuites.python.PSObject.Properties
    } else {
        $suitesList = $Results.testSuites.javascript.PSObject.Properties
    }
    
    Clear-Host
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host "              $Type Test Suites                 " -ForegroundColor Cyan
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host ""
    
    if (-not $suitesList -or ($suitesList | Measure-Object).Count -eq 0) {
        Write-Host "No $Type test suites found." -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Press Enter to continue"
        return
    }
    
    $i = 1
    foreach ($property in $suitesList) {
        $suiteName = $property.Name
        $suite = $property.Value
        $statusColor = switch ($suite.status) {
            "PASS" { "Green" }
            "FAIL" { "Red" }
            "ERROR" { "Red" }
            "SKIPPED" { "Yellow" }
            default { "White" }
        }
        
        Write-Host "$i: " -NoNewline
        Write-Host "$suiteName" -NoNewline -ForegroundColor Cyan
        Write-Host " [" -NoNewline
        Write-Host "$($suite.status)" -NoNewline -ForegroundColor $statusColor
        Write-Host "] - $($suite.tests.passed)/$($suite.tests.total) tests passing"
        $i++
    }
    
    Write-Host ""
    Read-Host "Press Enter to continue"
}

function Show-FailingTests {
    <#
    .SYNOPSIS
        Shows all failing tests across all suites
    #>
    $results = Get-TestResults
    
    Clear-Host
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host "              Failing Tests                    " -ForegroundColor Cyan
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host ""
    
    $failingSuites = 0
    $failingTests = 0
    
    # Check Python suites
    foreach ($suiteName in $results.testSuites.python.PSObject.Properties.Name) {
        $suite = $results.testSuites.python.$suiteName
        
        if ($suite.status -eq "FAIL" -or $suite.status -eq "ERROR") {
            $failingSuites++
            
            Write-Host "$suiteName (python)" -ForegroundColor Red
            
            if ($suite.details) {
                foreach ($test in $suite.details) {
                    if ($test.status -eq "FAIL") {
                        $failingTests++
                        Write-Host "  - $($test.name)" -ForegroundColor Red
                    }
                }
            }
            
            Write-Host ""
        }
    }
    
    # Check JavaScript suites
    foreach ($suiteName in $results.testSuites.javascript.PSObject.Properties.Name) {
        $suite = $results.testSuites.javascript.$suiteName
        
        if ($suite.status -eq "FAIL" -or $suite.status -eq "ERROR") {
            $failingSuites++
            
            Write-Host "$suiteName (javascript)" -ForegroundColor Red
            
            if ($suite.details) {
                foreach ($test in $suite.details) {
                    if ($test.status -eq "FAIL") {
                        $failingTests++
                        Write-Host "  - $($test.name)" -ForegroundColor Red
                    }
                }
            }
            
            Write-Host ""
        }
    }
    
    if ($failingSuites -eq 0) {
        Write-Host "No failing tests found." -ForegroundColor Green
    } else {
        Write-Host "Summary: $failingSuites failing suites with $failingTests failing tests" -ForegroundColor Red
    }
    
    Write-Host ""
    Read-Host "Press Enter to return to main menu"
}

function Show-TestSearch {
    <#
    .SYNOPSIS
        Provides a search interface for test results
    #>
    Clear-Host
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host "              Test Search                      " -ForegroundColor Cyan
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "This feature allows you to search through test results."
    Write-Host "Feature to be implemented in future version."
    Write-Host ""
    Read-Host "Press Enter to return to main menu"
}

function Show-LogBrowser {
    <#
    .SYNOPSIS
        Provides a browser for test log files
    #>
    Clear-Host
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host "             Test Log Browser                  " -ForegroundColor Cyan
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host ""
    
    $logFolder = $script:CONFIG.LogFolder
    
    if (-not (Test-Path -Path $logFolder)) {
        Write-Host "Log folder not found: $logFolder" -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Press Enter to return to main menu"
        return
    }
    
    $logFiles = Get-ChildItem -Path $logFolder -Filter "*.log" | Sort-Object -Property LastWriteTime -Descending
    
    if ($logFiles.Count -eq 0) {
        Write-Host "No log files found in $logFolder" -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Press Enter to return to main menu"
        return
    }
    
    Write-Host "Found $($logFiles.Count) log files:" -ForegroundColor Green
    Write-Host ""
    
    for ($i = 0; $i -lt [Math]::Min(10, $logFiles.Count); $i++) {
        $logFile = $logFiles[$i]
        Write-Host "$($i+1): $($logFile.Name) - $($logFile.LastWriteTime)"
    }
    
    Write-Host ""
    Write-Host "Showing the 10 most recent logs" -ForegroundColor Gray
    Write-Host ""
    Read-Host "Press Enter to return to main menu"
}

function Show-ReportGenerator {
    <#
    .SYNOPSIS
        Provides an interface for generating test reports
    #>
    $results = Get-TestResults
    
    Clear-Host
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host "            Report Generator                   " -ForegroundColor Cyan
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Select Report Type:"
    Write-Host "1: JUnit XML Report (for CI)"
    Write-Host "2: HTML Dashboard"
    Write-Host "3: Both"
    Write-Host "B: Back to Main Menu"
    Write-Host ""
    
    $selection = Read-Host "Please make a selection"
    
    switch ($selection) {
        '1' {
            # Generate JUnit XML
            $reportsFolder = Join-Path -Path (Split-Path -Parent -Path $PSScriptRoot) -ChildPath "test-reports"
            $junitFolder = Join-Path -Path $reportsFolder -ChildPath "junit"
            
            if (-not (Test-Path -Path $junitFolder)) {
                New-Item -Path $junitFolder -ItemType Directory -Force | Out-Null
            }
            
            $junitPaths = Export-JUnitXmlReport -Results $results
            
            Write-Host ""
            Write-Host "JUnit XML reports generated at:" -ForegroundColor Green
            Write-Host $junitFolder
            
            Write-Host ""
            Read-Host "Press Enter to return to main menu"
        }
        '2' {
            # Generate HTML Dashboard
            $reportsFolder = Join-Path -Path (Split-Path -Parent -Path $PSScriptRoot) -ChildPath "test-reports"
            $htmlFolder = Join-Path -Path $reportsFolder -ChildPath "html"
            
            if (-not (Test-Path -Path $htmlFolder)) {
                New-Item -Path $htmlFolder -ItemType Directory -Force | Out-Null
            }
            
            $htmlPath = Export-HtmlReport -Results $results
            
            Write-Host ""
            Write-Host "HTML dashboard generated at:" -ForegroundColor Green
            Write-Host $htmlPath
            
            Write-Host ""
            Read-Host "Press Enter to return to main menu"
        }
        '3' {
            # Generate Both
            $reportsFolder = Join-Path -Path (Split-Path -Parent -Path $PSScriptRoot) -ChildPath "test-reports"
            $junitFolder = Join-Path -Path $reportsFolder -ChildPath "junit"
            $htmlFolder = Join-Path -Path $reportsFolder -ChildPath "html"
            
            if (-not (Test-Path -Path $junitFolder)) {
                New-Item -Path $junitFolder -ItemType Directory -Force | Out-Null
            }
            
            if (-not (Test-Path -Path $htmlFolder)) {
                New-Item -Path $htmlFolder -ItemType Directory -Force | Out-Null
            }
            
            $junitPaths = Export-JUnitXmlReport -Results $results
            $htmlPath = Export-HtmlReport -Results $results
            
            Write-Host ""
            Write-Host "JUnit XML reports and HTML dashboard generated at:" -ForegroundColor Green
            Write-Host "JUnit: $junitFolder"
            Write-Host "HTML: $htmlPath"
            
            Write-Host ""
            Read-Host "Press Enter to return to main menu"
        }
        'B' {
            return
        }
        'b' {
            return
        }
        default {
            Write-Host "Invalid selection." -ForegroundColor Red
            Start-Sleep -Seconds 1
            return
        }
    }
}

function Show-TestComparison {
    <#
    .SYNOPSIS
        Provides an interface for comparing test runs
    #>
    Clear-Host
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host "           Test Run Comparison                 " -ForegroundColor Cyan
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "This feature allows comparison between test runs."
    Write-Host "Feature to be implemented in future version."
    Write-Host ""
    Read-Host "Press Enter to return to main menu"
}

# Export functions if imported as a module
if ($MyInvocation.MyCommand.ScriptBlock.Module) {
    Export-ModuleMember -Function @(
        'Start-InteractiveReview'
    )
}