using System;

namespace Remotecollect
{
    public class LogMessageEventArgs : EventArgs
    {
        public string Message { get; set; } = string.Empty;
        public LogLevel Level { get; set; }
    }
}
