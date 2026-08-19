using System.Collections.Generic;
using System.Text.Json;

namespace AiTokenDashboard
{
    public class UsagePayload
    {
        public KpiData? Kpis { get; set; }
        public List<DepartmentSummary> Departments { get; set; } = new List<DepartmentSummary>();
        public List<Dictionary<string, JsonElement>> DailyTrend { get; set; } = new List<Dictionary<string, JsonElement>>();
        public List<TopUser> TopUsers { get; set; } = new List<TopUser>();
        public List<AppUsage> ByApp { get; set; } = new List<AppUsage>();
        public bool TokensEstimated { get; set; }
        public string? GeneratedAt { get; set; }
        public string? Source { get; set; }
        public List<string> Warnings { get; set; } = new List<string>();
        public int HistoryDays { get; set; }
        public string? Error { get; set; }
    }

    public class KpiData
    {
        public double TotalTokens { get; set; }
        public double TotalCost { get; set; }
        public int DepartmentCount { get; set; }
        public int ActiveUsers { get; set; }
    }

    public class DepartmentSummary
    {
        public string Name { get; set; } = "";
        public double Tokens { get; set; }
        public double Cost { get; set; }
        public int Users { get; set; }
        public double AvgCostPerUser { get; set; }
    }

    public class TopUser
    {
        public string User { get; set; } = "";
        public string Department { get; set; } = "";
        public double Tokens { get; set; }
        public double Cost { get; set; }
    }

    public class AppUsage
    {
        public string App { get; set; } = "";
        public double Tokens { get; set; }
        public double Cost { get; set; }
    }
}
