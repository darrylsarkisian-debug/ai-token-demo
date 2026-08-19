using System;
using System.Windows;

namespace AiTokenDashboard
{
    public partial class App : Application
    {
        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);
            try
            {
                BackendProcessManager.Start();
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    "Could not start the local backend automatically:\n\n" + ex.Message +
                    "\n\nYou can start it manually (see README-APP.md), then click Refresh once it's running.",
                    "Backend not started",
                    MessageBoxButton.OK,
                    MessageBoxImage.Warning);
            }
        }

        protected override void OnExit(ExitEventArgs e)
        {
            BackendProcessManager.Stop();
            base.OnExit(e);
        }
    }
}
