using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Management;
using System.Management.Automation;
using System.Management.Automation.Runspaces;
using System.Security.Principal;
using System.Text;
using System.Threading.Tasks;

namespace Remotecollect
{
    public class LogCollectorService
    {
        private readonly List<Tuple<string, string>> agilentLogPaths = new List<Tuple<string, string>>
        {
            // Path format: (LocalPath, DisplayName)
            new Tuple<string, string>(@"C:\Program Files (x86)\Agilent Technologies\OpenLAB Data Store\tomcat\logs", "TomcatLogFiles"),
            new Tuple<string, string>(@"C:\ProgramData\Agilent\installLogs", "installLogs"),
            new Tuple<string, string>(@"C:\SVReports", "SVReports"),
            new Tuple<string, string>(@"C:\ProgramData\Agilent\LogFiles", "CDSLogs"),
            new Tuple<string, string>(@"C:\Program Files (x86)\Agilent Technologies\OpenLAB Services\Licensing\Flexera\logs", "flexLogs"),
            new Tuple<string, string>(@"C:\Program Files (x86)\Agilent Technologies\Content Management Search Services\logs", "searchLogs"),
            new Tuple<string, string>(@"C:\Program Files (x86)\Agilent Technologies\Content Management Search Services\solr\server\logs", "SolrLogs"),
            new Tuple<string, string>(@"C:\Program Files (x86)\Agilent Technologies\OpenLab Reverse Proxy Configuration Service\ConfigurationService\logs\service", "RPCFGlogs"),
            new Tuple<string, string>(@"C:\Program Files\OpenLab Reverse Proxy\Apache24\logs", "2.7RPlogs"),
            new Tuple<string, string>(@"C:\Program Files (x86)\OpenLab Reverse Proxy\Apache24\logs", "2.6RPlogs"),
            new Tuple<string, string>(@"C:\ProgramData\Agilent\installation", "installConf"),
            new Tuple<string, string>(@"C:\ProgramData\Agilent\OpenLab ECM XT Import Scheduler\Logs", "imporschedulerlog"),
            new Tuple<string, string>(@"D:\MassHunter\log", "MassHunterLog"),
            new Tuple<string, string>(@"C:\ProgramData\Agilent Technologies\ChemStation", "ChemstationLog"),
        };

        public event EventHandler<LogMessageEventArgs> LogMessage;
        
        // Session timestamp for organizing all collections in the same session
        public string SessionTimestamp { get; set; }

        public async Task<CollectionResult> CollectLogsAsync(ComputerInfo computer)
        {
            var result = new CollectionResult
            {
                Hostname = computer.Hostname,
                CollectionTime = DateTime.Now
            };

            Logger.Info($"Starting log collection from {computer.Hostname}");
            // Use session timestamp if set, otherwise use current timestamp
            var sessionTimestamp = SessionTimestamp ?? DateTime.Now.ToString("yyyyMMdd_HHmmss");
            var timestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
            
            // Get current user's Documents folder (not admin's folder if running elevated)
            string documentsPath = GetCurrentUserDocumentsFolder();
            var destinationBase = Path.Combine(
                documentsPath,
                $"Logs_{sessionTimestamp}",
                $"{computer.Hostname}_{timestamp}"
            );

            result.DestinationPath = destinationBase;
            Logger.Info($"Destination directory: {destinationBase}");
            // Don't create folder yet - only create if we find content to copy

            Log($"\n=== Starting collection from {computer.Hostname} ===", LogLevel.Info);

            bool success = false;

            // Method 1: Try SMB Administrative Shares (C$)
            Log($"Attempting Method 1: SMB Administrative Share (C$) for {computer.Hostname}...", LogLevel.Info);
            try
            {
                var smbResult = await CollectViaSMBAsync(computer, destinationBase, result);
                if (smbResult)
                {
                    result.Success = true;
                    result.ConnectionMethod = "SMB (C$)";
                    Log($"✓ Method 1 (SMB) succeeded for {computer.Hostname}", LogLevel.Success);
                    return result;
                }
            }
            catch (Exception ex)
            {
                Log($"✗ Method 1 (SMB) failed for {computer.Hostname}: {ex.Message}", LogLevel.Warning);
                result.ErrorMessage = $"SMB failed: {ex.Message}";
            }

            // Method 2: Try PowerShell Remoting (WinRM)
            Log($"Attempting Method 2: PowerShell Remoting (WinRM) for {computer.Hostname}...", LogLevel.Info);
            try
            {
                var winrmResult = await CollectViaWinRMAsync(computer, destinationBase, result);
                if (winrmResult)
                {
                    result.Success = true;
                    result.ConnectionMethod = "WinRM";
                    Log($"✓ Method 2 (WinRM) succeeded for {computer.Hostname}", LogLevel.Success);
                    return result;
                }
            }
            catch (Exception ex)
            {
                Log($"✗ Method 2 (WinRM) failed for {computer.Hostname}: {ex.Message}", LogLevel.Warning);
                if (string.IsNullOrEmpty(result.ErrorMessage))
                {
                    result.ErrorMessage = $"WinRM failed: {ex.Message}";
                }
            }

            // Method 3: Try PSExec Fallback
            Log($"Attempting Method 3: PSExec for {computer.Hostname}...", LogLevel.Info);
            try
            {
                var psexecResult = await CollectViaPSExecAsync(computer, destinationBase, result);
                if (psexecResult)
                {
                    result.Success = true;
                    result.ConnectionMethod = "PSExec";
                    Log($"✓ Method 3 (PSExec) succeeded for {computer.Hostname}", LogLevel.Success);
                    return result;
                }
            }
            catch (Exception ex)
            {
                Log($"✗ Method 3 (PSExec) failed for {computer.Hostname}: {ex.Message}", LogLevel.Warning);
                if (string.IsNullOrEmpty(result.ErrorMessage))
                {
                    result.ErrorMessage = $"PSExec failed: {ex.Message}";
                }
            }

            if (!success)
            {
                result.Success = false;
                if (string.IsNullOrEmpty(result.ErrorMessage))
                {
                    result.ErrorMessage = "All connection methods failed";
                }
                Log($"✗ All connection methods failed for {computer.Hostname}", LogLevel.Error);
            }

            // Final check: if destination folder exists but is empty, remove it
            if (Directory.Exists(destinationBase))
            {
                try
                {
                    var files = Directory.GetFiles(destinationBase, "*", SearchOption.AllDirectories);
                    if (files.Length == 0)
                    {
                        Directory.Delete(destinationBase, true);
                        result.DestinationPath = null;
                        if (success)
                        {
                            result.Success = false;
                        }
                    }
                }
                catch (Exception ex)
                {
                    Logger.Warning($"Failed to verify destination folder: {ex.Message}");
                }
            }
            else if (!success)
            {
                result.DestinationPath = null;
            }

            return result;
        }

