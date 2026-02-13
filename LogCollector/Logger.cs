using System;
using System.IO;
using System.Text;
using System.Windows.Forms;

namespace Remotecollect
{
    public static class Logger
    {
        private static string _logFilePath;
        private static readonly object _lockObject = new object();
        private static bool _initialized = false;

        public static void Initialize()
        {
            if (_initialized) return;

            try
            {
                var logDir = Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                    "Remotecollect",
                    "Logs"
                );

                Directory.CreateDirectory(logDir);

                var timestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
                _logFilePath = Path.Combine(logDir, $"Remotecollect_{timestamp}.log");

                // Write initial log entry
                WriteLog("INFO", "=== Remotecollect Application Started ===");
                WriteLog("INFO", $"Application Version: 260212");
                WriteLog("INFO", $"OS Version: {Environment.OSVersion}");
                WriteLog("INFO", $".NET Version: {Environment.Version}");
                WriteLog("INFO", $"Machine Name: {Environment.MachineName}");
                WriteLog("INFO", $"User Name: {Environment.UserName}");
                WriteLog("INFO", $"Is Administrator: {IsRunningAsAdministrator()}");
                WriteLog("INFO", $"Working Directory: {Environment.CurrentDirectory}");
                WriteLog("INFO", $"Application Directory: {AppDomain.CurrentDomain.BaseDirectory}");

                _initialized = true;
            }
            catch (Exception ex)
            {
                // Fallback to temp directory if AppData fails
                _logFilePath = Path.Combine(Path.GetTempPath(), $"Remotecollect_{DateTime.Now:yyyyMMdd_HHmmss}.log");
                WriteLog("ERROR", $"Failed to initialize logger in AppData, using temp: {ex.Message}");
                _initialized = true;
            }
        }

        public static void WriteLog(string level, string message)
        {
            lock (_lockObject)
            {
                try
                {
                    if (string.IsNullOrEmpty(_logFilePath))
                    {
                        Initialize();
                    }

                    // Double-check after initialization
                    if (string.IsNullOrEmpty(_logFilePath))
                    {
                        // Last resort fallback
                        _logFilePath = Path.Combine(Path.GetTempPath(), $"Remotecollect_{DateTime.Now:yyyyMMdd_HHmmss}.log");
                    }

                    var logEntry = $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss.fff}] [{level}] {message}";
                    var logLine = logEntry + Environment.NewLine;

                    File.AppendAllText(_logFilePath, logLine, Encoding.UTF8);

                    // Also write to debug output
                    System.Diagnostics.Debug.WriteLine(logEntry);
                }
                catch (Exception ex)
                {
                    // Last resort - try to show in message box if file logging fails
                    try
                    {
                        System.Diagnostics.Debug.WriteLine($"Logger Error: {ex.Message}");
                    }
                    catch { /* Ignore */ }
                }
            }
        }

        public static void Info(string message)
        {
            WriteLog("INFO", message);
        }

        public static void Warning(string message)
        {
            WriteLog("WARN", message);
        }

        public static void Error(string message, Exception ex = null)
        {
            WriteLog("ERROR", message);
            if (ex != null)
            {
                WriteLog("ERROR", $"Exception: {ex.GetType().Name}");
                WriteLog("ERROR", $"Message: {ex.Message}");
                WriteLog("ERROR", $"Stack Trace: {ex.StackTrace}");
                if (ex.InnerException != null)
                {
                    WriteLog("ERROR", $"Inner Exception: {ex.InnerException.Message}");
                }
            }
        }

        public static void Debug(string message)
        {
            WriteLog("DEBUG", message);
        }

        public static string GetLogFilePath()
        {
            if (string.IsNullOrEmpty(_logFilePath))
            {
                Initialize();
            }
            return _logFilePath ?? Path.Combine(Path.GetTempPath(), "Remotecollect.log");
        }

        private static bool IsRunningAsAdministrator()
        {
            try
            {
                var identity = System.Security.Principal.WindowsIdentity.GetCurrent();
                var principal = new System.Security.Principal.WindowsPrincipal(identity);
                return principal.IsInRole(System.Security.Principal.WindowsBuiltInRole.Administrator);
            }
            catch
            {
                return false;
            }
        }
    }
}
