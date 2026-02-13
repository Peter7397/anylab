using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Web.Script.Serialization;

namespace Remotecollect
{
    public static class ScanResultStorage
    {
        private static readonly string ScanResultsFileName = "DomainScanResults.json";
        
        /// <summary>
        /// Gets the path to the scan results file (same folder as executable)
        /// </summary>
        private static string GetScanResultsPath()
        {
            var exePath = System.Reflection.Assembly.GetExecutingAssembly().Location;
            var exeDirectory = Path.GetDirectoryName(exePath) ?? AppDomain.CurrentDomain.BaseDirectory;
            return Path.Combine(exeDirectory, ScanResultsFileName);
        }

        /// <summary>
        /// Saves domain scan results to a JSON file
        /// </summary>
        public static void SaveScanResults(List<ComputerInfo> computers)
        {
            try
            {
                var scanData = new ScanResultData
                {
                    ScanDate = DateTime.Now,
                    Computers = computers.Select(c => new ComputerInfoData
                    {
                        Hostname = c.Hostname,
                        IPAddress = c.IPAddress,
                        OperatingSystem = c.OperatingSystem,
                        LastLogon = c.LastLogon,
                        DistinguishedName = c.DistinguishedName
                    }).ToList()
                };

                var serializer = new JavaScriptSerializer();
                var json = serializer.Serialize(scanData);
                
                var filePath = GetScanResultsPath();
                File.WriteAllText(filePath, json, System.Text.Encoding.UTF8);
                
                Logger.Info($"Domain scan results saved to: {filePath}");
            }
            catch (Exception ex)
            {
                Logger.Error("Error saving scan results", ex);
                throw;
            }
        }

        /// <summary>
        /// Loads domain scan results from JSON file
        /// </summary>
        public static List<ComputerInfo> LoadScanResults()
        {
            try
            {
                var filePath = GetScanResultsPath();
                
                if (!File.Exists(filePath))
                {
                    Logger.Debug("No saved scan results found");
                    return new List<ComputerInfo>();
                }

                var json = File.ReadAllText(filePath, System.Text.Encoding.UTF8);
                var serializer = new JavaScriptSerializer();
                var scanData = serializer.Deserialize<ScanResultData>(json);
                
                if (scanData == null || scanData.Computers == null)
                {
                    Logger.Warning("Invalid scan results file format");
                    return new List<ComputerInfo>();
                }

                var computers = scanData.Computers.Select(c => new ComputerInfo
                {
                    Hostname = c.Hostname,
                    IPAddress = c.IPAddress,
                    OperatingSystem = c.OperatingSystem,
                    LastLogon = c.LastLogon,
                    DistinguishedName = c.DistinguishedName
                }).ToList();

                Logger.Info($"Loaded {computers.Count} computers from saved scan results (scanned on {scanData.ScanDate:yyyy-MM-dd HH:mm:ss})");
                return computers;
            }
            catch (Exception ex)
            {
                Logger.Error("Error loading scan results", ex);
                return new List<ComputerInfo>();
            }
        }

        /// <summary>
        /// Gets the scan date from saved results
        /// </summary>
        public static DateTime GetScanDate()
        {
            try
            {
                var filePath = GetScanResultsPath();
                if (!File.Exists(filePath))
                {
                    return DateTime.MinValue;
                }

                var json = File.ReadAllText(filePath, System.Text.Encoding.UTF8);
                var serializer = new JavaScriptSerializer();
                var scanData = serializer.Deserialize<ScanResultData>(json);
                if (scanData != null && scanData.ScanDate != default(DateTime))
                {
                    return scanData.ScanDate;
                }
                return DateTime.MinValue;
            }
            catch
            {
                return DateTime.MinValue;
            }
        }

        private class ScanResultData
        {
            public DateTime ScanDate { get; set; }
            public List<ComputerInfoData> Computers { get; set; } = new List<ComputerInfoData>();
        }

        private class ComputerInfoData
        {
            public string Hostname { get; set; } = string.Empty;
            public string IPAddress { get; set; } = string.Empty;
            public string OperatingSystem { get; set; } = string.Empty;
            public DateTime? LastLogon { get; set; }
            public string DistinguishedName { get; set; } = string.Empty;
        }
    }
}
