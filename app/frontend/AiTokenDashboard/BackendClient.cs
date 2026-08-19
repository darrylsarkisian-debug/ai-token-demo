using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json;
using System.Threading.Tasks;

namespace AiTokenDashboard
{
    public class BackendClient
    {
        private readonly HttpClient _http;
        private readonly JsonSerializerOptions _jsonOptions = new JsonSerializerOptions
        {
            PropertyNameCaseInsensitive = true
        };

        public BackendClient(string baseUrl = "http://127.0.0.1:8731")
        {
            _http = new HttpClient
            {
                BaseAddress = new Uri(baseUrl),
                Timeout = TimeSpan.FromMinutes(3) // live sign-in can take a while
            };
        }

        public async Task<bool> IsHealthyAsync()
        {
            try
            {
                var resp = await _http.GetAsync("/api/health");
                return resp.IsSuccessStatusCode;
            }
            catch
            {
                return false;
            }
        }

        public async Task<UsagePayload?> GetUsageAsync(string mode, string? tenantId = null, string? clientId = null, int days = 30)
        {
            var body = new
            {
                mode,
                tenantId,
                clientId,
                days
            };

            HttpResponseMessage resp = await _http.PostAsJsonAsync("/api/usage", body);
            string json = await resp.Content.ReadAsStringAsync();
            return JsonSerializer.Deserialize<UsagePayload>(json, _jsonOptions);
        }
    }
}
