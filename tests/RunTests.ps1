#Requires -Version 5.0
<#
.SYNOPSIS
    Test execution utility for Data Dictionary Agency
.DESCRIPTION
    Provides functionality for running and managing Python and JavaScript tests
.PARAMETER List
    List all available test suites
.PARAMETER Suite
    Name of the test suite to run
.PARAMETER Type
    Type of test suite (python or javascript)
.PARAMETER Parallel
    Run tests in parallel
.PARAMETER MaxJobs
    Maximum number of parallel jobs (default: 5)
.PARAMETER Detail
    Show detailed test results
.PARAMETER Summary
    Show test results summary
.PARAMETER Interactive
    Run in interactive mode
.PARAMETER CI
    Run in CI mode
.PARAMETER Partition
    Partition number for CI mode
.PARAMETER TotalPartitions
    Total number of partitions for CI mode
.PARAMETER ExportJUnit
    Export test results to JUnit XML format
.PARAMETER ExportHtml
    Export test results to HTML format
.PARAMETER Review
    Start interactive test review
.EXAMPLE
    ./RunTests.ps1 -List
    Lists all available test suites.
.EXAMPLE
    ./RunTests.ps1 -Suite test_avro_parser -Type python
    Runs the Python test suite 'test_avro_parser'.
.EXAMPLE
    ./RunTests.ps1 -Parallel -MaxJobs 10
    Runs all tests in parallel with a maximum of 10 concurrent jobs.
.NOTES
    File Name      : RunTests.ps1
    Author         : Data Dictionary Agency
    Prerequisite   : PowerShell 5.0
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [switch]$List,
    
    [Parameter(Mandatory=$false)]
    [string]$Suite,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("python", "javascript")]
    [string]$Type,
    
    [Parameter(Mandatory=$false)]
    [switch]$Parallel,
    
    [Parameter(Mandatory=$false)]
    [int]$MaxJobs = 10,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("Component", "Format", "LoadBalanced")]
    [string]$PartitionStrategy = "LoadBalanced",
    
    [Parameter(Mandatory=$false)]
    [switch]$Detail,
    
    [Parameter(Mandatory=$false)]
    [switch]$Summary,
    
    [Parameter(Mandatory=$false)]
    [switch]$Interactive,
    
    [Parameter(Mandatory=$false)]
    [switch]$CI,
    
    [Parameter(Mandatory=$false)]
    [int]$Partition = 0,
    
    [Parameter(Mandatory=$false)]
    [int]$TotalPartitions = 1,
    
    [Parameter(Mandatory=$false)]
    [switch]$ExportJUnit,
    
    [Parameter(Mandatory=$false)]
    [switch]$ExportHtml,
    
    [Parameter(Mandatory=$false)]
    [switch]$Review
)

# Import required modules
$testTrackerPath = Join-Path -Path $PSScriptRoot -ChildPath "TestTracker.ps1"
$testReporterPath = Join-Path -Path $PSScriptRoot -ChildPath "TestReporter.ps1"
$ciIntegrationPath = Join-Path -Path $PSScriptRoot -ChildPath "CIIntegration.ps1"
$testReviewPath = Join-Path -Path $PSScriptRoot -ChildPath "TestReview.ps1"

# Source the modules
. $testTrackerPath
. $testReporterPath
. $ciIntegrationPath
. $testReviewPath

# Script configuration
$script:CONFIG = @{
    ResultsFile = Join-Path -Path (Split-Path -Parent -Path $PSScriptRoot) -ChildPath "test-results.json"
    LogFolder = Join-Path -Path (Split-Path -Parent -Path $PSScriptRoot) -ChildPath "test-logs"
    ReportsFolder = Join-Path -Path (Split-Path -Parent -Path $PSScriptRoot) -ChildPath "test-reports"
    ExitCode = 0
}

# Show welcome message
function Show-WelcomeMessage {
    Clear-Host
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host "         Data Dictionary Agency               " -ForegroundColor Cyan
    Write-Host "         Test Execution System                " -ForegroundColor Cyan
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host ""
}

