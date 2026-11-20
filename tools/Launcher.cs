using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;
using System.Reflection;
using System.Text;
using System.Threading.Tasks;

internal static class Launcher
{
    [STAThread]
    private static void Main()
    {
        string projectDirectory = Path.GetDirectoryName(Application.ExecutablePath);
        if (!string.IsNullOrEmpty(projectDirectory) && projectDirectory.Contains("~"))
            projectDirectory = Path.GetFullPath(projectDirectory);
        bool portable = File.Exists(Path.Combine(projectDirectory, @"runtime\python.exe"));
        string runtimeDirectory = portable ? "runtime" : @".venv\Scripts";
        string python = Path.Combine(projectDirectory, runtimeDirectory, portable ? "python.exe" : "pythonw.exe");
        if (!File.Exists(python))
        {
            MessageBox.Show(
                "未找到本地运行环境，请先完成项目安装。",
                "本地会议同传",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            );
            return;
        }
        try
        {
            EnsureDesktopShortcut(projectDirectory);
            var startInfo = new ProcessStartInfo
            {
                FileName = python,
                Arguments = portable ? "\"" + Path.Combine(projectDirectory, @"runtime\portable_bootstrap.py") + "\"" : "-m local_meeting_interpreter.qt_app",
                WorkingDirectory = projectDirectory,
                UseShellExecute = false,
                CreateNoWindow = true,
                RedirectStandardError = portable,
            };
            if (portable)
                startInfo.EnvironmentVariables["PYTHONPATH"] = Path.Combine(projectDirectory, @"runtime\Lib\site-packages");
            else
                startInfo.EnvironmentVariables["PYTHONPATH"] = Path.Combine(projectDirectory, "src");
            startInfo.EnvironmentVariables["PYTHONUTF8"] = "1";
            startInfo.EnvironmentVariables.Remove("PYTHONHOME");
            Process child = Process.Start(startInfo);
            if (child == null) throw new Exception("无法启动本地会议同传。");
            if (portable)
            {
                var errors = new System.Collections.Concurrent.ConcurrentQueue<string>();
                Task errorReader = Task.Run(() =>
                {
                    try
                    {
                        string line;
                        while ((line = child.StandardError.ReadLine()) != null)
                            errors.Enqueue(line);
                    }
                    catch { }
                });
                if (child.WaitForExit(3000))
                {
                    errorReader.GetAwaiter().GetResult();
                    string details = string.Join(Environment.NewLine, errors).Trim();
                    if (details.Contains("ImportError: DLL load failed"))
                    {
                        MessageBox.Show(
                            "本机安全软件拦截了当前目录的程序运行库（DLL）。\n\n"
                            + "请将整个 MeetingInterpreter 文件夹移到其他位置（例如桌面）后重试，"
                            + "或在安全软件中信任该文件夹。\n\n"
                            + "无需重新安装 Python 或其他工具。",
                            "本地会议同传 - 无法加载运行库",
                            MessageBoxButtons.OK,
                            MessageBoxIcon.Error
                        );
                        return;
                    }
                    MessageBox.Show(
                        "绿色版启动失败：\n\n" + details,
                        "本地会议同传",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error
                    );
                    return;
                }
            }
        }
        catch (Exception error)
        {
            MessageBox.Show(error.Message, "本地会议同传", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private static void EnsureDesktopShortcut(string projectDirectory)
    {
        try
        {
            string desktop = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory);
            string shortcutPath = Path.Combine(desktop, "Meeting Interpreter.lnk");
            object shell = Activator.CreateInstance(Type.GetTypeFromProgID("WScript.Shell"));
            object shortcut = shell.GetType().InvokeMember("CreateShortcut", BindingFlags.InvokeMethod, null, shell, new object[] { shortcutPath });
            Type type = shortcut.GetType();
            type.InvokeMember("TargetPath", BindingFlags.SetProperty, null, shortcut, new object[] { Application.ExecutablePath });
            type.InvokeMember("WorkingDirectory", BindingFlags.SetProperty, null, shortcut, new object[] { projectDirectory });
            type.InvokeMember("IconLocation", BindingFlags.SetProperty, null, shortcut, new object[] { Path.Combine(projectDirectory, @"assets\interpreter.ico") });
            type.InvokeMember("Description", BindingFlags.SetProperty, null, shortcut, new object[] { "本地会议同传" });
            type.InvokeMember("Save", BindingFlags.InvokeMethod, null, shortcut, null);
        }
        catch { }
    }
}

