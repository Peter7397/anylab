using System;

namespace Remotecollect
{
    public class ComputerInfo
    {
        public string Hostname { get; set; } = string.Empty;
        public string IPAddress { get; set; } = string.Empty;
        public string OperatingSystem { get; set; } = string.Empty;
        public DateTime? LastLogon { get; set; }
        public string DistinguishedName { get; set; } = string.Empty;
    }
}