# Run in interactive mode
function Start-InteractiveMode {
    $exit = $false
    
    while (-not $exit) {
        Show-WelcomeMessage
        
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
        Write-Host "$overallStatus" -ForegroundColor $statusColor
        Write-Host "Total Suites: $($results.summary.totalSuites)"
        Write-Host "Completed Suites: $($results.summary.completedSuites) / $($results.summary.totalSuites)"
        Write-Host "Passing Suites: $($results.summary.passingSuites)"
        Write-Host "Failing Suites: $($results.summary.failingSuites)"
        Write-Host ""
        
        Write-Host "Select an option:"
        Write-Host "1: List all test suites"
        Write-Host "2: Run a Python test suite"
        Write-Host "3: Run a JavaScript test suite"
        Write-Host "4: Show test results summary"
        Write-Host "5: Show detailed test results"
        Write-Host "6: Run all tests in parallel"
        Write-Host "7: Export test reports"
        Write-Host "8: Run interactive test review"
        Write-Host "9: Quit"
        Write-Host ""
        
        $selection = Read-Host "Please make a selection"
        
        switch ($selection) {
            '1' {
                # List all test suites
                Clear-Host
                Write-Host "===============================================" -ForegroundColor Cyan
                Write-Host "             Available Test Suites             " -ForegroundColor Cyan
                Write-Host "===============================================" -ForegroundColor Cyan
                Write-Host ""
                
                Write-Host "Python Test Suites:" -ForegroundColor Green
                $pythonSuites = Get-PythonTestSuites
                
                foreach ($suite in $pythonSuites) {
                    Write-Host "  $($suite.Name) ($($suite.Path))"
                }
                
                Write-Host ""
                Write-Host "JavaScript Test Suites:" -ForegroundColor Green
                $jsSuites = Get-JavaScriptTestSuites
                
                foreach ($suite in $jsSuites) {
                    Write-Host "  $($suite.Name) ($($suite.Path))"
                }
                
                Write-Host ""
                Read-Host "Press Enter to continue"
            }
            '2' {
                # Run a Python test suite
                Clear-Host
                Write-Host "===============================================" -ForegroundColor Cyan
                Write-Host "             Run Python Test Suite             " -ForegroundColor Cyan
                Write-Host "===============================================" -ForegroundColor Cyan
                Write-Host ""
                
                $pythonSuites = Get-PythonTestSuites
                
                for ($i = 0; $i -lt $pythonSuites.Count; $i++) {
                    Write-Host "$($i+1): $($pythonSuites[$i].Name)"
                }
                
                Write-Host ""
                $selection = Read-Host "Enter the number of the test suite to run (or 'B' to go back)"
                
                if ($selection -ne "B" -and $selection -ne "b") {
                    $suiteIndex = [int]$selection - 1
                    
                    if ($suiteIndex -ge 0 -and $suiteIndex -lt $pythonSuites.Count) {
                        $suite = $pythonSuites[$suiteIndex]
                        
                        Write-Host ""
                        Write-Host "Running test suite: $($suite.Name)" -ForegroundColor Green
                        $result = Invoke-TestSuite -TestSuite $suite
                        
                        Write-Host ""
                        Write-Host "Test Suite: $($suite.Name)" -ForegroundColor Green
                        Write-Host "Status: $($result.status)" -ForegroundColor $(if ($result.status -eq "PASS") { "Green" } else { "Red" })
                        Write-Host "Tests: $($result.tests.total) total, $($result.tests.passed) passed, $($result.tests.failed) failed, $($result.tests.skipped) skipped"
                        Write-Host "Duration: $($result.duration) seconds"
                        Write-Host "Log File: $($result.logFile)"
                        
                        Write-Host ""
                        Read-Host "Press Enter to continue"
                    }
                }
            }
            '3' {
                # Run a JavaScript test suite
                Clear-Host
                Write-Host "===============================================" -ForegroundColor Cyan
                Write-Host "           Run JavaScript Test Suite           " -ForegroundColor Cyan
                Write-Host "===============================================" -ForegroundColor Cyan
                Write-Host ""
                
                $jsSuites = Get-JavaScriptTestSuites
                
                for ($i = 0; $i -lt $jsSuites.Count; $i++) {
                    Write-Host "$($i+1): $($jsSuites[$i].Name)"
                }
                
                Write-Host ""
                $selection = Read-Host "Enter the number of the test suite to run (or 'B' to go back)"
                
                if ($selection -ne "B" -and $selection -ne "b") {
                    $suiteIndex = [int]$selection - 1
                    
                    if ($suiteIndex -ge 0 -and $suiteIndex -lt $jsSuites.Count) {
                        $suite = $jsSuites[$suiteIndex]
                        
                        Write-Host ""
                        Write-Host "Running test suite: $($suite.Name)" -ForegroundColor Green
                        $result = Invoke-TestSuite -TestSuite $suite
                        
                        Write-Host ""
                        Write-Host "Test Suite: $($suite.Name)" -ForegroundColor Green
                        Write-Host "Status: $($result.status)" -ForegroundColor $(if ($result.status -eq "PASS") { "Green" } else { "Red" })
                        Write-Host "Tests: $($result.tests.total) total, $($result.tests.passed) passed, $($result.tests.failed) failed, $($result.tests.skipped) skipped"
                        Write-Host "Duration: $($result.duration) seconds"
                        Write-Host "Log File: $($result.logFile)"
                        
                        Write-Host ""
                        Read-Host "Press Enter to continue"
                    }
                }
            }
            '4' {
                # Show test results summary
                Clear-Host
                Write-Host "===============================================" -ForegroundColor Cyan
                Write-Host "            Test Results Summary              " -ForegroundColor Cyan
                Write-Host "===============================================" -ForegroundColor Cyan
                Write-Host ""
                
                $results = Get-TestResults
                $summary = Get-TestSummary -Results $results
                
                Write-Host ""
                Read-Host "Press Enter to continue"
            }
            '5' {
                # Show detailed test results
                Clear-Host
                Write-Host "===============================================" -ForegroundColor Cyan
                Write-Host "           Detailed Test Results              " -ForegroundColor Cyan
                Write-Host "===============================================" -ForegroundColor Cyan
                Write-Host ""
                
                $results = Get-TestResults
                
                Write-Host "Python Test Suites:"
                Write-Host ""
                
                foreach ($suiteName in $results.testSuites.python.PSObject.Properties.Name) {
                    $suite = $results.testSuites.python.$suiteName
                    $statusColor = switch ($suite.status) {
                        "PASS" { "Green" }
                        "FAIL" { "Red" }
                        "ERROR" { "Red" }
                        "SKIPPED" { "Yellow" }
                        default { "White" }
                    }
                    
                    Write-Host "${suiteName}: " -NoNewline
                    Write-Host "$($suite.status)" -ForegroundColor $statusColor
                    Write-Host "  Path: $($suite.path)"
                    Write-Host "  Last Run: $($suite.lastRun)"
                    Write-Host "  Duration: $($suite.duration) seconds"
                    Write-Host "  Tests: $($suite.tests.total) total, $($suite.tests.passed) passed, $($suite.tests.failed) failed, $($suite.tests.skipped) skipped"
                    
                    if ($suite.details) {
                        Write-Host "  Test Details:"
                        
                        foreach ($test in $suite.details) {
                            $testStatusColor = switch ($test.status) {
                                "PASS" { "Green" }
                                "FAIL" { "Red" }
                                "SKIPPED" { "Yellow" }
                                default { "White" }
                            }
                            
                            Write-Host "    $($test.name): " -NoNewline
                            Write-Host "$($test.status)" -ForegroundColor $testStatusColor
                        }
                    }
                    
                    Write-Host ""
                }
                
                Write-Host ""
                Write-Host "JavaScript Test Suites:"
                Write-Host ""
                
                foreach ($suiteName in $results.testSuites.javascript.PSObject.Properties.Name) {
                    $suite = $results.testSuites.javascript.$suiteName
                    $statusColor = switch ($suite.status) {
                        "PASS" { "Green" }
                        "FAIL" { "Red" }
                        "ERROR" { "Red" }
                        "SKIPPED" { "Yellow" }
                        default { "White" }
                    }
                    
                    Write-Host "${suiteName}: " -NoNewline
                    Write-Host "$($suite.status)" -ForegroundColor $statusColor
                    Write-Host "  Path: $($suite.path)"
                    Write-Host "  Last Run: $($suite.lastRun)"
                    Write-Host "  Duration: $($suite.duration) seconds"
                    Write-Host "  Tests: $($suite.tests.total) total, $($suite.tests.passed) passed, $($suite.tests.failed) failed, $($suite.tests.skipped) skipped"
                    
                    if ($suite.details) {
                        Write-Host "  Test Details:"
                        
                        foreach ($test in $suite.details) {
                            $testStatusColor = switch ($test.status) {
                                "PASS" { "Green" }
                                "FAIL" { "Red" }
                                "SKIPPED" { "Yellow" }
                                default { "White" }
                            }
                            
                            Write-Host "    $($test.name): " -NoNewline
                            Write-Host "$($test.status)" -ForegroundColor $testStatusColor
                        }
                    }
                    
                    Write-Host ""
                }
                
                Write-Host ""
                Read-Host "Press Enter to continue"
            }
            '6' {
                # Run all tests in parallel
                Clear-Host
                Write-Host "===============================================" -ForegroundColor Cyan
                Write-Host "           Run Tests in Parallel              " -ForegroundColor Cyan
                Write-Host "===============================================" -ForegroundColor Cyan
                Write-Host ""
                
                Write-Host "Enter maximum number of jobs (default: 10):"
                $jobsInput = Read-Host
                
                if ($jobsInput) {
                    $maxJobs = [int]$jobsInput
                } else {
                    $maxJobs = 10
                }
                
                Write-Host "Select partitioning strategy:"
                Write-Host "1: Component-based (group tests by component type)"
                Write-Host "2: Format-based (group tests by data format type)"
                Write-Host "3: Load-balanced (distribute based on historical execution time)"
                Write-Host ""
                $strategyInput = Read-Host "Enter selection (default: 3)"
                
                $strategy = "LoadBalanced"
                switch ($strategyInput) {
                    "1" { $strategy = "Component" }
                    "2" { $strategy = "Format" }
                    "3" { $strategy = "LoadBalanced" }
                }
                
                Write-Host ""
                Write-Host "Running all tests in parallel with $maxJobs max concurrent jobs using $strategy strategy..."
                
                $suites = Get-AllTestSuites
                $results = Invoke-ParallelTestExecution -TestSuites $suites -MaxJobs $maxJobs -PartitionStrategy $strategy
                
                Write-Host ""
                Write-Host "Parallel execution complete."
                Write-Host "Total Suites: $($suites.Count)"
                Write-Host "Completed Suites: $($results.completed.Count)"
                Write-Host "Passing Suites: $($results.passing.Count)"
                Write-Host "Failing Suites: $($results.failing.Count)"
                
                Write-Host ""
                Read-Host "Press Enter to continue"
            }
            '7' {
                # Export test reports
                Clear-Host
                Write-Host "===============================================" -ForegroundColor Cyan
                Write-Host "            Export Test Reports               " -ForegroundColor Cyan
                Write-Host "===============================================" -ForegroundColor Cyan
                Write-Host ""
                
                Write-Host "Select report type:"
                Write-Host "1: JUnit XML Reports"
                Write-Host "2: HTML Dashboard"
                Write-Host "3: Both"
                Write-Host "B: Back to main menu"
                Write-Host ""
                
                $selection = Read-Host "Please make a selection"
                
                switch ($selection) {
                    '1' {
                        # JUnit XML
                        $results = Get-TestResults
                        $reportPaths = Export-JUnitXmlReport -Results $results
                        
                        Write-Host ""
                        Write-Host "JUnit XML reports generated at:"
                        Write-Host $script:CONFIG.ReportsFolder
                        
                        Write-Host ""
                        Read-Host "Press Enter to continue"
                    }
                    '2' {
                        # HTML Dashboard
                        $results = Get-TestResults
                        $reportPath = Export-HtmlReport -Results $results
                        
                        Write-Host ""
                        Write-Host "HTML dashboard generated at:"
                        Write-Host $reportPath
                        
                        Write-Host ""
                        Write-Host "Would you like to open the HTML report? (Y/N)"
                        $openReport = Read-Host
                        
                        if ($openReport -eq "Y" -or $openReport -eq "y") {
                            Start-Process $reportPath
                        }
                        
                        Write-Host ""
                        Read-Host "Press Enter to continue"
                    }
                    '3' {
                        # Both
                        $results = Get-TestResults
                        $junitPaths = Export-JUnitXmlReport -Results $results
                        $htmlPath = Export-HtmlReport -Results $results
                        
                        Write-Host ""
                        Write-Host "JUnit XML reports and HTML dashboard generated:"
                        Write-Host "JUnit: $($script:CONFIG.ReportsFolder)/junit/"
                        Write-Host "HTML: $htmlPath"
                        
                        Write-Host ""
                        Write-Host "Would you like to open the HTML report? (Y/N)"
                        $openReport = Read-Host
                        
                        if ($openReport -eq "Y" -or $openReport -eq "y") {
                            Start-Process $htmlPath
                        }
                        
                        Write-Host ""
                        Read-Host "Press Enter to continue"
                    }
                    'B' {
                        # Back to main menu
                    }
                    'b' {
                        # Back to main menu
                    }
                    default {
                        Write-Host "Invalid selection." -ForegroundColor Red
                        Start-Sleep -Seconds 1
                    }
                }
            }
            '8' {
                # Run interactive test review
                Start-InteractiveReview
            }
            '9' {
                $exit = $true
            }
            default {
                Write-Host "Invalid selection." -ForegroundColor Red
                Start-Sleep -Seconds 1
            }
        }
    }
}

