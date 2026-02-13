using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Management;
using System.Net;
using System.Net.NetworkInformation;
using System.Reflection;
using System.Security.Principal;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace Remotecollect
{
    public partial class MainForm : Form
    {
        private CheckedListBox checkedListBoxPCs;
        private Button btnScanDomain;
        private Button btnCollectLogs;
        private ProgressBar progressBar;
        private RichTextBox richTextBoxConsole;
        private Label lblStatus;
        private ListBox listBoxResults;
        private Label lblResults;
        private DomainScanner domainScanner;
        private LogCollectorService logCollectorService;
        private List<ComputerInfo> discoveredComputers;
        private List<CollectionResult> collectionResults;
        private TextBox txtManualPC;
        private Button btnAddPC;
        private MenuStrip menuStrip;

        public MainForm()
        {
            try
            {
                Logger.Info("MainForm constructor started");
                InitializeComponent();
                Logger.Info("UI components initialized");
                
                domainScanner = new DomainScanner();
                logCollectorService = new LogCollectorService();
                discoveredComputers = new List<ComputerInfo>();
                collectionResults = new List<CollectionResult>();
                logCollectorService.LogMessage += OnLogMessage;
                
                Logger.Info("MainForm constructor completed successfully");
                Logger.Info($"Log file location: {Logger.GetLogFilePath()}");
                
                // Try to load saved scan results
                LoadSavedScanResults();

                // Ensure localhost (current PC) is always available in the list
                EnsureLocalhostInList();

                // Show log file location in status
                lblStatus.Text = $"Ready - Log: {Path.GetFileName(Logger.GetLogFilePath())}";
            }
            catch (Exception ex)
            {
                Logger.Error("Fatal error in MainForm constructor", ex);
                MessageBox.Show(
                    $"Failed to initialize application:\n\n{ex.Message}\n\n" +
                    $"Log file: {Logger.GetLogFilePath()}",
                    "Initialization Error",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                );
                throw;
            }
        }

        private void InitializeComponent()
        {
            try
            {
                Logger.Debug("Initializing UI components...");
                
                this.Text = "Multi-Method Remote Log Collector (Admin Tool)";
                this.Size = new Size(1000, 700);
                this.StartPosition = FormStartPosition.CenterScreen;
                this.MinimumSize = new Size(800, 600);
                
                // Set application icon from embedded resources (no separate file needed)
                try
                {
                    // Try to load from embedded resources (icon is embedded in EXE)
                    var assembly = System.Reflection.Assembly.GetExecutingAssembly();
                    var resourceNames = assembly.GetManifestResourceNames();
                    
                    // Try different possible resource names
                    string iconResourceName = null;
                    foreach (var name in resourceNames)
                    {
                        if (name.Contains("log8.ico") || name.EndsWith(".log8.ico"))
                        {
                            iconResourceName = name;
                            break;
                        }
                    }
                    
                    if (iconResourceName != null)
                    {
                        using (var iconStream = assembly.GetManifestResourceStream(iconResourceName))
                        {
                            if (iconStream != null)
                            {
                                this.Icon = new Icon(iconStream);
                            }
                        }
                    }
                    else
                    {
                        // Fallback: try loading from file in same directory (for development/testing)
                        var iconPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "log8.ico");
                        if (File.Exists(iconPath))
                        {
                            this.Icon = new Icon(iconPath);
                        }
                    }
                }
                catch (Exception ex)
                {
                    Logger.Warning($"Could not load application icon: {ex.Message}");
                    // Continue without icon if file doesn't exist or is invalid
                }
                
                // Add form load event to ensure visibility
                this.Load += MainForm_Load;
                this.Shown += MainForm_Shown;

            // Create MenuStrip with Help menu
            menuStrip = new MenuStrip();
            
            var helpMenu = new ToolStripMenuItem("Help");
            
            var aboutMenuItem = new ToolStripMenuItem("About...");
            aboutMenuItem.Click += AboutMenuItem_Click;
            helpMenu.DropDownItems.Add(aboutMenuItem);
            
            helpMenu.DropDownItems.Add(new ToolStripSeparator());
            
            var userGuideEnMenuItem = new ToolStripMenuItem("User Guide (English)");
            userGuideEnMenuItem.Click += (s, e) => UserGuideMenuItem_Click(s, e, "EN");
            helpMenu.DropDownItems.Add(userGuideEnMenuItem);
            
            var userGuideCnMenuItem = new ToolStripMenuItem("User Guide (中文)");
            userGuideCnMenuItem.Click += (s, e) => UserGuideMenuItem_Click(s, e, "CN");
            helpMenu.DropDownItems.Add(userGuideCnMenuItem);
            
            menuStrip.Items.Add(helpMenu);
            this.MainMenuStrip = menuStrip;
            this.Controls.Add(menuStrip);

            // Left column fixed width
            const int leftColumnWidth = 400;
            const int leftMargin = 12;
            const int columnGap = 18;
            const int rightColumnStartX = leftMargin + leftColumnWidth + columnGap;

            // Menu strip takes about 24 pixels at the top, so adjust all Y positions
            const int menuStripHeight = 24;
            const int topOffset = menuStripHeight + 5;

            // Manual PC input controls (hostname or IP) - positioned below buttons
            var lblManualPC = new Label
            {
                Text = "Manual PC (hostname or IP):",
                Location = new Point(leftMargin, topOffset + 43),
                Size = new Size(leftColumnWidth, 20),
                Anchor = AnchorStyles.Top | AnchorStyles.Left
            };

            txtManualPC = new TextBox
            {
                Location = new Point(leftMargin, topOffset + 65),
                Size = new Size(leftColumnWidth - 100, 22),
                Anchor = AnchorStyles.Top | AnchorStyles.Left
            };

            btnAddPC = new Button
            {
                Text = "Add PC",
                Location = new Point(leftMargin + leftColumnWidth - 90, topOffset + 63),
                Size = new Size(90, 26),
                Anchor = AnchorStyles.Top | AnchorStyles.Left
            };
            btnAddPC.Click += BtnAddPC_Click;

            // CheckedListBox for PCs - fixed width, expands vertically, anchored top/bottom/left
            // Placed below manual input and buttons
            checkedListBoxPCs = new CheckedListBox
            {
                Location = new Point(leftMargin, topOffset + 98),
                Size = new Size(leftColumnWidth, 290),
                Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left,
                CheckOnClick = true
            };

            // Results Label - fixed width, anchored bottom/left
            // Moved down to account for menu strip (24px) plus one more row
            lblResults = new Label
            {
                Text = "Collection Results:",
                Location = new Point(leftMargin, 430),
                Size = new Size(leftColumnWidth, 20),
                Anchor = AnchorStyles.Bottom | AnchorStyles.Left
            };

            // Results ListBox - fixed width, anchored bottom/left
            // Moved down to account for menu strip (24px) plus one more row
            listBoxResults = new ListBox
            {
                Location = new Point(leftMargin, 455),
                Size = new Size(leftColumnWidth, 125),
                Anchor = AnchorStyles.Bottom | AnchorStyles.Left,
                Font = new Font("Consolas", 8),
                HorizontalScrollbar = true
            };

            // Scan Domain Button - fixed position at top
            btnScanDomain = new Button
            {
                Text = "Scan Domain",
                Location = new Point(leftMargin, topOffset),
                Size = new Size(120, 35),
                UseVisualStyleBackColor = true,
                Anchor = AnchorStyles.Top | AnchorStyles.Left
            };
            btnScanDomain.Click += BtnScanDomain_Click;

            // Collect Logs Button - fixed position at top
            btnCollectLogs = new Button
            {
                Text = "Collect Logs",
                Location = new Point(leftMargin + 130, topOffset),
                Size = new Size(120, 35),
                UseVisualStyleBackColor = true,
                Enabled = false,
                Anchor = AnchorStyles.Top | AnchorStyles.Left
            };
            btnCollectLogs.Click += BtnCollectLogs_Click;

            // Progress Bar - expands with form width (constrained by Resize handler)
            progressBar = new ProgressBar
            {
                Location = new Point(rightColumnStartX, topOffset),
                Size = new Size(550, 23),
                Anchor = AnchorStyles.Top | AnchorStyles.Left,
                Style = ProgressBarStyle.Continuous
            };

            // Status Label - expands with form width (constrained by Resize handler)
            lblStatus = new Label
            {
                Text = "Ready",
                Location = new Point(rightColumnStartX, topOffset + 28),
                Size = new Size(550, 20),
                Anchor = AnchorStyles.Top | AnchorStyles.Left
            };

            // Console RichTextBox - expands with form width and height (constrained by Resize handler)
            richTextBoxConsole = new RichTextBox
            {
                Location = new Point(rightColumnStartX, topOffset + 53),
                Size = new Size(550, 495),
                Anchor = AnchorStyles.Top | AnchorStyles.Left,
                Font = new Font("Consolas", 9),
                ReadOnly = true,
                BackColor = Color.Black,
                ForeColor = Color.LimeGreen
            };

                // Add controls to form
                this.Controls.Add(checkedListBoxPCs);
                this.Controls.Add(btnScanDomain);
                this.Controls.Add(btnCollectLogs);
                this.Controls.Add(progressBar);
                this.Controls.Add(lblStatus);
                this.Controls.Add(richTextBoxConsole);
            this.Controls.Add(lblManualPC);
            this.Controls.Add(txtManualPC);
            this.Controls.Add(btnAddPC);
            this.Controls.Add(lblResults);
            this.Controls.Add(listBoxResults);
                
                // Handle form resize to constrain right column width for better readability
                this.Resize += MainForm_Resize;
                
                Logger.Debug("All UI controls added to form");
            }
            catch (Exception ex)
            {
                Logger.Error("Error in InitializeComponent", ex);
                throw;
            }
        }

        private async void BtnScanDomain_Click(object sender, EventArgs e)
        {
            try
            {
                Logger.Info("Scan Domain button clicked");
                btnScanDomain.Enabled = false;
                btnCollectLogs.Enabled = false;
                checkedListBoxPCs.Items.Clear();
                discoveredComputers.Clear();
                progressBar.Maximum = 100; // Ensure Maximum is set before setting Value
                progressBar.Value = 0;
                progressBar.Style = ProgressBarStyle.Marquee;

                LogMessage("Starting domain scan...", LogLevel.Info);
                Logger.Info("Starting domain scan operation");

                string domainScanError = null;
                await Task.Run(() =>
                {
                    try
                    {
                        discoveredComputers = domainScanner.ScanDomain();
                    }
                    catch (Exception scanEx)
                    {
                        // Log the error but don't throw - we still want localhost to be available
                        domainScanError = scanEx.Message;
                        Logger.Warning($"Domain scan failed, but continuing with localhost only: {scanEx.Message}");
                        // Clear discovered computers - we'll only have localhost
                        discoveredComputers = new List<ComputerInfo>();
                    }
                });

                this.Invoke((MethodInvoker)delegate
                {
                    // Always ensure localhost (host machine) is included, even if domain scan failed
                    EnsureLocalhostInList();

                    // Populate list with localhost always at top
                    PopulatePCList();
                    
                    progressBar.Style = ProgressBarStyle.Continuous;
                    progressBar.Maximum = 100; // Ensure Maximum is set before setting Value
                    progressBar.Value = 100;
                    
                    if (domainScanError != null)
                    {
                        // Domain scan failed, but localhost is still available
                        lblStatus.Text = "Domain scan failed - localhost is available for log collection";
                        LogMessage($"Domain scan failed: {domainScanError}", LogLevel.Warning);
                        LogMessage("Localhost is still available for log collection. You can also manually add PCs.", LogLevel.Info);
                    }
                    else if (discoveredComputers.Count > 0)
                    {
                        lblStatus.Text = $"Found {discoveredComputers.Count} computers (including localhost)";
                        LogMessage($"Domain scan completed. Found {discoveredComputers.Count} computers (including localhost).", LogLevel.Success);
                    }
                    else
                    {
                        lblStatus.Text = "Domain scan completed - no additional computers found (localhost only)";
                        LogMessage("Domain scan completed - no additional computers found. Only localhost is available.", LogLevel.Warning);
                    }
                    
                    // Always enable Collect Logs if we have at least localhost
                    btnCollectLogs.Enabled = discoveredComputers.Count > 0;
                    // Keep Scan Domain button enabled if scan failed, so user can retry
                    btnScanDomain.Enabled = (domainScanError != null);
                });
                
                // Save scan results to file
                try
                {
                    ScanResultStorage.SaveScanResults(discoveredComputers);
                    LogMessage("Scan results saved to DomainScanResults.json", LogLevel.Info);
                }
                catch (Exception ex)
                {
                    Logger.Error("Failed to save scan results", ex);
                    LogMessage($"Warning: Failed to save scan results: {ex.Message}", LogLevel.Warning);
                }
            }
            catch (Exception ex)
            {
                Logger.Error("Error during domain scan", ex);
                LogMessage($"Error during domain scan: {ex.Message}", LogLevel.Error);
                LogMessage("Localhost is still available for log collection. You can also manually add PCs.", LogLevel.Info);
                this.Invoke((MethodInvoker)delegate
                {
                    // Always ensure localhost is available even if scan failed
                    EnsureLocalhostInList();
                    PopulatePCList();
                    
                    progressBar.Style = ProgressBarStyle.Continuous;
                    progressBar.Maximum = 100; // Ensure Maximum is set before setting Value
                    progressBar.Value = 0;
                    lblStatus.Text = "Domain scan failed - localhost is available for log collection";
                    btnCollectLogs.Enabled = discoveredComputers.Count > 0; // Enable if localhost is available
                    btnScanDomain.Enabled = true; // Allow retry
                });
            }
        }

        private async void BtnCollectLogs_Click(object sender, EventArgs e)
        {
            var selectedIndices = checkedListBoxPCs.CheckedIndices.Cast<int>().ToList();
            if (selectedIndices.Count == 0)
            {
                MessageBox.Show("Please select at least one PC to collect logs from.", "No Selection", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            btnScanDomain.Enabled = false;
            btnCollectLogs.Enabled = false;
            progressBar.Maximum = selectedIndices.Count; // Set Maximum first
            progressBar.Value = 0;
            progressBar.Style = ProgressBarStyle.Continuous;
            listBoxResults.Items.Clear();
            collectionResults.Clear();

            // Map CheckedListBox indices to ComputerInfo objects based on the display order
            // This matches the order used in PopulatePCList() (localhost first, then others sorted)
            var selectedComputers = GetComputersFromCheckedListBoxIndices(selectedIndices);

            // Generate session timestamp for this collection session
            var sessionTimestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
            logCollectorService.SessionTimestamp = sessionTimestamp;

            LogMessage($"Starting log collection from {selectedComputers.Count} PC(s)...", LogLevel.Info);

            try
            {
                await Task.Run(async () =>
                {
                    int completed = 0;
                    foreach (var computer in selectedComputers)
                    {
                        this.Invoke((MethodInvoker)delegate
                        {
                            lblStatus.Text = $"Collecting from {computer.Hostname}... ({completed + 1}/{selectedComputers.Count})";
                        });

                        var result = await logCollectorService.CollectLogsAsync(computer);
                        collectionResults.Add(result);
                        
                        // Update results display
                        this.Invoke((MethodInvoker)delegate
                        {
                            UpdateResultsDisplay(result);
                        });

                        completed++;
                        this.Invoke((MethodInvoker)delegate
                        {
                            progressBar.Value = completed;
                        });
                    }
                });

                this.Invoke((MethodInvoker)delegate
                {
                    var successCount = collectionResults.Count(r => r.Success);
                    lblStatus.Text = $"Collection completed - {successCount}/{collectionResults.Count} succeeded";
                    btnScanDomain.Enabled = true;
                    btnCollectLogs.Enabled = true;
                    ShowCollectionSummary();
                    
                    // Save console log to file
                    SaveConsoleLogToFile();
                });

                LogMessage("Log collection completed for all selected PCs.", LogLevel.Success);
            }
            catch (Exception ex)
            {
                LogMessage($"Error during log collection: {ex.Message}", LogLevel.Error);
                this.Invoke((MethodInvoker)delegate
                {
                    btnScanDomain.Enabled = true;
                    btnCollectLogs.Enabled = true;
                });
            }
        }

        private void OnLogMessage(object sender, LogMessageEventArgs e)
        {
            if (this.InvokeRequired)
            {
                this.Invoke(new Action(() => LogMessage(e.Message, e.Level)));
            }
            else
            {
                LogMessage(e.Message, e.Level);
            }
        }

        private void LogMessage(string message, LogLevel level)
        {
            if (richTextBoxConsole.InvokeRequired)
            {
                richTextBoxConsole.Invoke(new Action(() => AppendLog(message, level)));
            }
            else
            {
                AppendLog(message, level);
            }
        }

        private void AppendLog(string message, LogLevel level)
        {
            Color color = level switch
            {
                LogLevel.Info => Color.Cyan,
                LogLevel.Success => Color.LimeGreen,
                LogLevel.Warning => Color.Yellow,
                LogLevel.Error => Color.Red,
                _ => Color.White
            };

            richTextBoxConsole.SelectionStart = richTextBoxConsole.TextLength;
            richTextBoxConsole.SelectionLength = 0;
            richTextBoxConsole.SelectionColor = color;
            richTextBoxConsole.AppendText($"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] {message}\r\n");
            richTextBoxConsole.SelectionColor = richTextBoxConsole.ForeColor;
            richTextBoxConsole.ScrollToCaret();
        }

        private void UpdateResultsDisplay(CollectionResult result)
        {
            try
            {
                if (result.Success)
                {
                    var collectedCount = result.CollectedItems.Count;
                    var notFoundCount = result.NotFoundItems.Count;
                    var status = collectedCount > 0 ? $"✓ {result.Hostname}: {collectedCount} collected" : $"⚠ {result.Hostname}: No logs found";
                    listBoxResults.Items.Add(status);
                    
                    if (notFoundCount > 0)
                    {
                        listBoxResults.Items.Add($"  └─ {notFoundCount} paths not found");
                    }
                }
                else
                {
                        var error = string.IsNullOrEmpty(result.ErrorMessage) ? "Connection failed" : result.ErrorMessage;
                        listBoxResults.Items.Add($"✗ {result.Hostname}: Failed - {error}");
                }
                
                // Auto-scroll to bottom
                if (listBoxResults.Items.Count > 0)
                {
                    listBoxResults.TopIndex = listBoxResults.Items.Count - 1;
                }
            }
            catch (Exception ex)
            {
                Logger.Error("Error updating results display", ex);
            }
        }

        /// <summary>
        /// Handles adding a PC manually by hostname or IP address.
        /// Works even when the machine is not joined to a domain.
        /// </summary>
        private void BtnAddPC_Click(object sender, EventArgs e)
        {
            try
            {
                var input = txtManualPC.Text.Trim();
                if (string.IsNullOrEmpty(input))
                {
                    MessageBox.Show("Please enter a hostname or IP address.", "Input Required",
                        MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    return;
                }

                if (discoveredComputers == null)
                {
                    discoveredComputers = new List<ComputerInfo>();
                }

                // Determine hostname and IP
                string hostname = input;
                string ipAddress = input;

                // If input is not a valid IP, treat as hostname and try to resolve IP
                if (!IPAddress.TryParse(input, out _))
                {
                    try
                    {
                        var entry = Dns.GetHostEntry(input);
                        var ipv4 = entry.AddressList
                            .FirstOrDefault(a => a.AddressFamily == System.Net.Sockets.AddressFamily.InterNetwork);
                        ipAddress = ipv4 != null ? ipv4.ToString() : "N/A";
                    }
                    catch
                    {
                        ipAddress = "N/A";
                    }
                }

                // Check for duplicates by hostname
                if (discoveredComputers.Any(c =>
                        c.Hostname.Equals(hostname, StringComparison.OrdinalIgnoreCase)))
                {
                    MessageBox.Show("This PC is already in the list.", "Duplicate PC",
                        MessageBoxButtons.OK, MessageBoxIcon.Information);
                    return;
                }

                var manualComputer = new ComputerInfo
                {
                    Hostname = hostname,
                    IPAddress = ipAddress,
                    OperatingSystem = "Manual entry"
                };
                discoveredComputers.Add(manualComputer);

                // Refresh the entire list to ensure localhost stays at top
                PopulatePCList();

                // Save updated list to scan results file
                try
                {
                    ScanResultStorage.SaveScanResults(discoveredComputers);
                    LogMessage("Manual PC list updated and saved.", LogLevel.Info);
                }
                catch (Exception ex)
                {
                    Logger.Error("Failed to save scan results after manual PC add", ex);
                    LogMessage($"Warning: Failed to save scan results after manual PC add: {ex.Message}", LogLevel.Warning);
                }

                Logger.Info($"Manual PC added: {hostname} ({ipAddress})");
                txtManualPC.Clear();
            }
            catch (Exception ex)
            {
                Logger.Error("Error adding manual PC", ex);
                MessageBox.Show($"Error adding PC: {ex.Message}", "Error",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void ShowCollectionSummary()
        {
            try
            {
                var summary = new StringBuilder();
                summary.AppendLine("=== Collection Summary ===\n");

                foreach (var result in collectionResults)
                {
                    summary.AppendLine($"{result.Hostname} ({result.ConnectionMethod}):");
                    
                    if (result.Success)
                    {
                        summary.AppendLine($"  ✓ Success - {result.CollectedItems.Count} items collected");
                        
                        if (result.CollectedItems.Count > 0)
                        {
                            summary.AppendLine("  Collected:");
                            foreach (var item in result.CollectedItems)
                            {
                                summary.AppendLine($"    • {item}");
                            }
                        }
                        
                        if (result.NotFoundItems.Count > 0)
                        {
                            summary.AppendLine("  Not Found:");
                            foreach (var item in result.NotFoundItems)
                            {
                                summary.AppendLine($"    ✗ {item}");
                            }
                        }
                    }
                    else
                    {
                        var error = string.IsNullOrEmpty(result.ErrorMessage) ? "Connection failed" : result.ErrorMessage;
                        summary.AppendLine($"  ✗ Failed: {error}");
                    }
                    
                    var dest = string.IsNullOrEmpty(result.DestinationPath) ? "N/A" : result.DestinationPath;
                    summary.AppendLine($"  Destination: {dest}");
                    summary.AppendLine();
                }

                LogMessage(summary.ToString(), LogLevel.Info);
            }
            catch (Exception ex)
            {
                Logger.Error("Error showing collection summary", ex);
            }
        }

        private void MainForm_Load(object sender, EventArgs e)
        {
            try
            {
                Logger.Info("MainForm loaded");
                // Ensure form is visible
                this.Visible = true;
                this.BringToFront();
            }
            catch (Exception ex)
            {
                Logger.Error("Error in MainForm_Load", ex);
            }
        }

        private void MainForm_Shown(object sender, EventArgs e)
        {
            try
            {
                Logger.Info("MainForm shown");
                // Log that the form is now visible
                LogMessage("Application ready. Click 'Scan Domain' to discover PCs.", LogLevel.Info);
            }
            catch (Exception ex)
            {
                Logger.Error("Error in MainForm_Shown", ex);
            }
        }

        private void MainForm_Resize(object sender, EventArgs e)
        {
            try
            {
                // Constrain right column width for better readability on wide screens
                const int leftColumnWidth = 400;
                const int leftMargin = 12;
                const int rightMargin = 12;
                const int columnGap = 18;
                const int maxRightColumnWidth = 1200; // Maximum width for right column
                const int menuStripHeight = 24;
                const int topOffset = menuStripHeight + 5;
                
                int availableWidth = this.ClientSize.Width - leftMargin - leftColumnWidth - columnGap - rightMargin;
                int rightColumnWidth = Math.Max(300, Math.Min(availableWidth, maxRightColumnWidth)); // Min 300px, max 1200px
                
                // Update right column controls position and size
                int rightColumnStartX = leftMargin + leftColumnWidth + columnGap;
                
                // Progress bar
                progressBar.Location = new Point(rightColumnStartX, topOffset);
                progressBar.Width = rightColumnWidth;
                
                // Status label
                lblStatus.Location = new Point(rightColumnStartX, topOffset + 28);
                lblStatus.Width = rightColumnWidth;
                
                // Console - fill remaining height
                int consoleTop = topOffset + 53;
                int consoleHeight = this.ClientSize.Height - consoleTop - rightMargin;
                richTextBoxConsole.Location = new Point(rightColumnStartX, consoleTop);
                richTextBoxConsole.Width = rightColumnWidth;
                richTextBoxConsole.Height = Math.Max(100, consoleHeight); // Minimum 100px height
            }
            catch (Exception ex)
            {
                Logger.Error("Error in MainForm_Resize", ex);
            }
        }

        private string GetLocalIPAddress()
        {
            try
            {
                // Get the first non-loopback IPv4 address
                var networkInterfaces = NetworkInterface.GetAllNetworkInterfaces()
                    .Where(ni => ni.OperationalStatus == OperationalStatus.Up &&
                                 ni.NetworkInterfaceType != NetworkInterfaceType.Loopback);

                foreach (var ni in networkInterfaces)
                {
                    var ipProps = ni.GetIPProperties();
                    var ipv4Address = ipProps.UnicastAddresses
                        .FirstOrDefault(addr => addr.Address.AddressFamily == System.Net.Sockets.AddressFamily.InterNetwork);
                    
                    if (ipv4Address != null)
                    {
                        return ipv4Address.Address.ToString();
                    }
                }
                
                // Fallback: try to get from Dns
                var hostEntry = Dns.GetHostEntry(Dns.GetHostName());
                var ipAddress = hostEntry.AddressList
                    .FirstOrDefault(ip => ip.AddressFamily == System.Net.Sockets.AddressFamily.InterNetwork);
                
                return ipAddress?.ToString() ?? "127.0.0.1";
            }
            catch
            {
                return "127.0.0.1";
            }
        }

        private void LoadSavedScanResults()
        {
            try
            {
                var savedComputers = ScanResultStorage.LoadScanResults();
                if (savedComputers != null && savedComputers.Count > 0)
                {
                    discoveredComputers = savedComputers;
                    
                    // Ensure localhost is included
                    EnsureLocalhostInList();
                    
                    // Populate the list with localhost always at top
                    PopulatePCList();
                    
                    var scanDate = ScanResultStorage.GetScanDate();
                    var dateInfo = scanDate != DateTime.MinValue ? $" (scanned on {scanDate:yyyy-MM-dd HH:mm:ss})" : "";
                    lblStatus.Text = $"Loaded {discoveredComputers.Count} computers from saved scan results{dateInfo}";
                    btnCollectLogs.Enabled = discoveredComputers.Count > 0;
                    
                    LogMessage($"Loaded {discoveredComputers.Count} computers from saved scan results{dateInfo}", LogLevel.Info);
                    LogMessage("Click 'Scan Domain' to refresh the list, or proceed with log collection.", LogLevel.Info);
                    
                    Logger.Info($"Loaded {discoveredComputers.Count} computers from saved scan results");
                }
            }
            catch (Exception ex)
            {
                Logger.Error("Error loading saved scan results", ex);
                // Don't show error to user, just log it - app can continue without saved results
            }
        }

        /// <summary>
        /// Ensures the current machine (localhost) is present in the PC list,
        /// even if domain scan is not available or the machine is not joined to a domain.
        /// </summary>
        private void EnsureLocalhostInList()
        {
            try
            {
                var localHostname = Environment.MachineName;
                var localIPAddress = GetLocalIPAddress();

                if (discoveredComputers == null)
                {
                    discoveredComputers = new List<ComputerInfo>();
                }

                var localhostExists = discoveredComputers.Any(c =>
                    c.Hostname.Equals(localHostname, StringComparison.OrdinalIgnoreCase));

                if (!localhostExists)
                {
                    var localhostComputer = new ComputerInfo
                    {
                        Hostname = localHostname,
                        IPAddress = localIPAddress,
                        OperatingSystem = Environment.OSVersion.ToString()
                    };
                    discoveredComputers.Insert(0, localhostComputer);
                    Logger.Info("Localhost added to discovered computers list");
                }
            }
            catch (Exception ex)
            {
                Logger.Error("Error ensuring localhost in PC list", ex);
            }
        }

        /// <summary>
        /// Maps CheckedListBox indices to ComputerInfo objects based on the display order.
        /// This matches the order used in PopulatePCList() (localhost first, then others sorted).
        /// </summary>
        private List<ComputerInfo> GetComputersFromCheckedListBoxIndices(List<int> checkedIndices)
        {
            var result = new List<ComputerInfo>();
            
            if (discoveredComputers == null || discoveredComputers.Count == 0)
            {
                return result;
            }

            var localHostname = Environment.MachineName;
            
            // Separate localhost from other computers (same logic as PopulatePCList)
            var localhostComputer = discoveredComputers.FirstOrDefault(c =>
                c.Hostname.Equals(localHostname, StringComparison.OrdinalIgnoreCase));
            
            var otherComputers = discoveredComputers.Where(c =>
                !c.Hostname.Equals(localHostname, StringComparison.OrdinalIgnoreCase))
                .OrderBy(c => c.Hostname)
                .ToList();

            // Build the ordered list matching PopulatePCList() order
            var orderedComputers = new List<ComputerInfo>();
            if (localhostComputer != null)
            {
                orderedComputers.Add(localhostComputer);
            }
            orderedComputers.AddRange(otherComputers);

            // Map CheckedListBox indices to ComputerInfo objects
            foreach (var index in checkedIndices)
            {
                if (index >= 0 && index < orderedComputers.Count)
                {
                    result.Add(orderedComputers[index]);
                }
            }

            return result;
        }

        /// <summary>
        /// Populates the PC list in the CheckedListBox, ensuring localhost is always at the top.
        /// </summary>
        private void PopulatePCList()
        {
            try
            {
                checkedListBoxPCs.Items.Clear();
                
                if (discoveredComputers == null || discoveredComputers.Count == 0)
                {
                    return;
                }

                var localHostname = Environment.MachineName;
                
                // Separate localhost from other computers
                var localhostComputer = discoveredComputers.FirstOrDefault(c =>
                    c.Hostname.Equals(localHostname, StringComparison.OrdinalIgnoreCase));
                
                var otherComputers = discoveredComputers.Where(c =>
                    !c.Hostname.Equals(localHostname, StringComparison.OrdinalIgnoreCase))
                    .OrderBy(c => c.Hostname)
                    .ToList();

                // Always add localhost first
                if (localhostComputer != null)
                {
                    var localhostDisplayName = $"{localhostComputer.Hostname} ({localhostComputer.IPAddress}) [localhost]";
                    checkedListBoxPCs.Items.Add(localhostDisplayName, false);
                }

                // Then add all other computers (sorted alphabetically)
                foreach (var computer in otherComputers)
                {
                    var displayName = $"{computer.Hostname} ({computer.IPAddress})";
                    checkedListBoxPCs.Items.Add(displayName, false);
                }
            }
            catch (Exception ex)
            {
                Logger.Error("Error populating PC list", ex);
            }
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

        private void SaveConsoleLogToFile()
        {
            try
            {
                if (richTextBoxConsole.TextLength == 0)
                {
                    Logger.Debug("Console log is empty, skipping save");
                    return;
                }

                // Use session timestamp if available, otherwise use current timestamp
                var sessionTimestamp = logCollectorService.SessionTimestamp ?? DateTime.Now.ToString("yyyyMMdd_HHmmss");
                var timestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
                
                // Create log directory in Logs folder with timestamp token
                // Use current user's Documents folder (not admin's if running elevated)
                string documentsPath = GetCurrentUserDocumentsFolder();
                var logDir = Path.Combine(
                    documentsPath,
                    $"Logs_{sessionTimestamp}"
                );
                Directory.CreateDirectory(logDir);

                // Save with timestamp for better organization
                var logFileName = $"CollectionProcessLog_{timestamp}.txt";
                var logFilePath = Path.Combine(logDir, logFileName);

                // Save the console content
                File.WriteAllText(logFilePath, richTextBoxConsole.Text, Encoding.UTF8);
                
                Logger.Info($"Console log saved to: {logFilePath}");
                LogMessage($"Complete collection process log saved to: {logFilePath}", LogLevel.Info);
            }
            catch (Exception ex)
            {
                Logger.Error("Error saving console log to file", ex);
                LogMessage($"Warning: Failed to save console log: {ex.Message}", LogLevel.Warning);
            }
        }

        private void AboutMenuItem_Click(object sender, EventArgs e)
        {
            try
            {
                using (var aboutDialog = new AboutDialog())
                {
                    aboutDialog.ShowDialog(this);
                }
            }
            catch (Exception ex)
            {
                Logger.Error("Error showing About dialog", ex);
                MessageBox.Show(
                    $"Error displaying About dialog:\n\n{ex.Message}",
                    "Error",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                );
            }
        }

        private void UserGuideMenuItem_Click(object sender, EventArgs e, string language = null)
        {
            try
            {
                // If language not specified, try to determine from system or default to English
                if (string.IsNullOrEmpty(language))
                {
                    language = "EN"; // Default to English
                }
                
                // Try to load user guide from embedded resources
                var assembly = Assembly.GetExecutingAssembly();
                string guideContent = null;
                string guideTitle = language == "CN" ? "User Guide (中文)" : "User Guide (English)";
                string resourceSuffix = language == "CN" ? "CN" : "EN";
                
                // Try different possible resource names
                string[] possibleNames = { 
                    $"Remotecollect.USER_GUIDE_{resourceSuffix}.md",
                    $"USER_GUIDE_{resourceSuffix}.md"
                };
                
                string resourceName = null;
                
                // First, try exact matches
                foreach (var name in possibleNames)
                {
                    var stream = assembly.GetManifestResourceStream(name);
                    if (stream != null)
                    {
                        resourceName = name;
                        stream.Close();
                        break;
                    }
                }
                
                // If not found, search all resources case-insensitively
                if (resourceName == null)
                {
                    var allResources = assembly.GetManifestResourceNames();
                    foreach (var resName in allResources)
                    {
                        if (resName.EndsWith($"USER_GUIDE_{resourceSuffix}.md", StringComparison.OrdinalIgnoreCase))
                        {
                            resourceName = resName;
                            break;
                        }
                    }
                }
                
                if (resourceName != null)
                {
                    using (var stream = assembly.GetManifestResourceStream(resourceName))
                    {
                        if (stream != null)
                        {
                            using (var reader = new StreamReader(stream, Encoding.UTF8))
                            {
                                guideContent = reader.ReadToEnd();
                            }
                        }
                    }
                }
                
                if (!string.IsNullOrEmpty(guideContent))
                {
                    // Show user guide in a dialog
                    using (var guideViewer = new UserGuideViewer(guideContent, guideTitle))
                    {
                        guideViewer.ShowDialog(this);
                    }
                }
                else
                {
                    // Fallback: Try to find user guide files in application directory
                    string appDir = AppDomain.CurrentDomain.BaseDirectory;
                    string guidePath = Path.Combine(appDir, $"USER_GUIDE_{resourceSuffix}.md");
                    
                    if (File.Exists(guidePath))
                    {
                        // Read file and display in viewer
                        guideContent = File.ReadAllText(guidePath, Encoding.UTF8);
                        using (var guideViewer = new UserGuideViewer(guideContent, guideTitle))
                        {
                            guideViewer.ShowDialog(this);
                        }
                    }
                    else
                    {
                        MessageBox.Show(
                            $"User Guide ({language}) not found in embedded resources or application directory.\n\n" +
                            $"Expected location:\n  {guidePath}",
                            "User Guide Not Found",
                            MessageBoxButtons.OK,
                            MessageBoxIcon.Information
                        );
                    }
                }
            }
            catch (Exception ex)
            {
                Logger.Error("Error opening user guide", ex);
                MessageBox.Show(
                    $"Error opening user guide:\n\n{ex.Message}",
                    "Error",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                );
            }
        }
    }

    public enum LogLevel
    {
        Info,
        Success,
        Warning,
        Error
    }
}
