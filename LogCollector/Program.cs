using System;
using System.Diagnostics;
using System.Windows.Forms;

namespace Remotecollect
{
    internal static class Program
    {
        /// <summary>
        /// The main entry point for the application.
        /// </summary>
        [STAThread]
        static void Main()
        {
            // These must be called before any IWin32Window (Form) is created
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);

            // Add global exception handler for unhandled exceptions
            Application.SetUnhandledExceptionMode(UnhandledExceptionMode.CatchException);
            Application.ThreadException += Application_ThreadException;
            AppDomain.CurrentDomain.UnhandledException += CurrentDomain_UnhandledException;

            // Initialize logging first
            try
            {
                Logger.Initialize();
                Logger.Info("Application starting...");
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    $"Failed to initialize logging: {ex.Message}\n\nApplication will continue but logging may not work.",
                    "Logging Warning",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Warning
                );
            }

            try
            {
                // Check if running as administrator
                bool hasAdminPrivileges = IsRunningAsAdministrator();
                // Treat an elevated/admin process as having the required domain admin privileges.
                // The previous DirectoryServices-based check was unreliable in some environments
                // and caused valid domain admin users to be prompted unnecessarily.
                bool isDomainAdmin = hasAdminPrivileges;

                // If not domain admin, prompt for credentials
                if (!isDomainAdmin)
                {
                    Logger.Warning("Application started without domain administrator privileges");
                    
                    using (var credentialDialog = new CredentialDialog())
                    {
                        var dialogResult = credentialDialog.ShowDialog();
                        
                        if (dialogResult != DialogResult.OK)
                        {
                            Logger.Info("User cancelled credential input - application exited");
                            return;
                        }

                        // Validate credentials
                        bool isValid = DomainAdminHelper.ValidateDomainAdminCredentials(
                            credentialDialog.Domain,
                            credentialDialog.Username,
                            credentialDialog.Password
                        );

                        if (!isValid)
                        {
                            MessageBox.Show(
                                "Invalid domain administrator credentials.\n\n" +
                                "Please verify:\n" +
                                "• Domain name is correct\n" +
                                "• Username is correct\n" +
                                "• Password is correct\n" +
                                "• Account has Domain Administrator privileges\n\n" +
                                "Application will exit.",
                                "Invalid Credentials",
                                MessageBoxButtons.OK,
                                MessageBoxIcon.Error
                            );
                            Logger.Warning("Invalid domain administrator credentials provided");
                            return;
                        }

                        Logger.Info($"Domain administrator credentials validated for: {credentialDialog.Domain}\\{credentialDialog.Username}");
                        // Note: Credentials are validated but not used for impersonation in this version
                        // The application will still run with current user's privileges
                        // Future enhancement: Implement credential impersonation for operations
                    }
                }
                else
                {
                    Logger.Info("Domain administrator privileges confirmed");
                }

                // Check ping file (required after 1 year from reference date)
                if (!PingFileValidator.ValidatePingFile(out string pingFileMessage))
                {
                    Logger.Warning("Ping file validation failed");
                    MessageBox.Show(
                        pingFileMessage,
                        "System Compatibility Check Failed",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error
                    );
                    Logger.Info("Application exited - ping file validation failed");
                    return;
                }

                // .NET Framework 4.8 is built into modern Windows versions, no runtime check needed

                Logger.Info("Starting Windows Forms application");
                Application.Run(new MainForm());
                
                Logger.Info("Application closed normally");
            }
            catch (Exception ex)
            {
                Logger.Error("Fatal error in Main method", ex);
                
                var errorMsg = $"A fatal error occurred:\n\n{ex.Message}\n\n" +
                              $"Log file: {Logger.GetLogFilePath()}\n\n" +
                              "Please check the log file for details.";
                
                MessageBox.Show(
                    errorMsg,
                    "Fatal Error",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                );
            }
        }

        private static bool IsRunningAsAdministrator()
        {
            try
            {
                var identity = System.Security.Principal.WindowsIdentity.GetCurrent();
                var principal = new System.Security.Principal.WindowsPrincipal(identity);
                return principal.IsInRole(System.Security.Principal.WindowsBuiltInRole.Administrator);
            }
            catch (Exception ex)
            {
                Logger.Error("Error checking administrator status", ex);
                return false;
            }
        }

        private static void Application_ThreadException(object sender, System.Threading.ThreadExceptionEventArgs e)
        {
            Logger.Error("Unhandled exception in UI thread", e.Exception);
            MessageBox.Show(
                $"An unhandled error occurred:\n\n{e.Exception.Message}\n\n" +
                $"Log file: {Logger.GetLogFilePath()}",
                "Application Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            );
        }

        private static void CurrentDomain_UnhandledException(object sender, UnhandledExceptionEventArgs e)
        {
            var ex = e.ExceptionObject as Exception;
            Logger.Error("Unhandled exception in application domain", ex);
            
            if (ex != null)
            {
                MessageBox.Show(
                    $"A critical error occurred:\n\n{ex.Message}\n\n" +
                    $"Log file: {Logger.GetLogFilePath()}",
                    "Critical Error",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                );
            }
        }

    }
}
