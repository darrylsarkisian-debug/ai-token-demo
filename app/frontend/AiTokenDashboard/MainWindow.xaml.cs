using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Shapes;

namespace AiTokenDashboard
{
    public partial class MainWindow : Window
    {
        private readonly BackendClient _client = new BackendClient();

        private readonly Brush[] _palette = new Brush[]
        {
            new SolidColorBrush(Color.FromRgb(0x25, 0x63, 0xEB)), // blue
            new SolidColorBrush(Color.FromRgb(0x05, 0x96, 0x69)), // green
            new SolidColorBrush(Color.FromRgb(0xD9, 0x77, 0x06)), // amber
            new SolidColorBrush(Color.FromRgb(0x7C, 0x3A, 0xED)), // purple
            new SolidColorBrush(Color.FromRgb(0xDC, 0x26, 0x26)), // red
            new SolidColorBrush(Color.FromRgb(0x08, 0x91, 0xB2)), // teal
        };

        public MainWindow()
        {
            InitializeComponent();
            ModeCombo.SelectionChanged += ModeCombo_SelectionChanged;
            ActionButton.Click += ActionButton_Click;
            ModeCombo.SelectedIndex = 0;
        }

        private void ModeCombo_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            bool isLive = ModeCombo.SelectedIndex == 1;
            TenantPanel.Visibility = isLive ? Visibility.Visible : Visibility.Collapsed;
            ActionButton.Content = isLive ? "Connect & pull live data" : "Load demo data";
        }

        private async void ActionButton_Click(object sender, RoutedEventArgs e)
        {
            ActionButton.IsEnabled = false;
            StatusText.Text = "Working...";
            try
            {
                bool isLive = ModeCombo.SelectedIndex == 1;
                string mode = isLive ? "live" : "demo";
                string? tenantId = isLive ? TenantIdBox.Text.Trim() : null;

                if (isLive && string.IsNullOrWhiteSpace(tenantId))
                {
                    StatusText.Text = "Enter a tenant ID or domain before connecting.";
                    return;
                }

                if (isLive)
                {
                    StatusText.Text = "Opening sign-in in your browser -- complete sign-in there...";
                }

                UsagePayload? payload = await _client.GetUsageAsync(mode, tenantId);

                if (payload == null)
                {
                    StatusText.Text = "No response from the local backend. Is it running? See README-APP.md.";
                    return;
                }

                if (!string.IsNullOrEmpty(payload.Error))
                {
                    StatusText.Text = "Error: " + payload.Error;
                    return;
                }

                RenderDashboard(payload);

                string estimateNote = payload.TokensEstimated
                    ? " (tokens/cost are modeled estimates)"
                    : "";
                string warningNote = payload.Warnings.Count > 0
                    ? " | " + string.Join(" ", payload.Warnings)
                    : "";
                StatusText.Text = $"Loaded from {payload.Source} at {payload.GeneratedAt}{estimateNote}{warningNote}";
            }
            catch (Exception ex)
            {
                StatusText.Text = "Error: " + ex.Message;
            }
            finally
            {
                ActionButton.IsEnabled = true;
            }
        }

        private void RenderDashboard(UsagePayload data)
        {
            if (data.Kpis == null) return;

            KpiTokens.Text = data.Kpis.TotalTokens.ToString("N0");
            KpiCost.Text = "$" + data.Kpis.TotalCost.ToString("N2");
            KpiDepartments.Text = data.Kpis.DepartmentCount.ToString();
            KpiUsers.Text = data.Kpis.ActiveUsers.ToString();
            HistoryText.Text = $"History window: {data.HistoryDays} day(s) captured";

            var deptColors = new Dictionary<string, Brush>();
            for (int i = 0; i < data.Departments.Count; i++)
            {
                deptColors[data.Departments[i].Name] = _palette[i % _palette.Length];
            }

            RenderDeptBars(data, deptColors);
            RenderTrendChart(data, deptColors);

            DeptGrid.ItemsSource = data.Departments.OrderByDescending(d => d.Cost).ToList();
            AppGrid.ItemsSource = data.ByApp;
            UsersGrid.ItemsSource = data.TopUsers;
        }

