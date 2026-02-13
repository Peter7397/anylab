using System;
using System.Collections.Generic;
using System.DirectoryServices;
using System.Linq;
using System.Net;
using System.Net.NetworkInformation;

namespace Remotecollect
{
    public class DomainScanner
    {
        public List<ComputerInfo> ScanDomain()
        {
            Logger.Info("Starting Active Directory domain scan");
            var computers = new List<ComputerInfo>();

            try
            {
                // First, check if machine is joined to a domain by trying to access AD
                // We'll detect this when we try to connect to DirectoryEntry

                // Try to connect to Active Directory
                using (var entry = new DirectoryEntry())
                {
                    // Test connection first
                    try
                    {
                        var test = entry.NativeObject;
                        Logger.Info($"Successfully connected to Active Directory. Path: {entry.Path}");
                    }
                    catch (Exception ex)
                    {
                        Logger.Error($"Failed to connect to Active Directory. Path: {entry.Path}, Error: {ex.Message}", ex);
                        throw new Exception($"Cannot connect to Active Directory: {ex.Message}", ex);
                    }

                    using (var searcher = new DirectorySearcher(entry))
                    {
                        searcher.Filter = "(objectClass=computer)";
                        searcher.PropertiesToLoad.Add("name");
                        searcher.PropertiesToLoad.Add("operatingSystem");
                        searcher.PropertiesToLoad.Add("lastLogonTimestamp");
                        searcher.PropertiesToLoad.Add("distinguishedName");
                        searcher.PageSize = 1000;

                        Logger.Info("Executing Active Directory search for computer objects...");
                        SearchResultCollection results = null;
                        try
                        {
                            results = searcher.FindAll();
                            Logger.Info($"Active Directory search returned {results.Count} results");
                        }
                        catch (Exception ex)
                        {
                            Logger.Error($"Failed to execute Active Directory search: {ex.Message}", ex);
                            throw new Exception($"Active Directory search failed: {ex.Message}", ex);
                        }

                        int processedCount = 0;
                        foreach (SearchResult result in results)
                        {
                            try
                            {
                                var computer = new ComputerInfo
                                {
                                    Hostname = result.Properties["name"][0].ToString() ?? string.Empty,
                                    DistinguishedName = result.Properties["distinguishedName"][0].ToString() ?? string.Empty
                                };

                                if (result.Properties["operatingSystem"].Count > 0)
                                {
                                    computer.OperatingSystem = result.Properties["operatingSystem"][0].ToString() ?? "Unknown";
                                }

                                if (result.Properties["lastLogonTimestamp"].Count > 0)
                                {
                                    var timestamp = result.Properties["lastLogonTimestamp"][0];
                                    if (timestamp != null)
                                    {
                                        computer.LastLogon = DateTime.FromFileTime((long)timestamp);
                                    }
                                }

                                // Try to resolve IP address
                                try
                                {
                                    var hostEntry = Dns.GetHostEntry(computer.Hostname);
                                    computer.IPAddress = hostEntry.AddressList
                                        .FirstOrDefault(ip => ip.AddressFamily == System.Net.Sockets.AddressFamily.InterNetwork)?.ToString() ?? "N/A";
                                }
                                catch
                                {
                                    computer.IPAddress = "N/A";
                                }

                                computers.Add(computer);
                                processedCount++;
                            }
                            catch (Exception ex)
                            {
                                // Log individual computer errors but continue
                                Logger.Warning($"Error processing computer: {ex.Message}");
                            }
                        }

                        Logger.Info($"Successfully processed {processedCount} computers from {results.Count} search results");
                    }
                }
            }
            catch (System.Runtime.InteropServices.COMException comEx)
            {
                Logger.Error($"COM Exception during domain scan (may indicate AD connection issue): {comEx.Message}", comEx);
                throw new Exception($"Active Directory connection error: {comEx.Message}. " +
                    "Please verify: 1) Machine is joined to domain, 2) Domain Controller is accessible, 3) You have Domain Admin privileges.", comEx);
            }
            catch (Exception ex)
            {
                Logger.Error("Failed to scan Active Directory domain", ex);
                // Re-throw with more context
                throw new Exception($"Domain scan failed: {ex.Message}. " +
                    "Please check: 1) Machine is joined to domain, 2) Domain Controller is online, 3) Network connectivity, 4) Domain Admin privileges.", ex);
            }

            Logger.Info($"Domain scan completed. Found {computers.Count} computers");
            return computers.OrderBy(c => c.Hostname).ToList();
        }
    }
}