# Main function
function Main {
    # Create folders if they don't exist
    if (-not (Test-Path -Path $script:CONFIG.LogFolder)) {
        New-Item -Path $script:CONFIG.LogFolder -ItemType Directory -Force | Out-Null
    }
    
    if (-not (Test-Path -Path $script:CONFIG.ReportsFolder)) {
        New-Item -Path $script:CONFIG.ReportsFolder -ItemType Directory -Force | Out-Null
    }
    
    # Initialize CI environment if in CI mode
    if ($CI) {
        $ciEnv = Initialize-CIEnvironment
    }
    
    # Process command-line arguments
    if ($List) {
        # List all test suites
        Write-Host "Available Test Suites:" -ForegroundColor Cyan
        Write-Host ""
        
        Write-Host "Python Test Suites:" -ForegroundColor Green
        $pythonSuites = Get-PythonTestSuites
        
        foreach ($suite in $pythonSuites) {
            Write-Host "  $($suite.Name) ($($suite.Path))"
        }
        
        Write-Host ""
        Write-Host "JavaScript Test Suites:" -ForegroundColor Green
        $jsSuites = Get-JavaScriptTestSuites
        
        foreach ($suite in $jsSuites) {
            Write-Host "  $($suite.Name) ($($suite.Path))"
        }
        
        return
    }
    
    if ($Summary) {
        # Show test results summary
        $results = Get-TestResults
        $summary = Get-TestSummary -Results $results
        
        return
    }
    
    if ($Detail) {
        # Show detailed test results
        $results = Get-TestResults
        
        if ($Suite) {
            # Show details for specific suite
            if ($Type -eq "python") {
                if ($results.testSuites.python.PSObject.Properties[$Suite]) {
                    $suite = $results.testSuites.python.PSObject.Properties[$Suite].Value
                    Write-Host "Test Suite: $Suite (Python)" -ForegroundColor Cyan
                    Write-Host "Status: $($suite.status)" -ForegroundColor $(if ($suite.status -eq "PASS") { "Green" } else { "Red" })
                    Write-Host "Path: $($suite.path)"
                    Write-Host "Last Run: $($suite.lastRun)"
                    Write-Host "Duration: $($suite.duration) seconds"
                    Write-Host "Tests: $($suite.tests.total) total, $($suite.tests.passed) passed, $($suite.tests.failed) failed, $($suite.tests.skipped) skipped"
                    
                    if ($suite.details) {
                        Write-Host ""
                        Write-Host "Test Details:" -ForegroundColor Cyan
                        
                        foreach ($test in $suite.details) {
                            $testStatusColor = switch ($test.status) {
                                "PASS" { "Green" }
                                "FAIL" { "Red" }
                                "SKIPPED" { "Yellow" }
                                default { "White" }
                            }
                            
                            Write-Host "  $($test.name): " -NoNewline
                            Write-Host "$($test.status)" -ForegroundColor $testStatusColor
                        }
                    }
                } else {
                    Write-Host "Python test suite '$Suite' not found." -ForegroundColor Red
                }
            } elseif ($Type -eq "javascript") {
                if ($results.testSuites.javascript.PSObject.Properties[$Suite]) {
                    $suite = $results.testSuites.javascript.PSObject.Properties[$Suite].Value
                    Write-Host "Test Suite: $Suite (JavaScript)" -ForegroundColor Cyan
                    Write-Host "Status: $($suite.status)" -ForegroundColor $(if ($suite.status -eq "PASS") { "Green" } else { "Red" })
                    Write-Host "Path: $($suite.path)"
                    Write-Host "Last Run: $($suite.lastRun)"
                    Write-Host "Duration: $($suite.duration) seconds"
                    Write-Host "Tests: $($suite.tests.total) total, $($suite.tests.passed) passed, $($suite.tests.failed) failed, $($suite.tests.skipped) skipped"
                    
                    if ($suite.details) {
                        Write-Host ""
                        Write-Host "Test Details:" -ForegroundColor Cyan
                        
                        foreach ($test in $suite.details) {
                            $testStatusColor = switch ($test.status) {
                                "PASS" { "Green" }
                                "FAIL" { "Red" }
                                "SKIPPED" { "Yellow" }
                                default { "White" }
                            }
                            
                            Write-Host "  $($test.name): " -NoNewline
                            Write-Host "$($test.status)" -ForegroundColor $testStatusColor
                        }
                    }
                } else {
                    Write-Host "JavaScript test suite '$Suite' not found." -ForegroundColor Red
                }
            } else {
                Write-Host "Please specify a test type (python or javascript)." -ForegroundColor Red
            }
        } else {
            Write-Host "Please specify a test suite name with -Suite parameter." -ForegroundColor Red
        }
        
        return
    }
    
    if ($Suite) {
        # Run specific test suite
        if ($Type -eq "python") {
            $suite = [PSCustomObject]@{
                Name = $Suite
                Type = "python"
                Path = "tests/unit/$Suite.py"
            }
        } elseif ($Type -eq "javascript") {
            $suite = [PSCustomObject]@{
                Name = $Suite
                Type = "javascript"
                Path = "src/ui/components/__tests__/$Suite.test.js"
            }
        } else {
            Write-Host "Please specify a test type (python or javascript)." -ForegroundColor Red
            return
        }
        
        Write-Host "Running test suite: $Suite" -ForegroundColor Cyan
        $result = Invoke-TestSuite -TestSuite $suite
        
        Write-Host ""
        Write-Host "Test Suite: $Suite" -ForegroundColor Cyan
        Write-Host "Status: $($result.status)" -ForegroundColor $(if ($result.status -eq "PASS") { "Green" } else { "Red" })
        Write-Host "Tests: $($result.tests.total) total, $($result.tests.passed) passed, $($result.tests.failed) failed, $($result.tests.skipped) skipped"
        Write-Host "Duration: $($result.duration) seconds"
        Write-Host "Log File: $($result.logFile)"
        
        # Update exit code based on result
        if ($result.status -ne "PASS") {
            $script:CONFIG.ExitCode = 1
        }
        
        return
    }
    
    if ($Parallel) {
        # Run tests in parallel
        Write-Host "Running tests in parallel with $MaxJobs concurrent jobs using $PartitionStrategy strategy..." -ForegroundColor Cyan
        
        $suites = Get-AllTestSuites
        
        # Filter suites for CI partitioning
        if ($CI -and $TotalPartitions -gt 1) {
            $originalCount = $suites.Count
            $partitionSize = [Math]::Ceiling($suites.Count / $TotalPartitions)
            $startIndex = $Partition * $partitionSize
            $endIndex = [Math]::Min(($Partition + 1) * $partitionSize - 1, $suites.Count - 1)
            
            $suites = $suites[$startIndex..$endIndex]
            
            Write-Host "Running partition $Partition of $TotalPartitions" -ForegroundColor Cyan
            Write-Host "Original suite count: $originalCount, Partition size: $partitionSize" -ForegroundColor Cyan
            Write-Host "Running suites $startIndex to $endIndex ($($suites.Count) suites)" -ForegroundColor Cyan
        }
        
        $results = Invoke-ParallelTestExecution -TestSuites $suites -MaxJobs $MaxJobs -PartitionStrategy $PartitionStrategy
        
        Write-Host ""
        Write-Host "Parallel execution complete." -ForegroundColor Cyan
        Write-Host "Total Suites: $($suites.Count)"
        Write-Host "Completed Suites: $($results.completed.Count)"
        Write-Host "Passing Suites: $($results.passing.Count)"
        Write-Host "Failing Suites: $($results.failing.Count)"
        
        # Update exit code based on results
        if ($results.failing.Count -gt 0) {
            $script:CONFIG.ExitCode = 1
        }
        
        # Generate reports if requested
        if ($ExportJUnit) {
            $testResults = Get-TestResults
            $junitPaths = Export-JUnitXmlReport -Results $testResults
            Write-Host ""
            Write-Host "JUnit XML reports generated at:" -ForegroundColor Cyan
            Write-Host "$($script:CONFIG.ReportsFolder)/junit/"
        }
        
        if ($ExportHtml) {
            $testResults = Get-TestResults
            $htmlPath = Export-HtmlReport -Results $testResults
            Write-Host ""
            Write-Host "HTML dashboard generated at:" -ForegroundColor Cyan
            Write-Host $htmlPath
        }
        
        return
    }
    
    if ($Review) {
        # Start interactive test review
        Start-InteractiveReview
        return
    }
    
    if ($ExportJUnit) {
        # Export JUnit XML reports
        $results = Get-TestResults
        $reportPaths = Export-JUnitXmlReport -Results $results
        
        Write-Host "JUnit XML reports generated at:" -ForegroundColor Cyan
        Write-Host "$($script:CONFIG.ReportsFolder)/junit/"
        
        return
    }
    
    if ($ExportHtml) {
        # Export HTML dashboard
        $results = Get-TestResults
        $reportPath = Export-HtmlReport -Results $results
        
        Write-Host "HTML dashboard generated at:" -ForegroundColor Cyan
        Write-Host $reportPath
        
        return
    }
    
    if ($CI) {
        # Ensure TestTracker is explicitly sourced
        . $testTrackerPath
        
        # Generate dummy test results for demonstration
        $testResults = Get-TestResults

        # If test results don't exist, create dummy results for demo
        if ($null -eq $testResults -or $null -eq $testResults.summary) {
            Write-Host "Creating demo test results for CI mode" -ForegroundColor Yellow
            $testResults = [PSCustomObject]@{
                summary = @{
                    lastUpdated = (Get-Date).ToString("o")
                    totalSuites = 10
                    completedSuites = 10
                    passingSuites = 9
                    failingSuites = 1
                    overallStatus = "FAIL"
                }
                testSuites = @{
                    python = @{}
                    javascript = @{}
                }
            }
        }
        
        # Complete CI execution
        $ciStatus = Complete-CIExecution -Results $testResults
        
        # Set exit code
        $script:CONFIG.ExitCode = $ciStatus.ExitCode
        
        return
    }
    
    if ($Interactive -or (-not ($List -or $Suite -or $Parallel -or $Detail -or $Summary -or $Review -or $ExportJUnit -or $ExportHtml -or $CI))) {
        # Run in interactive mode
        Start-InteractiveMode
        return
    }
}

# Run the main function
Main

# Set exit code
exit $script:CONFIG.ExitCode
