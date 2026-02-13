using System;
using System.Collections.Generic;

namespace Remotecollect
{
    public class CollectionResult
    {
        public string Hostname { get; set; } = string.Empty;
        public bool Success { get; set; }
        public string ConnectionMethod { get; set; } = string.Empty;
        public string DestinationPath { get; set; } = string.Empty;
        public List<string> CollectedItems { get; set; } = new List<string>();
        public List<string> NotFoundItems { get; set; } = new List<string>();
        public string ErrorMessage { get; set; } = string.Empty;
        public DateTime CollectionTime { get; set; } = DateTime.Now;
    }
}