        private void RenderDeptBars(UsagePayload data, Dictionary<string, Brush> deptColors)
        {
            DeptBarsPanel.Children.Clear();

            double maxCost = data.Departments.Count > 0 ? data.Departments.Max(d => d.Cost) : 1;
            if (maxCost <= 0) maxCost = 1;

            foreach (DepartmentSummary dept in data.Departments.OrderByDescending(d => d.Cost))
            {
                var row = new Grid { Margin = new Thickness(0, 0, 0, 8) };
                row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(90) });
                row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
                row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(80) });

                var label = new TextBlock { Text = dept.Name, VerticalAlignment = VerticalAlignment.Center, FontSize = 12 };
                Grid.SetColumn(label, 0);

                var fill = new Border
                {
                    Background = deptColors[dept.Name],
                    CornerRadius = new CornerRadius(4),
                    HorizontalAlignment = HorizontalAlignment.Left,
                    Width = Math.Max(2, (dept.Cost / maxCost) * 300),
                    Height = 18,
                };
                var track = new Border
                {
                    Background = new SolidColorBrush(Color.FromRgb(0xF1, 0xF2, 0xF4)),
                    CornerRadius = new CornerRadius(4),
                    Height = 18,
                    Child = fill,
                };
                Grid.SetColumn(track, 1);

                var value = new TextBlock
                {
                    Text = "$" + dept.Cost.ToString("N2"),
                    VerticalAlignment = VerticalAlignment.Center,
                    HorizontalAlignment = HorizontalAlignment.Right,
                    FontSize = 12,
                    Foreground = Brushes.Gray,
                };
                Grid.SetColumn(value, 2);

                row.Children.Add(label);
                row.Children.Add(track);
                row.Children.Add(value);
                DeptBarsPanel.Children.Add(row);
            }
        }

        private void RenderTrendChart(UsagePayload data, Dictionary<string, Brush> deptColors)
        {
            TrendCanvas.Children.Clear();
            if (data.DailyTrend.Count == 0) return;

            double w = 460, h = 160, pad = 20;
            TrendCanvas.Width = w;
            TrendCanvas.Height = h;

            double maxVal = 1;
            foreach (Dictionary<string, JsonElement> row in data.DailyTrend)
            {
                foreach (DepartmentSummary dept in data.Departments)
                {
                    if (row.TryGetValue(dept.Name, out JsonElement v) && v.ValueKind == JsonValueKind.Number)
                    {
                        maxVal = Math.Max(maxVal, v.GetDouble());
                    }
                }
            }

            double xStep = data.DailyTrend.Count > 1 ? (w - pad * 2) / (data.DailyTrend.Count - 1) : 0;

            var baseline = new Line
            {
                X1 = pad,
                Y1 = h - pad,
                X2 = w - pad,
                Y2 = h - pad,
                Stroke = new SolidColorBrush(Color.FromRgb(0xE5, 0xE7, 0xEB)),
                StrokeThickness = 1,
            };
            TrendCanvas.Children.Add(baseline);

            foreach (DepartmentSummary dept in data.Departments)
            {
                var poly = new Polyline
                {
                    Stroke = deptColors[dept.Name],
                    StrokeThickness = 2,
                };
                var points = new PointCollection();
                for (int i = 0; i < data.DailyTrend.Count; i++)
                {
                    double val = 0;
                    if (data.DailyTrend[i].TryGetValue(dept.Name, out JsonElement v) && v.ValueKind == JsonValueKind.Number)
                    {
                        val = v.GetDouble();
                    }
                    double x = pad + i * xStep;
                    double y = h - pad - (val / maxVal) * (h - pad * 2);
                    points.Add(new Point(x, y));
                }
                poly.Points = points;
                TrendCanvas.Children.Add(poly);
            }
        }
    }
}