        private async Task<bool> CollectViaSMBAsync(ComputerInfo computer, string destinationBase, CollectionResult result)
        {
            return await Task.Run(() =>
            {
                try
                {
                    bool anyFilesCollected = false;

                    foreach (var logPathTuple in agilentLogPaths)
                    {
                        var localPath = logPathTuple.Item1;
                        var displayName = logPathTuple.Item2;
                        
                        // Convert local path to UNC path for SMB access
                        // Handle C: drive
                        string uncPath;
                        if (localPath.StartsWith(@"C:\"))
                        {
                            uncPath = $@"\\{computer.Hostname}\C$\{localPath.Substring(3)}";
                        }
                        // Handle D: drive
                        else if (localPath.StartsWith(@"D:\"))
                        {
                            uncPath = $@"\\{computer.Hostname}\D$\{localPath.Substring(3)}";
                        }
                        else
                        {
                            // For other drives, try to map to C$ (fallback)
                            uncPath = $@"\\{computer.Hostname}\C$\{localPath.Replace(":", "").TrimStart('\\')}";
                        }

                        if (Directory.Exists(uncPath))
                        {
                            // Check if directory has files (excluding .dmp files)
                            var sourceFiles = Directory.GetFiles(uncPath, "*", SearchOption.AllDirectories)
                                .Where(f => !Path.GetExtension(f).Equals(".dmp", StringComparison.OrdinalIgnoreCase))
                                .ToList();
                            
                            if (sourceFiles.Count > 0)
                            {
                                // Only create folders if we have files to copy
                                if (!Directory.Exists(destinationBase))
                                {
                                    Directory.CreateDirectory(destinationBase);
                                }
                                
                                Log($"  Found directory: {displayName} ({localPath})", LogLevel.Info);
                                result.CollectedItems.Add($"{displayName} ({localPath})");
                                var destPath = Path.Combine(destinationBase, displayName);

                                Directory.CreateDirectory(destPath);
                                CopyDirectoryWithFilter(uncPath, destPath, ref anyFilesCollected);
                            }
                            else
                            {
                                result.NotFoundItems.Add($"{displayName} ({localPath})");
                                Log($"  Directory exists but empty: {displayName} ({localPath})", LogLevel.Info);
                            }
                        }
                        else
                        {
                            result.NotFoundItems.Add($"{displayName} ({localPath})");
                            Log($"  Not found: {displayName} ({localPath})", LogLevel.Info);
                        }
                    }

                    // Always ensure destination folder exists for system info collection
                    // System info should be collected whenever PC is reachable, regardless of Agilent logs
                    if (!Directory.Exists(destinationBase))
                    {
                        Directory.CreateDirectory(destinationBase);
                    }

                    // Collect system information and event logs via remote execution
                    // Always try to collect, even if no Agilent logs were found
                    // The collection methods will create the destination folder if they find content
                    CollectSystemInfoAndEventLogsViaSMB(computer, destinationBase, ref anyFilesCollected, result);
                    
                    // If system info wasn't successfully collected, try alternative SMB method
                    // This ensures system info is always attempted when PC is reachable
                    // Only try fallback if it wasn't successfully collected (not if it was already collected)
                    if (!result.CollectedItems.Contains("System_Info"))
                    {
                        Log("  System info not collected via primary method, attempting alternative SMB method...", LogLevel.Info);
                        // Remove from NotFoundItems if it was added, so we can retry
                        if (result.NotFoundItems.Contains("System_Info"))
                        {
                            result.NotFoundItems.Remove("System_Info");
                        }
                        CollectSystemInfoViaSMBDirect(computer, destinationBase, ref anyFilesCollected, result);
                    }
                    
                    CollectSQLServerLogsViaSMB(computer, destinationBase, ref anyFilesCollected, result);

                    // If nothing was collected, ensure destination folder doesn't exist
                    if (!anyFilesCollected && Directory.Exists(destinationBase))
                    {
                        try
                        {
                            if (Directory.GetFiles(destinationBase, "*", SearchOption.AllDirectories).Length == 0)
                            {
                                Directory.Delete(destinationBase, true);
                                result.DestinationPath = null;
                            }
                        }
                        catch { /* Ignore cleanup errors */ }
                    }

                    return anyFilesCollected;
                }
                catch (Exception ex)
                {
                    throw new Exception($"SMB collection failed: {ex.Message}", ex);
                }
            });
        }

        private async Task<bool> CollectViaWinRMAsync(ComputerInfo computer, string destinationBase, CollectionResult result)
        {
            return await Task.Run(() =>
            {
                try
                {
                    using (var ps = PowerShell.Create())
                    {
                        // Suppress snap-in loading errors that may occur in framework-dependent builds
                        ps.AddScript("$ErrorActionPreference = 'SilentlyContinue'; Get-PSSnapin -Registered | Out-Null");
                        ps.Invoke();
                        ps.Commands.Clear();
                        ps.Streams.Error.Clear();
                        
                        // Test WinRM connectivity
                        ps.AddCommand("Test-WSMan")
                            .AddParameter("ComputerName", computer.Hostname)
                            .AddParameter("ErrorAction", "Stop");

                        var testResult = ps.Invoke();
                        
                        // Check for errors, but ignore Diagnostics snap-in errors (known issue with framework-dependent builds)
                        if (ps.HadErrors)
                        {
                            bool hasNonDiagnosticsError = false;
                            var errors = ps.Streams.Error.ToList();
                            
                            foreach (var error in errors)
                            {
                                if (error.Exception != null && 
                                    (error.Exception.Message.Contains("Microsoft.PowerShell.Diagnostics") ||
                                     error.Exception.Message.Contains("Microsoft.PowerShell.Commands.Diagnostics") ||
                                     error.Exception.Message.Contains("Could not load file or assembly")))
                                {
                                    // Ignore Diagnostics snap-in errors - this is a known issue with framework-dependent builds
                                    Logger.Warning($"Ignoring PowerShell Diagnostics snap-in error: {error.Exception.Message}");
                                    continue;
                                }
                                hasNonDiagnosticsError = true;
                            }
                            
                            if (hasNonDiagnosticsError)
                            {
                                throw new Exception("WinRM not available or not configured");
                            }
                            
                            // Clear the Diagnostics errors so we can continue
                            ps.Streams.Error.Clear();
                        }

                        ps.Commands.Clear();

                        // Create remote session
                        ps.AddCommand("New-PSSession")
                            .AddParameter("ComputerName", computer.Hostname)
                            .AddParameter("ErrorAction", "Stop");

                        var sessions = ps.Invoke();
                        
                        // Check for errors, but ignore Diagnostics snap-in errors
                        if (ps.HadErrors)
                        {
                            bool hasNonDiagnosticsError = false;
                            var errors = ps.Streams.Error.ToList();
                            
                            foreach (var error in errors)
                            {
                                if (error.Exception != null && 
                                    (error.Exception.Message.Contains("Microsoft.PowerShell.Diagnostics") ||
                                     error.Exception.Message.Contains("Microsoft.PowerShell.Commands.Diagnostics") ||
                                     error.Exception.Message.Contains("Could not load file or assembly")))
                                {
                                    // Ignore Diagnostics snap-in errors
                                    Logger.Warning($"Ignoring PowerShell Diagnostics snap-in error during session creation: {error.Exception.Message}");
                                    continue;
                                }
                                hasNonDiagnosticsError = true;
                            }
                            
                            if (hasNonDiagnosticsError)
                            {
                                throw new Exception("Failed to create PSSession");
                            }
                            
                            // Clear the Diagnostics errors
                            ps.Streams.Error.Clear();
                        }
                        
                        if (sessions.Count == 0)
                        {
                            throw new Exception("Failed to create PSSession - no sessions returned");
                        }

                        var session = sessions[0].BaseObject as PSSession;
                        if (session == null)
                        {
                            throw new Exception("Failed to create PSSession - invalid session object");
                        }

                        try
                        {
                            ps.Commands.Clear();

                            // Build script to collect and compress logs remotely
                            var scriptBlock = BuildRemoteCollectionScriptBlock();

                            ps.AddCommand("Invoke-Command")
                                .AddParameter("Session", session)
                                .AddParameter("ScriptBlock", scriptBlock);

                            var results = ps.Invoke();

                            // Check for errors, but ignore Diagnostics snap-in errors
                            if (ps.HadErrors)
                            {
                                var errors = ps.Streams.Error.ToList();
                                var realErrors = new List<string>();
                                
                                foreach (var error in errors)
                                {
                                    if (error.Exception != null && 
                                        (error.Exception.Message.Contains("Microsoft.PowerShell.Diagnostics") ||
                                         error.Exception.Message.Contains("Microsoft.PowerShell.Commands.Diagnostics") ||
                                         error.Exception.Message.Contains("Could not load file or assembly")))
                                    {
                                        // Ignore Diagnostics snap-in errors
                                        Logger.Warning($"Ignoring PowerShell Diagnostics snap-in error during script execution: {error.Exception.Message}");
                                        continue;
                                    }
                                    realErrors.Add(error.ToString());
                                }
                                
                                if (realErrors.Count > 0)
                                {
                                    var errorMessage = string.Join("; ", realErrors);
                                    throw new Exception($"Remote script execution failed: {errorMessage}");
                                }
                                
                                // Clear the Diagnostics errors
                                ps.Streams.Error.Clear();
                            }

                            // Download the compressed archive
                            ps.Commands.Clear();
                            ps.AddCommand("Copy-Item")
                                .AddParameter("Path", $@"\\{computer.Hostname}\C$\Temp\AgilentLogs.zip")
                                .AddParameter("Destination", Path.Combine(destinationBase, "AgilentLogs.zip"))
                                .AddParameter("Force");

                            ps.Invoke();

                            if (File.Exists(Path.Combine(destinationBase, "AgilentLogs.zip")))
                            {
                                ZipFile.ExtractToDirectory(
                                    Path.Combine(destinationBase, "AgilentLogs.zip"),
                                    destinationBase
                                );
                                File.Delete(Path.Combine(destinationBase, "AgilentLogs.zip"));
                                
                                // Extract and analyze what was collected
                                AnalyzeCollectedItems(destinationBase, result);
                                
                                // Collect system info and event logs via WinRM
                                CollectSystemInfoAndEventLogsViaWinRM(computer, session, destinationBase, result);
                                
                                // Collect SQL Server logs via WinRM
                                CollectSQLServerLogsViaWinRM(computer, session, destinationBase, result);
                                
                                return true;
                            }
                        }
                        finally
                        {
                            // Cleanup session
                            ps.Commands.Clear();
                            ps.AddCommand("Remove-PSSession")
                                .AddParameter("Session", session);
                            ps.Invoke();
                        }
                    }

                    return false;
                }
                catch (Exception ex)
                {
                    throw new Exception($"WinRM collection failed: {ex.Message}", ex);
                }
            });
        }

        private ScriptBlock BuildRemoteCollectionScriptBlock()
        {
            var pathConfigs = agilentLogPaths.Select(t => new { Path = t.Item1, Name = t.Item2 }).ToList();
            var pathsArray = string.Join(", ", pathConfigs.Select(p => 
            {
                var escapedPath = p.Path.Replace("'", "''");
                var escapedName = p.Name.Replace("'", "''");
                return $"@{{Path='{escapedPath}'; Name='{escapedName}'}}";
            }));
            
            var scriptText = $@"
                $tempZip = 'C:\Temp\AgilentLogs.zip'
                $tempDir = 'C:\Temp\AgilentLogs'
                
                if (Test-Path $tempDir) {{ Remove-Item $tempDir -Recurse -Force }}
                if (Test-Path $tempZip) {{ Remove-Item $tempZip -Force }}
                
                New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
                
                # Collect Agilent logs
                $logConfigs = @({pathsArray})
                
                foreach ($config in $logConfigs) {{
                    $path = $config.Path
                    $displayName = $config.Name
                    
                    if (Test-Path $path) {{
                        $destPath = Join-Path $tempDir $displayName
                        New-Item -ItemType Directory -Path $destPath -Force | Out-Null
                        
                        Get-ChildItem -Path $path -Recurse -File | Where-Object {{
                            $_.Extension -ne '.dmp'
                        }} | ForEach-Object {{
                            $destFile = Join-Path $destPath $_.Name
                            $counter = 1
                            $baseName = $_.BaseName
                            $extension = $_.Extension
                            while (Test-Path $destFile) {{
                                $destFile = Join-Path $destPath ($baseName + '_' + $counter + $extension)
                                $counter++
                            }}
                            Copy-Item $_.FullName -Destination $destFile -Force
                        }}
                    }}
                }}
                
                # Collect System Information
                $sysInfoDir = Join-Path $tempDir 'System_Info'
                New-Item -ItemType Directory -Path $sysInfoDir -Force | Out-Null
                
                systeminfo | Out-File (Join-Path $sysInfoDir 'systeminfo.txt') -Encoding UTF8
                Get-HotFix | Sort-Object InstalledOn -Descending | Format-List | Out-File (Join-Path $sysInfoDir 'installed_updates.txt') -Encoding UTF8
                Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* | Select-Object DisplayName, DisplayVersion | Format-List | Out-File (Join-Path $sysInfoDir 'installed_programs.txt') -Encoding UTF8
                Get-Service | Select-Object Status, Name, DisplayName | Format-List | Out-File (Join-Path $sysInfoDir 'system_services.txt') -Encoding UTF8
                
                # Collect Windows Event Logs
                $eventLogDir = Join-Path $sysInfoDir 'EventLogs'
                New-Item -ItemType Directory -Path $eventLogDir -Force | Out-Null
                
                foreach ($logName in @('Application', 'System', 'Security')) {{
                    try {{
                        $evtxFile = Join-Path $eventLogDir ($logName + '.evtx')
                        wevtutil epl $logName $evtxFile 2>$null
                    }} catch {{}}
                }}
                
                # Collect SQL Server Logs
                $sqlLogDir = Join-Path $tempDir 'SQLServer_Logs'
                New-Item -ItemType Directory -Path $sqlLogDir -Force | Out-Null
                
                $sqlPaths = @(
                    'C:\Program Files\Microsoft SQL Server\MSSQL*\MSSQL\Log',
                    'C:\Program Files (x86)\Microsoft SQL Server\MSSQL*\MSSQL\Log'
                )
                
                foreach ($sqlPath in $sqlPaths) {{
                    $foundDirs = Get-ChildItem -Path $sqlPath -ErrorAction SilentlyContinue -Directory
                    foreach ($dir in $foundDirs) {{
                        $destDir = Join-Path $sqlLogDir $dir.Name
                        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
                        Get-ChildItem -Path $dir.FullName -File | Where-Object {{ $_.Extension -ne '.dmp' }} | Copy-Item -Destination $destDir -Force -ErrorAction SilentlyContinue
                    }}
                }}
                
                Compress-Archive -Path $tempDir\* -DestinationPath $tempZip -Force
                Remove-Item $tempDir -Recurse -Force
            ";

            return ScriptBlock.Create(scriptText);
        }

        private void CollectSystemInfoAndEventLogsViaWinRM(ComputerInfo computer, System.Management.Automation.Runspaces.PSSession session, string destinationBase, CollectionResult result)
        {
            try
            {
                // Check if this is localhost - if so, use local execution instead of remote
                var localHostname = Environment.MachineName;
                if (computer.Hostname.Equals(localHostname, StringComparison.OrdinalIgnoreCase))
                {
                    Log("    Detected localhost - collecting system info locally...", LogLevel.Info);
                    bool anyFilesCollected = false;
                    CollectSystemInfoLocally(destinationBase, ref anyFilesCollected, result);
                    return;
                }

                using (var ps = PowerShell.Create())
                {
                    var sysInfoDir = Path.Combine(destinationBase, "System_Info");
                    // Don't create directory yet - only create if we have data

                    ps.AddCommand("Invoke-Command")
                        .AddParameter("Session", session)
                        .AddParameter("ScriptBlock", ScriptBlock.Create(@"
                            $sysInfo = @{
                                SystemInfo = systeminfo
                                HotFixes = Get-HotFix | Sort-Object InstalledOn -Descending | Format-List | Out-String
                                Programs = Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* | Select-Object DisplayName, DisplayVersion | Format-List | Out-String
                                Services = Get-Service | Select-Object Status, Name, DisplayName | Format-List | Out-String
                            }
                            return $sysInfo
                        "));

                    var results = ps.Invoke();
                    
                    // Check for PowerShell errors
                    if (ps.Streams.Error.Count > 0)
                    {
                        var errors = string.Join("; ", ps.Streams.Error.Select(e => e.ToString()));
                        Log($"    PowerShell errors during system info collection: {errors}", LogLevel.Warning);
                        Logger.Warning($"PowerShell errors collecting system info from {computer.Hostname}: {errors}");
                    }
                    
                    if (results.Count > 0 && results[0].Properties != null)
                    {
                        var sysInfo = results[0].Properties;
                        
                        // Check if we have any actual data
                        bool hasData = false;
                        string systemInfoValue = sysInfo["SystemInfo"]?.Value?.ToString() ?? "";
                        string hotFixesValue = sysInfo["HotFixes"]?.Value?.ToString() ?? "";
                        string programsValue = sysInfo["Programs"]?.Value?.ToString() ?? "";
                        string servicesValue = sysInfo["Services"]?.Value?.ToString() ?? "";
                        
                        if (!string.IsNullOrWhiteSpace(systemInfoValue))
                            hasData = true;
                        if (!string.IsNullOrWhiteSpace(hotFixesValue))
                            hasData = true;
                        if (!string.IsNullOrWhiteSpace(programsValue))
                            hasData = true;
                        if (!string.IsNullOrWhiteSpace(servicesValue))
                            hasData = true;
                        
                        if (hasData)
                        {
                            // Create destination base folder if it doesn't exist
                            if (!Directory.Exists(destinationBase))
                            {
                                Directory.CreateDirectory(destinationBase);
                            }
                            
                            // Create system info directory
                            Directory.CreateDirectory(sysInfoDir);
                            
                            try
                            {
                                File.WriteAllText(Path.Combine(sysInfoDir, "systeminfo.txt"), systemInfoValue, Encoding.UTF8);
                                Log($"    Collected systeminfo.txt", LogLevel.Info);
                            }
                            catch (Exception ex)
                            {
                                Log($"    Error writing systeminfo.txt: {ex.Message}", LogLevel.Warning);
                            }
                            
                            try
                            {
                                File.WriteAllText(Path.Combine(sysInfoDir, "installed_updates.txt"), hotFixesValue, Encoding.UTF8);
                                Log($"    Collected installed_updates.txt", LogLevel.Info);
                            }
                            catch (Exception ex)
                            {
                                Log($"    Error writing installed_updates.txt: {ex.Message}", LogLevel.Warning);
                            }
                            
                            try
                            {
                                File.WriteAllText(Path.Combine(sysInfoDir, "installed_programs.txt"), programsValue, Encoding.UTF8);
                                Log($"    Collected installed_programs.txt", LogLevel.Info);
                            }
                            catch (Exception ex)
                            {
                                Log($"    Error writing installed_programs.txt: {ex.Message}", LogLevel.Warning);
                            }
                            
                            try
                            {
                                File.WriteAllText(Path.Combine(sysInfoDir, "system_services.txt"), servicesValue, Encoding.UTF8);
                                Log($"    Collected system_services.txt", LogLevel.Info);
                            }
                            catch (Exception ex)
                            {
                                Log($"    Error writing system_services.txt: {ex.Message}", LogLevel.Warning);
                            }
                            
                            result.CollectedItems.Add("System_Info");
                            Log($"    System info collection completed successfully", LogLevel.Success);
                        }
                        else
                        {
                            Log($"    Warning: System info collection returned no data", LogLevel.Warning);
                            result.NotFoundItems.Add("System_Info");
                        }
                    }
                    else
                    {
                        Log($"    Warning: System info collection returned no results", LogLevel.Warning);
                        result.NotFoundItems.Add("System_Info");
                    }
                }
            }
            catch (Exception ex)
            {
                Log($"    Warning: Could not collect system info via WinRM: {ex.Message}", LogLevel.Warning);
                Logger.Error($"Error collecting system info via WinRM from {computer.Hostname}", ex);
                result.NotFoundItems.Add("System_Info");
            }
        }

        private void CollectSQLServerLogsViaWinRM(ComputerInfo computer, System.Management.Automation.Runspaces.PSSession session, string destinationBase, CollectionResult result)
        {
            try
            {
                using (var ps = PowerShell.Create())
                {
                    var sqlLogDir = Path.Combine(destinationBase, "SQLServer_Logs");
                    // Don't create directory yet - only create if we find SQL logs

                    ps.AddCommand("Invoke-Command")
                        .AddParameter("Session", session)
                        .AddParameter("ScriptBlock", ScriptBlock.Create(@"
                            $sqlPaths = @(
                                'C:\Program Files\Microsoft SQL Server\MSSQL*\MSSQL\Log',
                                'C:\Program Files (x86)\Microsoft SQL Server\MSSQL*\MSSQL\Log'
                            )
                            $foundPaths = @()
                            foreach ($path in $sqlPaths) {
                                $dirs = Get-ChildItem -Path $path -ErrorAction SilentlyContinue -Directory
                                foreach ($dir in $dirs) {
                                    $foundPaths += $dir.FullName
                                }
                            }
                            return $foundPaths
                        "));

                    var results = ps.Invoke();
                    bool sqlFilesCollected = false;
                    foreach (var pathResult in results)
                    {
                        var path = pathResult.ToString();
                        if (!string.IsNullOrEmpty(path))
                        {
                            // Copy files via UNC
                            var uncPath = path.Replace("C:\\", $@"\\{computer.Hostname}\C$\");
                            if (Directory.Exists(uncPath))
                            {
                                // Check if source directory has files (excluding .dmp)
                                var sourceFiles = Directory.GetFiles(uncPath, "*", SearchOption.AllDirectories)
                                    .Where(f => !Path.GetExtension(f).Equals(".dmp", StringComparison.OrdinalIgnoreCase))
                                    .ToList();
                                
                                if (sourceFiles.Count > 0)
                                {
                                    // Create destination base folder if it doesn't exist
                                    if (!Directory.Exists(destinationBase))
                                    {
                                        Directory.CreateDirectory(destinationBase);
                                    }
                                    
                                    // Create SQL logs directory if it doesn't exist
                                    if (!Directory.Exists(sqlLogDir))
                                    {
                                        Directory.CreateDirectory(sqlLogDir);
                                    }
                                    
                                    var dirName = new DirectoryInfo(uncPath).Name;
                                    var destPath = Path.Combine(sqlLogDir, dirName);
                                    Directory.CreateDirectory(destPath);
                                    CopyDirectoryWithFilter(uncPath, destPath, ref sqlFilesCollected);
                                }
                            }
                        }
                    }
                    
                    if (sqlFilesCollected)
                    {
                        result.CollectedItems.Add("SQLServer_Logs");
                    }
                    else
                    {
                        result.NotFoundItems.Add("SQLServer_Logs");
                    }
                }
            }
            catch (Exception ex)
            {
                Log($"    Warning: Could not collect SQL Server logs via WinRM: {ex.Message}", LogLevel.Warning);
                result.NotFoundItems.Add("SQLServer_Logs");
            }
        }

        private async Task<bool> CollectViaPSExecAsync(ComputerInfo computer, string destinationBase, CollectionResult result)
        {
            return await Task.Run(() =>
            {
                try
                {
                    var psexecPath = FindPSExec();
                    if (string.IsNullOrEmpty(psexecPath))
                    {
                        throw new Exception("PSExec not found. Please ensure Sysinternals PSExec is installed or in PATH.");
                    }

                    // Create a batch script that will run remotely
                    var batchScript = CreateRemoteBatchScript();
                    var localScriptPath = Path.Combine(Path.GetTempPath(), $"collect_logs_{Guid.NewGuid()}.bat");
                    File.WriteAllText(localScriptPath, batchScript);

                    try
                    {
                        // Copy script to remote machine
                        var remoteScriptPath = $@"\\{computer.Hostname}\C$\Temp\collect_logs.bat";
                        var remoteDir = Path.GetDirectoryName(remoteScriptPath);
                        if (!string.IsNullOrEmpty(remoteDir) && !Directory.Exists(remoteDir))
                        {
                            Directory.CreateDirectory(remoteDir);
                        }
                        File.Copy(localScriptPath, remoteScriptPath, true);

                        // Execute via PSExec
                        var psi = new System.Diagnostics.ProcessStartInfo
                        {
                            FileName = psexecPath,
                            Arguments = $@"\\{computer.Hostname} -s -h -accepteula -c ""{localScriptPath}""",
                            UseShellExecute = false,
                            RedirectStandardOutput = true,
                            RedirectStandardError = true,
                            CreateNoWindow = true,
                            WindowStyle = System.Diagnostics.ProcessWindowStyle.Hidden
                        };

                        using (var process = System.Diagnostics.Process.Start(psi))
                        {
                            if (process != null)
                            {
                                process.WaitForExit(300000); // 5 minute timeout
                                
                                // Try to copy results back
                                var remoteZip = $@"\\{computer.Hostname}\C$\Temp\AgilentLogs.zip";
                                if (File.Exists(remoteZip))
                                {
                                    var localZip = Path.Combine(destinationBase, "AgilentLogs.zip");
                                    File.Copy(remoteZip, localZip, true);
                                    
                                    ZipFile.ExtractToDirectory(localZip, destinationBase);
                                    File.Delete(localZip);
                                    
                                    // System info and event logs are already included in the zip from the PowerShell script
                                    return true;
                                }
                            }
                        }
                    }
                    finally
                    {
                        if (File.Exists(localScriptPath))
                        {
                            File.Delete(localScriptPath);
                        }
                    }

                    return false;
                }
                catch (Exception ex)
                {
                    throw new Exception($"PSExec collection failed: {ex.Message}", ex);
                }
            });
        }

        private string CreateRemoteBatchScript()
        {
            // Build the path configurations for the PowerShell script
            var sb = new System.Text.StringBuilder();
            for (int i = 0; i < agilentLogPaths.Count; i++)
            {
                var tuple = agilentLogPaths[i];
                var path = tuple.Item1.Replace("'", "''").Replace("(", "^(").Replace(")", "^)");
                var name = tuple.Item2.Replace("'", "''");
                sb.Append($"echo     @{{Path='{path}'; Name='{name}'}}");
                if (i < agilentLogPaths.Count - 1)
                {
                    sb.AppendLine(",");
                }
                else
                {
                    sb.AppendLine();
                }
            }
            var pathsSection = sb.ToString();

            // Create a PowerShell script that will be executed via PSExec
            var script = $@"@echo off
setlocal enabledelayedexpansion

set TEMP_DIR=C:\Temp\AgilentLogs
set ZIP_FILE=C:\Temp\AgilentLogs.zip
set PS_SCRIPT=C:\Temp\collect_logs_ps.ps1

REM Cleanup previous runs
if exist ""%TEMP_DIR%"" rmdir /s /q ""%TEMP_DIR%""
if exist ""%ZIP_FILE%"" del /q ""%ZIP_FILE%""
if exist ""%PS_SCRIPT%"" del /q ""%PS_SCRIPT%""

REM Create PowerShell script for log collection
(
echo $tempZip = '%ZIP_FILE%'
echo $tempDir = '%TEMP_DIR%'
echo.
echo if ^(Test-Path $tempDir^) {{ Remove-Item $tempDir -Recurse -Force }}
echo if ^(Test-Path $tempZip^) {{ Remove-Item $tempZip -Force }}
echo.
echo New-Item -ItemType Directory -Path $tempDir -Force ^| Out-Null
echo.
echo $logConfigs = @^(
{pathsSection}echo ^)
echo.
echo foreach ^($config in $logConfigs^) {{
echo     $path = $config.Path
echo     $displayName = $config.Name
echo     if ^(Test-Path $path^) {{
echo         $destPath = Join-Path $tempDir $displayName
echo         New-Item -ItemType Directory -Path $destPath -Force ^| Out-Null
echo         Get-ChildItem -Path $path -Recurse -File ^| Where-Object {{ $_.Extension -ne '.dmp' }} ^| ForEach-Object {{
echo             $destFile = Join-Path $destPath $_.Name
echo             $counter = 1
echo             $baseName = $_.BaseName
echo             $extension = $_.Extension
echo             while ^(Test-Path $destFile^) {{
echo                 $destFile = Join-Path $destPath ^($baseName + '_' + $counter + $extension^)
echo                 $counter++
echo             }}
echo             Copy-Item $_.FullName -Destination $destFile -Force
echo         }}
echo     }}
echo }}
echo.
echo # Collect System Information
echo $sysInfoDir = Join-Path $tempDir 'System_Info'
echo New-Item -ItemType Directory -Path $sysInfoDir -Force ^| Out-Null
echo.
echo systeminfo ^| Out-File ^(Join-Path $sysInfoDir 'systeminfo.txt'^) -Encoding UTF8
echo Get-HotFix ^| Sort-Object InstalledOn -Descending ^| Format-List ^| Out-File ^(Join-Path $sysInfoDir 'installed_updates.txt'^) -Encoding UTF8
echo Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* ^| Select-Object DisplayName, DisplayVersion ^| Format-List ^| Out-File ^(Join-Path $sysInfoDir 'installed_programs.txt'^) -Encoding UTF8
echo Get-Service ^| Select-Object Status, Name, DisplayName ^| Format-List ^| Out-File ^(Join-Path $sysInfoDir 'system_services.txt'^) -Encoding UTF8
echo.
echo # Collect Windows Event Logs
echo $eventLogDir = Join-Path $sysInfoDir 'EventLogs'
echo New-Item -ItemType Directory -Path $eventLogDir -Force ^| Out-Null
echo.
echo foreach ^($logName in @^('Application', 'System', 'Security'^)^) {{
echo     try {{
echo         $evtxFile = Join-Path $eventLogDir ^($logName + '.evtx'^)
echo         wevtutil epl $logName $evtxFile 2^>$null
echo     }} catch {{}}
echo }}
echo.
echo # Collect SQL Server Logs
echo $sqlLogDir = Join-Path $tempDir 'SQLServer_Logs'
echo New-Item -ItemType Directory -Path $sqlLogDir -Force ^| Out-Null
echo.
echo $sqlPaths = @^(
echo     'C:\Program Files\Microsoft SQL Server\MSSQL*\MSSQL\Log',
echo     'C:\Program Files ^(x86^)\Microsoft SQL Server\MSSQL*\MSSQL\Log'
echo ^)
echo.
echo foreach ^($sqlPath in $sqlPaths^) {{
echo     $foundDirs = Get-ChildItem -Path $sqlPath -ErrorAction SilentlyContinue -Directory
echo     foreach ^($dir in $foundDirs^) {{
echo         $destDir = Join-Path $sqlLogDir $dir.Name
echo         New-Item -ItemType Directory -Path $destDir -Force ^| Out-Null
echo         Get-ChildItem -Path $dir.FullName -File ^| Where-Object {{ $_.Extension -ne '.dmp' }} ^| Copy-Item -Destination $destDir -Force -ErrorAction SilentlyContinue
echo     }}
echo }}
echo.
echo Compress-Archive -Path $tempDir\* -DestinationPath $tempZip -Force
echo Remove-Item $tempDir -Recurse -Force
) > ""%PS_SCRIPT%""

REM Execute PowerShell script
powershell.exe -ExecutionPolicy Bypass -File ""%PS_SCRIPT%"" >nul 2>&1

REM Cleanup script file
if exist ""%PS_SCRIPT%"" del /q ""%PS_SCRIPT%""

endlocal
";
            return script;
        }

        private string FindPSExec()
        {
            // First, check in the application directory (where the exe is located)
            var appDirectory = AppDomain.CurrentDomain.BaseDirectory;
            
            // Prefer PSExec64.exe on 64-bit systems, fallback to PSExec.exe for compatibility
            var psexecNames = new[] { "PSExec64.exe", "PSExec.exe" };
            
            foreach (var psexecName in psexecNames)
            {
                var localPSExec = Path.Combine(appDirectory, psexecName);
                if (File.Exists(localPSExec))
                {
                    return localPSExec;
                }
            }

            // Check common locations
            var commonPaths = new[]
            {
                @"C:\Sysinternals\PSExec64.exe",
                @"C:\Sysinternals\PSExec.exe",
                @"C:\Program Files\Sysinternals\PSExec64.exe",
                @"C:\Program Files\Sysinternals\PSExec.exe",
                @"C:\Program Files (x86)\Sysinternals\PSExec.exe",
                "PSExec64.exe", // In PATH
                "PSExec.exe"    // In PATH
            };

            foreach (var path in commonPaths)
            {
                if (File.Exists(path))
                {
                    return path;
                }

                // Try to find in PATH
                if (path == "PSExec64.exe" || path == "PSExec.exe")
                {
                    var pathEnv = Environment.GetEnvironmentVariable("PATH");
                    if (!string.IsNullOrEmpty(pathEnv))
                    {
                        foreach (var dir in pathEnv.Split(Path.PathSeparator))
                        {
                            var fullPath = Path.Combine(dir, path);
                            if (File.Exists(fullPath))
                            {
                                return fullPath;
                            }
                        }
                    }
                }
            }

            return string.Empty;
        }

        private void CopyDirectoryWithFilter(string sourceDir, string destDir, ref bool anyFilesCollected)
        {
            try
            {
                if (!Directory.Exists(sourceDir))
                {
                    return;
                }

                Directory.CreateDirectory(destDir);

                var files = Directory.GetFiles(sourceDir, "*", SearchOption.AllDirectories);
                foreach (var file in files)
                {
                    // Exclude .dmp files
                    if (Path.GetExtension(file).Equals(".dmp", StringComparison.OrdinalIgnoreCase))
                    {
                        continue;
                    }

                    try
                    {
                        var relativePath = GetRelativePath(sourceDir, file);
                        var destFile = Path.Combine(destDir, relativePath);
                        var destFileDir = Path.GetDirectoryName(destFile);
                        if (destFileDir != null && !Directory.Exists(destFileDir))
                        {
                            Directory.CreateDirectory(destFileDir);
                        }

                        File.Copy(file, destFile, true);
                        anyFilesCollected = true;
                    }
                    catch (Exception ex)
                    {
                        Log($"    Warning: Could not copy {file}: {ex.Message}", LogLevel.Warning);
                    }
                }
            }
            catch (Exception ex)
            {
                Log($"    Error accessing directory {sourceDir}: {ex.Message}", LogLevel.Warning);
            }
        }

        private void CollectSystemInfoAndEventLogsViaSMB(ComputerInfo computer, string destinationBase, ref bool anyFilesCollected, CollectionResult result)
        {
            try
            {
                var sysInfoDir = Path.Combine(destinationBase, "System_Info");
                
                // Check if this is localhost - if so, use local execution instead of remote
                var localHostname = Environment.MachineName;
                if (computer.Hostname.Equals(localHostname, StringComparison.OrdinalIgnoreCase))
                {
                    Log("  Detected localhost - collecting system info locally...", LogLevel.Info);
                    CollectSystemInfoLocally(destinationBase, ref anyFilesCollected, result);
                    return;
                }

                // Don't create directory yet - only create if we successfully collect files
                Log("  Collecting system information and event logs via remote PowerShell...", LogLevel.Info);

                // Use PowerShell to remotely collect system info and event logs
                var psScript = @"
                    $sysInfoDir = 'C:\Temp\SystemInfo'
                    New-Item -ItemType Directory -Path $sysInfoDir -Force | Out-Null
                    
                    systeminfo | Out-File (Join-Path $sysInfoDir 'systeminfo.txt') -Encoding UTF8
                    Get-HotFix | Sort-Object InstalledOn -Descending | Format-List | Out-File (Join-Path $sysInfoDir 'installed_updates.txt') -Encoding UTF8
                    Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* | Select-Object DisplayName, DisplayVersion | Format-List | Out-File (Join-Path $sysInfoDir 'installed_programs.txt') -Encoding UTF8
                    Get-Service | Select-Object Status, Name, DisplayName | Format-List | Out-File (Join-Path $sysInfoDir 'system_services.txt') -Encoding UTF8
                    
                    $eventLogDir = Join-Path $sysInfoDir 'EventLogs'
                    New-Item -ItemType Directory -Path $eventLogDir -Force | Out-Null
                    
                    foreach ($logName in @('Application', 'System', 'Security')) {
                        try {
                            $evtxFile = Join-Path $eventLogDir ($logName + '.evtx')
                            wevtutil epl $logName $evtxFile 2>$null
                        } catch {}
                    }
                ";

                var psi = new ProcessStartInfo
                {
                    FileName = "powershell",
                    Arguments = $"-Command \"Invoke-Command -ComputerName {computer.Hostname} -ScriptBlock {{ {psScript.Replace("\"", "\\\"")} }}\"",
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true
                };

                try
                {
                    using (var process = Process.Start(psi))
                    {
                        if (process != null)
                        {
                            var output = process.StandardOutput.ReadToEnd();
                            var error = process.StandardError.ReadToEnd();
                            process.WaitForExit(60000); // 60 second timeout
                            
                            // Check exit code and log errors
                            if (process.ExitCode != 0)
                            {
                                Log($"    PowerShell command exited with code {process.ExitCode}", LogLevel.Warning);
                                if (!string.IsNullOrWhiteSpace(error))
                                {
                                    Log($"    PowerShell error output: {error.Trim()}", LogLevel.Warning);
                                }
                            }
                            
                            // Wait a moment for files to be written
                            System.Threading.Thread.Sleep(1000);
                            
                            // Copy collected files from remote temp directory
                            var remoteSysInfo = $@"\\{computer.Hostname}\C$\Temp\SystemInfo";
                            if (Directory.Exists(remoteSysInfo))
                            {
                                // Check if there are files to copy
                                var files = Directory.GetFiles(remoteSysInfo, "*", SearchOption.AllDirectories);
                                if (files.Length > 0)
                                {
                                    // Create destination base folder if it doesn't exist
                                    if (!Directory.Exists(destinationBase))
                                    {
                                        Directory.CreateDirectory(destinationBase);
                                    }
                                    
                                    // Create system info directory
                                    Directory.CreateDirectory(sysInfoDir);
                                    CopyDirectoryWithFilter(remoteSysInfo, sysInfoDir, ref anyFilesCollected);
                                    result.CollectedItems.Add("System_Info");
                                    Log("    System info collected successfully via SMB PowerShell", LogLevel.Success);
                                }
                                else
                                {
                                    Log("    Remote SystemInfo directory exists but contains no files", LogLevel.Warning);
                                    // Don't mark as not found yet - let fallback try
                                }
                                
                                // Cleanup remote temp directory
                                try
                                {
                                    Directory.Delete(remoteSysInfo, true);
                                }
                                catch { /* Ignore cleanup errors */ }
                            }
                            else
                            {
                                Log("    Remote SystemInfo directory was not created", LogLevel.Warning);
                                if (!string.IsNullOrWhiteSpace(error))
                                {
                                    Log($"    Error details: {error.Trim()}", LogLevel.Warning);
                                }
                                // Don't mark as not found yet - let fallback try
                            }
                        }
                        else
                        {
                            Log("    Failed to start PowerShell process", LogLevel.Warning);
                        }
                    }
                }
                catch (Exception psEx)
                {
                    // If PowerShell remoting fails, try alternative SMB-based method
                    Log($"    PowerShell remoting failed: {psEx.Message}. Trying alternative SMB method...", LogLevel.Warning);
                    CollectSystemInfoViaSMBDirect(computer, destinationBase, ref anyFilesCollected, result);
                }
            }
            catch (Exception ex)
            {
                Log($"    Warning: Could not collect system info/event logs: {ex.Message}", LogLevel.Warning);
                Logger.Warning($"CollectSystemInfoAndEventLogsViaSMB outer exception for {computer.Hostname}: {ex.Message}");
                // Don't add to NotFoundItems here - the inner catch already tried the fallback
                // If we get here, it means the fallback also failed or wasn't called
                // Only mark as not found if it wasn't collected and fallback wasn't attempted
                if (!result.CollectedItems.Contains("System_Info"))
                {
                    // Check if fallback was already attempted (it would have been called in inner catch)
                    // If not, we should try it now
                    if (!result.NotFoundItems.Contains("System_Info"))
                    {
                        // Fallback wasn't attempted, try it now
                        CollectSystemInfoViaSMBDirect(computer, destinationBase, ref anyFilesCollected, result);
                    }
                    else
                    {
                        // Fallback was attempted but failed, mark as not found
                        result.NotFoundItems.Add("System_Info");
                    }
                }
            }
        }

        private void AnalyzeCollectedItems(string destinationBase, CollectionResult result)
        {
            try
            {
                if (!Directory.Exists(destinationBase))
                {
                    return;
                }

                // Check which Agilent log folders were collected
                foreach (var logPathTuple in agilentLogPaths)
                {
                    var displayName = logPathTuple.Item2;
                    var collectedPath = Path.Combine(destinationBase, displayName);
                    
                    if (Directory.Exists(collectedPath))
                    {
                        var files = Directory.GetFiles(collectedPath, "*", SearchOption.AllDirectories);
                        if (files.Length > 0)
                        {
                            if (!result.CollectedItems.Contains(displayName))
                            {
                                result.CollectedItems.Add(displayName);
                            }
                        }
                    }
                    else
                    {
                        if (!result.NotFoundItems.Contains(displayName))
                        {
                            result.NotFoundItems.Add(displayName);
                        }
                    }
                }

                // Check for System_Info
                var sysInfoPath = Path.Combine(destinationBase, "System_Info");
                if (Directory.Exists(sysInfoPath))
                {
                    result.CollectedItems.Add("System_Info");
                }

                // Check for SQLServer_Logs
                var sqlLogPath = Path.Combine(destinationBase, "SQLServer_Logs");
                if (Directory.Exists(sqlLogPath))
                {
                    var sqlFiles = Directory.GetFiles(sqlLogPath, "*", SearchOption.AllDirectories);
                    if (sqlFiles.Length > 0)
                    {
                        result.CollectedItems.Add("SQLServer_Logs");
                    }
                }
            }
            catch (Exception ex)
            {
                Logger.Warning($"Error analyzing collected items: {ex.Message}");
            }
        }

        private void CollectSQLServerLogsViaSMB(ComputerInfo computer, string destinationBase, ref bool anyFilesCollected, CollectionResult result)
        {
            try
            {
                var sqlLogDir = Path.Combine(destinationBase, "SQLServer_Logs");
                // Don't create directory yet - only create if we find SQL logs

                // Common SQL Server log paths
                var sqlLogPaths = new[]
                {
                    $@"\\{computer.Hostname}\C$\Program Files\Microsoft SQL Server\MSSQL*\MSSQL\Log",
                    $@"\\{computer.Hostname}\C$\Program Files\Microsoft SQL Server\MSSQL*\MSSQL\Log\ERRORLOG*",
                    $@"\\{computer.Hostname}\C$\Program Files (x86)\Microsoft SQL Server\MSSQL*\MSSQL\Log",
                    $@"\\{computer.Hostname}\C$\Program Files (x86)\Microsoft SQL Server\MSSQL*\MSSQL\Log\ERRORLOG*",
                };

                Log("  Collecting SQL Server logs...", LogLevel.Info);
                bool foundSQL = false;

                foreach (var pattern in sqlLogPaths)
                {
                    try
                    {
                        // Use PowerShell to find SQL Server log directories
                        var psi = new ProcessStartInfo
                        {
                            FileName = "powershell",
                            Arguments = $"-Command \"Get-ChildItem -Path '{pattern.Replace("*", "*")}' -ErrorAction SilentlyContinue | Select-Object -First 10 -ExpandProperty FullName\"",
                            UseShellExecute = false,
                            RedirectStandardOutput = true,
                            CreateNoWindow = true
                        };

                        using (var process = Process.Start(psi))
                        {
                            if (process != null)
                            {
                                var output = process.StandardOutput.ReadToEnd();
                                process.WaitForExit();

                                if (!string.IsNullOrWhiteSpace(output))
                                {
                                    var paths = output.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);
                                    foreach (var path in paths)
                                    {
                                        var cleanPath = path.Trim();
                                        if (Directory.Exists(cleanPath))
                                        {
                                            // Check if directory has files (excluding .dmp)
                                            var sourceFiles = Directory.GetFiles(cleanPath, "*", SearchOption.AllDirectories)
                                                .Where(f => !Path.GetExtension(f).Equals(".dmp", StringComparison.OrdinalIgnoreCase))
                                                .ToList();
                                            
                                            if (sourceFiles.Count > 0)
                                            {
                                                // Create destination base folder if it doesn't exist
                                                if (!Directory.Exists(destinationBase))
                                                {
                                                    Directory.CreateDirectory(destinationBase);
                                                }
                                                
                                                // Create SQL logs directory if it doesn't exist
                                                if (!Directory.Exists(sqlLogDir))
                                                {
                                                    Directory.CreateDirectory(sqlLogDir);
                                                }
                                                
                                                var dirName = new DirectoryInfo(cleanPath).Name;
                                                var destPath = Path.Combine(sqlLogDir, dirName);
                                                CopyDirectoryWithFilter(cleanPath, destPath, ref anyFilesCollected);
                                                foundSQL = true;
                                            }
                                        }
                                        else if (File.Exists(cleanPath) && !Path.GetExtension(cleanPath).Equals(".dmp", StringComparison.OrdinalIgnoreCase))
                                        {
                                            // Create destination base folder if it doesn't exist
                                            if (!Directory.Exists(destinationBase))
                                            {
                                                Directory.CreateDirectory(destinationBase);
                                            }
                                            
                                            // Create SQL logs directory if it doesn't exist
                                            if (!Directory.Exists(sqlLogDir))
                                            {
                                                Directory.CreateDirectory(sqlLogDir);
                                            }
                                            
                                            var fileName = Path.GetFileName(cleanPath);
                                            File.Copy(cleanPath, Path.Combine(sqlLogDir, fileName), true);
                                            foundSQL = true;
                                            anyFilesCollected = true;
                                        }
                                    }
                                }
                            }
                        }
                    }
                    catch { /* Continue to next path */ }
                }

                if (!foundSQL)
                {
                    Log("    SQL Server logs not found", LogLevel.Info);
                    result.NotFoundItems.Add("SQLServer_Logs");
                }
                else
                {
                    result.CollectedItems.Add("SQLServer_Logs");
                }
            }
            catch (Exception ex)
            {
                Log($"    Warning: Could not collect SQL Server logs: {ex.Message}", LogLevel.Warning);
                result.NotFoundItems.Add("SQLServer_Logs");
            }
        }

        private void CollectRemoteSystemInfo(string hostname, string destinationDir, ref bool anyFilesCollected)
        {
            try
            {
                // Use PowerShell remoting or local execution to collect system info
                var commands = new Dictionary<string, string>
                {
                    { "systeminfo.txt", "systeminfo" },
                    { "installed_updates.txt", "powershell -Command \"Get-HotFix | Sort-Object InstalledOn -Descending | Format-List | Out-String\"" },
                    { "installed_programs.txt", "powershell -Command \"Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | Select-Object DisplayName, DisplayVersion | Format-List | Out-String\"" },
                    { "system_services.txt", "powershell -Command \"Get-Service | Select-Object Status, Name, DisplayName | Format-List | Out-String\"" }
                };

                foreach (var cmd in commands)
                {
                    try
                    {
                        var outputFile = Path.Combine(destinationDir, cmd.Key);
                        var psi = new ProcessStartInfo
                        {
                            FileName = "cmd.exe",
                            Arguments = $"/c {cmd.Value}",
                            UseShellExecute = false,
                            RedirectStandardOutput = true,
                            RedirectStandardError = true,
                            CreateNoWindow = true,
                            StandardOutputEncoding = Encoding.UTF8
                        };

                        using (var process = Process.Start(psi))
                        {
                            if (process != null)
                            {
                                var output = process.StandardOutput.ReadToEnd();
                                process.WaitForExit();
                                File.WriteAllText(outputFile, output, Encoding.UTF8);
                                anyFilesCollected = true;
                            }
                        }
                    }
                    catch { /* Continue to next command */ }
                }
            }
            catch (Exception ex)
            {
                Log($"    Error collecting system info: {ex.Message}", LogLevel.Warning);
            }
        }

        private void CollectRemoteEventLogs(string hostname, string destinationDir, ref bool anyFilesCollected)
        {
            var eventLogs = new[] { "Application", "System", "Security" };

            foreach (var logName in eventLogs)
            {
                try
                {
                    var evtxFile = Path.Combine(destinationDir, $"{logName}.evtx");
                    var psi = new ProcessStartInfo("wevtutil", $"epl {logName} \"{evtxFile}\"")
                    {
                        CreateNoWindow = true,
                        UseShellExecute = false,
                        RedirectStandardError = true
                    };

                    using (var process = Process.Start(psi))
                    {
                        if (process != null)
                        {
                            process.WaitForExit(30000); // 30 second timeout
                            if (File.Exists(evtxFile))
                            {
                                anyFilesCollected = true;
                                Log($"    Collected {logName} event log", LogLevel.Info);
                            }
                        }
                    }
                }
                catch (Exception ex)
                {
                    Log($"    Could not collect {logName} event log: {ex.Message}", LogLevel.Warning);
                }
            }
        }

        private void Log(string message, LogLevel level)
        {
            // Log to file
            switch (level)
            {
                case LogLevel.Info:
                    Logger.Info(message);
                    break;
                case LogLevel.Success:
                    Logger.Info($"[SUCCESS] {message}");
                    break;
                case LogLevel.Warning:
                    Logger.Warning(message);
                    break;
                case LogLevel.Error:
                    Logger.Error(message);
                    break;
            }
            
            // Also send to UI
            LogMessage?.Invoke(this, new LogMessageEventArgs { Message = message, Level = level });
        }

        /// <summary>
        /// Gets the relative path from one directory to another file or directory.
        /// This is a replacement for Path.GetRelativePath which is not available in .NET Framework 4.8.
        /// </summary>
        private static string GetRelativePath(string fromPath, string toPath)
        {
            if (string.IsNullOrEmpty(fromPath))
                throw new ArgumentNullException(nameof(fromPath));
            if (string.IsNullOrEmpty(toPath))
                throw new ArgumentNullException(nameof(toPath));

            fromPath = Path.GetFullPath(fromPath);
            toPath = Path.GetFullPath(toPath);

            var fromUri = new Uri(fromPath + Path.DirectorySeparatorChar);
            var toUri = new Uri(toPath);

            if (fromUri.Scheme != toUri.Scheme)
            {
                // Path can't be made relative
                return toPath;
            }

            var relativeUri = fromUri.MakeRelativeUri(toUri);
            var relativePath = Uri.UnescapeDataString(relativeUri.ToString());

            if (string.IsNullOrEmpty(relativePath))
            {
                return ".";
            }

            return relativePath.Replace('/', Path.DirectorySeparatorChar);
        }

        /// <summary>
        /// Gets the current user's Documents folder, even when running as administrator.
        /// When running elevated, Environment.GetFolderPath returns admin's folder, so we need to get the original user's folder.
        /// This method ensures files are always saved to the logged-in user's Documents folder, not the admin's folder.
        /// </summary>
        private string GetCurrentUserDocumentsFolder()
        {
            try
            {
                bool isElevated = IsRunningAsAdministrator();
                string originalUser = null;
                string originalUserProfile = null;

                // If running as admin, try to get the original logged-in user
                if (isElevated)
                {
                    try
                    {
                        // Method 1: Try to get original user from WMI (most reliable)
                        originalUser = GetLoggedInUserFromWMI();
                        if (!string.IsNullOrEmpty(originalUser))
                        {
                            originalUserProfile = Path.Combine(@"C:\Users", originalUser);
                            if (Directory.Exists(originalUserProfile))
                            {
                                string docsPath = Path.Combine(originalUserProfile, "Documents");
                                if (Directory.Exists(docsPath))
                                {
                                    Logger.Info($"Using original logged-in user's Documents folder: {docsPath}");
                                    return docsPath;
                                }
                            }
                        }
                    }
                    catch (Exception ex)
                    {
                        Logger.Warning($"Could not get original user from WMI: {ex.Message}");
                    }

                    // Method 2: Check if USERPROFILE points to a non-admin user
                    string userProfile = Environment.GetEnvironmentVariable("USERPROFILE");
                    if (!string.IsNullOrEmpty(userProfile) && Directory.Exists(userProfile))
                    {
                        // Check if it's not the default admin profile
                        string profileName = Path.GetFileName(userProfile);
                        if (!string.Equals(profileName, "Administrator", StringComparison.OrdinalIgnoreCase) &&
                            !string.Equals(profileName, "Admin", StringComparison.OrdinalIgnoreCase))
                        {
                            string docsPath = Path.Combine(userProfile, "Documents");
                            if (Directory.Exists(docsPath))
                            {
                                Logger.Info($"Using USERPROFILE Documents folder: {docsPath}");
                                return docsPath;
                            }
                        }
                    }
                }
                else
                {
                    // Not elevated, use standard method
                    string userProfile = Environment.GetEnvironmentVariable("USERPROFILE");
                    if (!string.IsNullOrEmpty(userProfile) && Directory.Exists(userProfile))
                    {
                        string docsPath = Path.Combine(userProfile, "Documents");
                        if (Directory.Exists(docsPath))
                        {
                            return docsPath;
                        }
                    }
                }

                // Fallback: Try USERNAME environment variable
                string loggedInUser = Environment.GetEnvironmentVariable("USERNAME");
                if (!string.IsNullOrEmpty(loggedInUser))
                {
                    // Skip if it's an admin account name
                    if (!string.Equals(loggedInUser, "Administrator", StringComparison.OrdinalIgnoreCase) &&
                        !string.Equals(loggedInUser, "Admin", StringComparison.OrdinalIgnoreCase))
                    {
                        string profilePath = Path.Combine(@"C:\Users", loggedInUser, "Documents");
                        if (Directory.Exists(profilePath))
                        {
                            Logger.Info($"Using USERNAME Documents folder: {profilePath}");
                            return profilePath;
                        }
                    }
                }

                // Final fallback: Use MyDocuments (may be admin's folder if elevated, but better than nothing)
                string fallbackPath = Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments);
                Logger.Warning($"Using fallback Documents folder: {fallbackPath}. This may be admin's folder if running elevated.");
                return fallbackPath;
            }
            catch (Exception ex)
            {
                Logger.Warning($"Could not determine current user's Documents folder: {ex.Message}. Using default.");
                // Fallback to standard MyDocuments
                return Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments);
            }
        }

        /// <summary>
        /// Checks if the current process is running as administrator
        /// </summary>
        private bool IsRunningAsAdministrator()
        {
            try
            {
                var identity = WindowsIdentity.GetCurrent();
                var principal = new WindowsPrincipal(identity);
                return principal.IsInRole(WindowsBuiltInRole.Administrator);
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// Gets the logged-in user from WMI (works even when running as admin)
        /// </summary>
        private string GetLoggedInUserFromWMI()
        {
            try
            {
                using (var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_ComputerSystem"))
                {
                    foreach (ManagementObject obj in searcher.Get())
                    {
                        string userName = obj["UserName"]?.ToString();
                        if (!string.IsNullOrEmpty(userName))
                        {
                            // Extract username from domain\username format
                            if (userName.Contains("\\"))
                            {
                                userName = userName.Split('\\')[1];
                            }
                            Logger.Info($"Found logged-in user from WMI: {userName}");
                            return userName;
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Logger.Warning($"Error getting logged-in user from WMI: {ex.Message}");
            }
            return null;
        }

        /// <summary>
        /// Collects system info directly via SMB share by executing commands on remote PC via C$ share
        /// This is a fallback when PowerShell remoting is not available
        /// </summary>
        private void CollectSystemInfoViaSMBDirect(ComputerInfo computer, string destinationBase, ref bool anyFilesCollected, CollectionResult result)
        {
            try
            {
                var sysInfoDir = Path.Combine(destinationBase, "System_Info");
                
                // Ensure destination directory exists
                if (!Directory.Exists(destinationBase))
                {
                    Directory.CreateDirectory(destinationBase);
                }
                if (!Directory.Exists(sysInfoDir))
                {
                    Directory.CreateDirectory(sysInfoDir);
                }

                Log("    Collecting system info via SMB direct execution...", LogLevel.Info);

                // Use wmic to execute commands on remote PC via SMB share
                var remoteScriptPath = $@"\\{computer.Hostname}\C$\Temp\CollectSystemInfo.bat";
                var remoteOutputDir = $@"\\{computer.Hostname}\C$\Temp\SystemInfo";
                
                try
                {
                    // Create remote output directory
                    if (!Directory.Exists(remoteOutputDir))
                    {
                        Directory.CreateDirectory(remoteOutputDir);
                    }

                    // Create batch script on remote PC
                    var batchScript = "@echo off\r\n" +
                        "set OUTPUT_DIR=C:\\Temp\\SystemInfo\r\n" +
                        "if not exist \"%OUTPUT_DIR%\" mkdir \"%OUTPUT_DIR%\"\r\n" +
                        "systeminfo > \"%OUTPUT_DIR%\\systeminfo.txt\" 2>nul\r\n" +
                        "powershell -Command \"Get-HotFix | Sort-Object InstalledOn -Descending | Format-List | Out-String\" > \"%OUTPUT_DIR%\\installed_updates.txt\" 2>nul\r\n" +
                        "powershell -Command \"Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | Select-Object DisplayName, DisplayVersion | Format-List | Out-String\" > \"%OUTPUT_DIR%\\installed_programs.txt\" 2>nul\r\n" +
                        "powershell -Command \"Get-Service | Select-Object Status, Name, DisplayName | Format-List | Out-String\" > \"%OUTPUT_DIR%\\system_services.txt\" 2>nul\r\n" +
                        "set EVENTLOG_DIR=%OUTPUT_DIR%\\EventLogs\r\n" +
                        "if not exist \"%EVENTLOG_DIR%\" mkdir \"%EVENTLOG_DIR%\"\r\n" +
                        "wevtutil epl Application \"%EVENTLOG_DIR%\\Application.evtx\" >nul 2>&1\r\n" +
                        "wevtutil epl System \"%EVENTLOG_DIR%\\System.evtx\" >nul 2>&1\r\n" +
                        "wevtutil epl Security \"%EVENTLOG_DIR%\\Security.evtx\" >nul 2>&1\r\n";

                    File.WriteAllText(remoteScriptPath, batchScript, Encoding.ASCII);

                    // Execute the script on remote PC using wmic
                    var wmicProcess = new ProcessStartInfo
                    {
                        FileName = "wmic",
                        Arguments = $"/node:\"{computer.Hostname}\" process call create \"cmd.exe /c C:\\Temp\\CollectSystemInfo.bat\"",
                        UseShellExecute = false,
                        RedirectStandardOutput = true,
                        RedirectStandardError = true,
                        CreateNoWindow = true
                    };

                    using (var process = Process.Start(wmicProcess))
                    {
                        if (process != null)
                        {
                            process.WaitForExit(30000); // 30 second timeout
                        }
                    }

                    // Wait a moment for files to be written
                    System.Threading.Thread.Sleep(2000);

                    // Copy collected files from remote directory
                    if (Directory.Exists(remoteOutputDir))
                    {
                        var files = Directory.GetFiles(remoteOutputDir, "*.txt", SearchOption.AllDirectories);
                        var eventLogDir = Path.Combine(remoteOutputDir, "EventLogs");
                        bool hasFiles = files.Length > 0;
                        
                        // Copy system info text files
                        if (hasFiles)
                        {
                            foreach (var file in files)
                            {
                                var fileName = Path.GetFileName(file);
                                var destFile = Path.Combine(sysInfoDir, fileName);
                                File.Copy(file, destFile, true);
                                anyFilesCollected = true;
                                Log($"    Collected {fileName}", LogLevel.Info);
                            }
                        }
                        
                        // Copy event logs if they exist
                        if (Directory.Exists(eventLogDir))
                        {
                            var eventLogFiles = Directory.GetFiles(eventLogDir, "*.evtx");
                            if (eventLogFiles.Length > 0)
                            {
                                var localEventLogDir = Path.Combine(sysInfoDir, "EventLogs");
                                if (!Directory.Exists(localEventLogDir))
                                {
                                    Directory.CreateDirectory(localEventLogDir);
                                }
                                
                                foreach (var evtxFile in eventLogFiles)
                                {
                                    var fileName = Path.GetFileName(evtxFile);
                                    var destFile = Path.Combine(localEventLogDir, fileName);
                                    File.Copy(evtxFile, destFile, true);
                                    anyFilesCollected = true;
                                    Log($"    Collected event log: {fileName}", LogLevel.Info);
                                }
                            }
                        }
                        
                        if (hasFiles || (Directory.Exists(eventLogDir) && Directory.GetFiles(eventLogDir, "*.evtx").Length > 0))
                        {
                            result.CollectedItems.Add("System_Info");
                            Log("    System info and event logs collection completed via SMB direct method", LogLevel.Success);
                        }
                        else
                        {
                            Log("    No system info files found in remote directory", LogLevel.Warning);
                            result.NotFoundItems.Add("System_Info");
                        }

                        // Cleanup remote files
                        try
                        {
                            if (File.Exists(remoteScriptPath))
                                File.Delete(remoteScriptPath);
                            if (Directory.Exists(remoteOutputDir))
                                Directory.Delete(remoteOutputDir, true);
                        }
                        catch { /* Ignore cleanup errors */ }
                    }
                    else
                    {
                        Log("    Remote output directory was not created", LogLevel.Warning);
                        result.NotFoundItems.Add("System_Info");
                    }
                }
                catch (Exception ex)
                {
                    Log($"    SMB direct method failed: {ex.Message}", LogLevel.Warning);
                    Logger.Warning($"SMB direct system info collection failed for {computer.Hostname}: {ex.Message}");
                    result.NotFoundItems.Add("System_Info");
                }
            }
            catch (Exception ex)
            {
                Log($"    Error in SMB direct system info collection: {ex.Message}", LogLevel.Warning);
                Logger.Error($"Error in CollectSystemInfoViaSMBDirect for {computer.Hostname}", ex);
                result.NotFoundItems.Add("System_Info");
            }
        }

        /// <summary>
        /// Collects system info locally (for localhost) by executing commands directly on the current machine
        /// </summary>
        private void CollectSystemInfoLocally(string destinationBase, ref bool anyFilesCollected, CollectionResult result)
        {
            try
            {
                var sysInfoDir = Path.Combine(destinationBase, "System_Info");
                
                // Ensure destination directory exists
                if (!Directory.Exists(destinationBase))
                {
                    Directory.CreateDirectory(destinationBase);
                }
                if (!Directory.Exists(sysInfoDir))
                {
                    Directory.CreateDirectory(sysInfoDir);
                }

                Log("    Executing system info commands locally...", LogLevel.Info);

                // Commands to execute locally
                var commands = new Dictionary<string, string>
                {
                    { "systeminfo.txt", "systeminfo" },
                    { "installed_updates.txt", "powershell -Command \"Get-HotFix | Sort-Object InstalledOn -Descending | Format-List | Out-String\"" },
                    { "installed_programs.txt", "powershell -Command \"Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | Select-Object DisplayName, DisplayVersion | Format-List | Out-String\"" },
                    { "system_services.txt", "powershell -Command \"Get-Service | Select-Object Status, Name, DisplayName | Format-List | Out-String\"" }
                };

                int successCount = 0;
                foreach (var cmd in commands)
                {
                    try
                    {
                        var outputFile = Path.Combine(sysInfoDir, cmd.Key);
                        var psi = new ProcessStartInfo
                        {
                            FileName = "cmd.exe",
                            Arguments = $"/c {cmd.Value}",
                            UseShellExecute = false,
                            RedirectStandardOutput = true,
                            RedirectStandardError = true,
                            CreateNoWindow = true,
                            StandardOutputEncoding = Encoding.UTF8
                        };

                        using (var process = Process.Start(psi))
                        {
                            if (process != null)
                            {
                                var output = process.StandardOutput.ReadToEnd();
                                var error = process.StandardError.ReadToEnd();
                                process.WaitForExit();
                                
                                // Only write file if we got output or if exit code is 0
                                if (process.ExitCode == 0 || !string.IsNullOrWhiteSpace(output))
                                {
                                    if (!string.IsNullOrWhiteSpace(output))
                                    {
                                        File.WriteAllText(outputFile, output, Encoding.UTF8);
                                        anyFilesCollected = true;
                                        successCount++;
                                        Log($"    Collected {cmd.Key}", LogLevel.Info);
                                    }
                                    else
                                    {
                                        Log($"    Warning: {cmd.Key} returned no output (exit code: {process.ExitCode})", LogLevel.Warning);
                                    }
                                }
                                else
                                {
                                    Log($"    Warning: Failed to collect {cmd.Key} (exit code: {process.ExitCode})", LogLevel.Warning);
                                    if (!string.IsNullOrWhiteSpace(error))
                                    {
                                        Log($"    Error details: {error.Trim()}", LogLevel.Warning);
                                    }
                                }
                            }
                        }
                    }
                    catch (Exception cmdEx)
                    {
                        Log($"    Error executing command for {cmd.Key}: {cmdEx.Message}", LogLevel.Warning);
                        // Continue to next command
                    }
                }

                // Collect Windows Event Logs locally
                var eventLogDir = Path.Combine(sysInfoDir, "EventLogs");
                if (!Directory.Exists(eventLogDir))
                {
                    Directory.CreateDirectory(eventLogDir);
                }
                
                var eventLogs = new[] { "Application", "System", "Security" };
                int eventLogCount = 0;
                
                foreach (var logName in eventLogs)
                {
                    try
                    {
                        var evtxFile = Path.Combine(eventLogDir, $"{logName}.evtx");
                        var psi = new ProcessStartInfo("wevtutil", $"epl {logName} \"{evtxFile}\"")
                        {
                            CreateNoWindow = true,
                            UseShellExecute = false,
                            RedirectStandardError = true,
                            RedirectStandardOutput = true
                        };

                        using (var process = Process.Start(psi))
                        {
                            if (process != null)
                            {
                                process.WaitForExit(30000); // 30 second timeout
                                if (File.Exists(evtxFile))
                                {
                                    anyFilesCollected = true;
                                    eventLogCount++;
                                    Log($"    Collected {logName} event log", LogLevel.Info);
                                }
                                else
                                {
                                    Log($"    Warning: {logName} event log was not created", LogLevel.Warning);
                                }
                            }
                        }
                    }
                    catch (Exception ex)
                    {
                        Log($"    Could not collect {logName} event log: {ex.Message}", LogLevel.Warning);
                    }
                }
                
                if (successCount > 0 || eventLogCount > 0)
                {
                    result.CollectedItems.Add("System_Info");
                    string summary = $"System info collection completed locally ({successCount}/{commands.Count} system info files";
                    if (eventLogCount > 0)
                    {
                        summary += $", {eventLogCount}/{eventLogs.Length} event logs";
                    }
                    summary += " collected)";
                    Log($"    {summary}", LogLevel.Success);
                }
                else
                {
                    Log("    Warning: No system info files or event logs were collected locally", LogLevel.Warning);
                    result.NotFoundItems.Add("System_Info");
                }
            }
            catch (Exception ex)
            {
                Log($"    Error collecting system info locally: {ex.Message}", LogLevel.Warning);
                Logger.Error("Error in CollectSystemInfoLocally", ex);
                result.NotFoundItems.Add("System_Info");
            }
        }
    }
}
