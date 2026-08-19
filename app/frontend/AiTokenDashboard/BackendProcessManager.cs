using System;
using System.Diagnostics;
using System.IO;

namespace AiTokenDashboard
{
    /// <summary>
    /// Launches the local Python backend as a child process so the app is a
    /// single double-click experience. This assumes Python (with
    /// requirements.txt installed) is on PATH and the "backend" folder sits
    /// next to the built exe -- fine for development and for this demo.
    ///
    /// For a real deployable build, package backend/ with PyInstaller into a
    /// standalone exe and point FileName at that instead of "python" -- that
    /// removes the "does this machine have Python" dependency entirely. Not
    /// done here for time; see README-APP.md.
    /// </summary>
    public static class BackendProcessManager
    {
        private static Process? _process;

        public static void Start()
        {
            if (_process != null && !_process.HasExited)
            {
                return;
            }

            string backendDir = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "backend");
            string mainPy = Path.Combine(backendDir, "main.py");

            if (!File.Exists(mainPy))
            {
                throw new FileNotFoundException(
                    "Could not find backend\\main.py next to the app. Copy the backend folder " +
                    "alongside the built exe, or start it manually with:\n" +
                    "  python -m uvicorn main:app --host 127.0.0.1 --port 8731\n" +
                    "from the backend folder, then relaunch this app.");
            }

            var psi = new ProcessStartInfo
            {
                FileName = "python",
                Arguments = "-m uvicorn main:app --host 127.0.0.1 --port 8731",
                WorkingDirectory = backendDir,
                UseShellExecute = false,
                CreateNoWindow = false,
            };

            _process = Process.Start(psi);
        }

        public static void Stop()
        {
            try
            {
                if (_process != null && !_process.HasExited)
                {
                    _process.Kill(true);
                }
            }
            catch
            {
                // best-effort cleanup on exit
            }
        }
    }
}
