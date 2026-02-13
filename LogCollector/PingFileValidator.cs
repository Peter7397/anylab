using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;

namespace Remotecollect
{
    /// <summary>
    /// Validates ping files for application expiration check.
    /// The application requires a ping file after 1 year from the reference date.
    /// </summary>
    public static class PingFileValidator
    {
        // Must match the encryption key, IV, and HMAC key in PingFileGenerator
        private static readonly byte[] EncryptionKey = Encoding.UTF8.GetBytes("SQLMonitorPIN2024!Key32Bytes!!XX"); // 32 bytes for AES-256
        private static readonly byte[] EncryptionIV = Encoding.UTF8.GetBytes("SQLMonitorIV16B!"); // 16 bytes for AES
        private static readonly byte[] HmacKey = Encoding.UTF8.GetBytes("SQLMonitorHMAC2024!Key32Bytes!!X"); // 32 bytes for HMAC-SHA256

        // Reference date: Today (2026-02-07)
        // After 1 year from this date, ping file is required
        private static readonly DateTime ReferenceDate = new DateTime(2026, 2, 7);
        private static readonly DateTime ExpirationDate = ReferenceDate.AddYears(1); // 2027-02-07

        // Ping file name
        private static readonly string PingFileName = "Remotecollect.ping";

        /// <summary>
        /// Checks if the ping file validation is required and if the file exists.
        /// </summary>
        /// <returns>True if ping file exists or validation is not yet required, false if required but missing</returns>
        public static bool ValidatePingFile(out string message)
        {
            message = string.Empty;
            DateTime currentDate = DateTime.Now;

            // Check if 1 year has passed since reference date
            if (currentDate < ExpirationDate)
            {
                // Not yet 1 year, no validation needed
                Logger.Info($"Ping file validation not yet required. Expiration date: {ExpirationDate:yyyy-MM-dd}");
                return true;
            }

            // 1 year has passed, ping file is required
            Logger.Info($"Ping file validation required. Current date: {currentDate:yyyy-MM-dd}, Expiration date: {ExpirationDate:yyyy-MM-dd}");

            // Get application directory
            string appDirectory = AppDomain.CurrentDomain.BaseDirectory;
            string pingFilePath = Path.Combine(appDirectory, PingFileName);

            // Check if ping file exists
            if (!File.Exists(pingFilePath))
            {
                message = $"The application has detected that your system is not compatible with the application.\n\n" +
                         $"This application requires a compatibility update after {ExpirationDate:yyyy-MM-dd}.\n\n" +
                         $"Continuing to run the tool may lead to unexpected errors.\n\n" +
                         $"Please contact the developer to get an update.";
                
                Logger.Warning($"Ping file not found: {pingFilePath}");
                return false;
            }

            // Ping file exists, validate it
            try
            {
                if (ValidatePingFileContent(pingFilePath))
                {
                    Logger.Info("Ping file validated successfully");
                    return true;
                }
                else
                {
                    message = $"The ping file is invalid or corrupted.\n\n" +
                             $"Please contact the developer to get a valid update file.";
                    Logger.Warning("Ping file validation failed - file is invalid or corrupted");
                    return false;
                }
            }
            catch (Exception ex)
            {
                message = $"Error validating ping file: {ex.Message}\n\n" +
                         $"Please contact the developer for assistance.";
                Logger.Error("Error validating ping file", ex);
                return false;
            }
        }

        /// <summary>
        /// Validates the content of the ping file (decrypts and verifies HMAC).
        /// </summary>
        private static bool ValidatePingFileContent(string filePath)
        {
            try
            {
                // Read the file
                byte[] fileData = File.ReadAllBytes(filePath);

                if (fileData.Length < 32) // HMAC is 32 bytes (SHA256)
                {
                    Logger.Warning("Ping file is too small to contain valid data");
                    return false;
                }

                // Extract HMAC and encrypted data
                byte[] hmac = new byte[32];
                byte[] encryptedData = new byte[fileData.Length - 32];
                Buffer.BlockCopy(fileData, 0, hmac, 0, 32);
                Buffer.BlockCopy(fileData, 32, encryptedData, 0, encryptedData.Length);

                // Verify HMAC
                byte[] calculatedHmac;
                using (HMACSHA256 hmacSha256 = new HMACSHA256(HmacKey))
                {
                    calculatedHmac = hmacSha256.ComputeHash(encryptedData);
                }

                // Compare HMACs (constant-time comparison)
                if (!CompareByteArrays(hmac, calculatedHmac))
                {
                    Logger.Warning("Ping file HMAC verification failed - file may be tampered");
                    return false;
                }

                // Decrypt the data
                string decryptedData;
                using (Aes aes = Aes.Create())
                {
                    aes.Key = EncryptionKey;
                    aes.IV = EncryptionIV;
                    aes.Mode = CipherMode.CBC;
                    aes.Padding = PaddingMode.PKCS7;

                    using (ICryptoTransform decryptor = aes.CreateDecryptor())
                    {
                        byte[] decryptedBytes = decryptor.TransformFinalBlock(encryptedData, 0, encryptedData.Length);
                        decryptedData = Encoding.UTF8.GetString(decryptedBytes);
                    }
                }

                // Parse the data (format: PIN|TIMESTAMP)
                string[] parts = decryptedData.Split('|');
                if (parts.Length != 2)
                {
                    Logger.Warning("Ping file data format is invalid");
                    return false;
                }

                // Validate timestamp (should be within reasonable range)
                if (DateTime.TryParse(parts[1], out DateTime fileDate))
                {
                    // Check if file is not too old (more than 2 years) or from the future
                    DateTime now = DateTime.Now;
                    if (fileDate < now.AddYears(-2) || fileDate > now.AddDays(1))
                    {
                        Logger.Warning($"Ping file timestamp is out of range: {fileDate}");
                        return false;
                    }

                    Logger.Info($"Ping file validated. Generated: {fileDate:yyyy-MM-dd HH:mm:ss}");
                    return true;
                }
                else
                {
                    Logger.Warning("Ping file timestamp cannot be parsed");
                    return false;
                }
            }
            catch (Exception ex)
            {
                Logger.Error("Error validating ping file content", ex);
                return false;
            }
        }

        /// <summary>
        /// Constant-time byte array comparison to prevent timing attacks.
        /// </summary>
        private static bool CompareByteArrays(byte[] a, byte[] b)
        {
            if (a.Length != b.Length)
                return false;

            int result = 0;
            for (int i = 0; i < a.Length; i++)
            {
                result |= a[i] ^ b[i];
            }

            return result == 0;
        }

        /// <summary>
        /// Gets the expiration date for informational purposes.
        /// </summary>
        public static DateTime GetExpirationDate()
        {
            return ExpirationDate;
        }
    }
}
