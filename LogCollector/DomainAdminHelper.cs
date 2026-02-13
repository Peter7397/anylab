using System;
using System.DirectoryServices;
using System.Security;
using System.Security.Principal;
using System.Text;

namespace Remotecollect
{
    public static class DomainAdminHelper
    {
        /// <summary>
        /// Checks if the current user has domain administrator privileges
        /// </summary>
        public static bool IsDomainAdmin()
        {
            try
            {
                var identity = WindowsIdentity.GetCurrent();
                var principal = new WindowsPrincipal(identity);
                
                // Check if user is in Domain Admins group
                return principal.IsInRole(WindowsBuiltInRole.Administrator) &&
                       IsInDomainAdminsGroup(identity);
            }
            catch (Exception ex)
            {
                Logger.Error("Error checking domain admin status", ex);
                return false;
            }
        }

        /// <summary>
        /// Checks if the current user is in Domain Admins group
        /// </summary>
        private static bool IsInDomainAdminsGroup(WindowsIdentity identity)
        {
            try
            {
                using (var entry = new DirectoryEntry())
                {
                    var domainDN = entry.Properties["distinguishedName"].Value?.ToString() ?? string.Empty;
                    if (string.IsNullOrEmpty(domainDN))
                    {
                        return false;
                    }

                    var domainAdminsDN = $"CN=Domain Admins,CN=Users,{domainDN}";
                    
                    using (var domainAdminsEntry = new DirectoryEntry($"LDAP://{domainAdminsDN}"))
                    {
                        var searcher = new DirectorySearcher(domainAdminsEntry)
                        {
                            Filter = $"(member={identity.User})"
                        };
                        
                        var result = searcher.FindOne();
                        return result != null;
                    }
                }
            }
            catch
            {
                // If we can't check, assume not domain admin for security
                return false;
            }
        }

        /// <summary>
        /// Validates domain administrator credentials by attempting to connect to Active Directory
        /// </summary>
        public static bool ValidateDomainAdminCredentials(string domain, string username, SecureString password)
        {
            try
            {
                string passwordPlain = SecureStringToString(password);
                
                // Try to connect to Active Directory with provided credentials
                // Use root domain path
                string ldapPath = domain.Contains(".") ? $"LDAP://DC={domain.Replace(".", ",DC=")}" : $"LDAP://{domain}";
                
                using (var entry = new DirectoryEntry(ldapPath, $"{domain}\\{username}", passwordPlain))
                {
                    // Try to access NativeObject to validate credentials
                    // This will throw an exception if credentials are invalid
                    var test = entry.NativeObject;
                    
                    // If we get here, credentials are valid
                    // Try to perform a simple search to ensure we have AD access
                    using (var searcher = new DirectorySearcher(entry))
                    {
                        searcher.Filter = "(objectClass=domain)";
                        searcher.PropertiesToLoad.Add("distinguishedName");
                        var result = searcher.FindOne();
                        
                        if (result != null)
                        {
                            Logger.Info($"Successfully validated credentials for {domain}\\{username}");
                            return true;
                        }
                    }
                    
                    // If search failed but NativeObject worked, credentials are still valid
                    Logger.Info($"Credentials validated for {domain}\\{username} (AD access confirmed)");
                    return true;
                }
            }
            catch (System.Runtime.InteropServices.COMException comEx)
            {
                // COM exceptions usually indicate authentication failure
                Logger.Warning($"Authentication failed for {domain}\\{username}: {comEx.Message}");
                return false;
            }
            catch (Exception ex)
            {
                Logger.Error($"Failed to validate domain admin credentials: {ex.Message}");
                return false;
            }
        }

        private static string SecureStringToString(SecureString secureString)
        {
            IntPtr ptr = IntPtr.Zero;
            try
            {
                ptr = System.Runtime.InteropServices.Marshal.SecureStringToGlobalAllocUnicode(secureString);
                return System.Runtime.InteropServices.Marshal.PtrToStringUni(ptr) ?? string.Empty;
            }
            finally
            {
                if (ptr != IntPtr.Zero)
                {
                    System.Runtime.InteropServices.Marshal.ZeroFreeGlobalAllocUnicode(ptr);
                }
            }
        }
    }
}
