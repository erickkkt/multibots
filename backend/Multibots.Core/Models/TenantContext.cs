// TenantContext.cs

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace Multibots.Core.Models
{
    public class TenantContext
    {
        public string TenantId { get; set; }
        public string TenantName { get; set; }
        public Dictionary<string, string> MetaData { get; set; }

        public TenantContext(string tenantId, string tenantName)
        {
            TenantId = tenantId;
            TenantName = tenantName;
            MetaData = new Dictionary<string, string>();
        }

        // Additional properties and methods can be added here as needed
    }
}