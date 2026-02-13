using System;
using System.Drawing;
using System.Reflection;
using System.Windows.Forms;

namespace Remotecollect
{
    public partial class AboutDialog : Form
    {
        public AboutDialog()
        {
            InitializeComponent();
            LoadAboutInformation();
        }

        private void InitializeComponent()
        {
            this.Text = "About Remotecollect";
            this.Size = new Size(500, 400);
            this.StartPosition = FormStartPosition.CenterParent;
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.MinimizeBox = false;
            this.ShowInTaskbar = false;

            // Try to load icon from embedded resources
            try
            {
                var assembly = System.Reflection.Assembly.GetExecutingAssembly();
                var resourceNames = assembly.GetManifestResourceNames();
                string iconResourceName = null;
                foreach (var name in resourceNames)
                {
                    if (name.Contains("log8.ico") || name.EndsWith(".log8.ico"))
                    {
                        iconResourceName = name;
                        break;
                    }
                }
                if (iconResourceName != null)
                {
                    using (var iconStream = assembly.GetManifestResourceStream(iconResourceName))
                    {
                        if (iconStream != null)
                        {
                            this.Icon = new Icon(iconStream);
                        }
                    }
                }
            }
            catch { /* Ignore icon loading errors */ }

            // Application icon/logo (if available)
            var picIcon = new PictureBox
            {
                Location = new Point(20, 20),
                Size = new Size(64, 64),
                SizeMode = PictureBoxSizeMode.StretchImage
            };
            try
            {
                var assembly = System.Reflection.Assembly.GetExecutingAssembly();
                var resourceNames = assembly.GetManifestResourceNames();
                string iconResourceName = null;
                foreach (var name in resourceNames)
                {
                    if (name.Contains("log8.ico") || name.EndsWith(".log8.ico"))
                    {
                        iconResourceName = name;
                        break;
                    }
                }
                if (iconResourceName != null)
                {
                    using (var iconStream = assembly.GetManifestResourceStream(iconResourceName))
                    {
                        if (iconStream != null)
                        {
                            picIcon.Image = new Icon(iconStream, 64, 64).ToBitmap();
                        }
                    }
                }
            }
            catch { /* Ignore icon loading errors */ }

            // Application name
            var lblAppName = new Label
            {
                Text = "Remotecollect",
                Location = new Point(100, 20),
                Size = new Size(360, 30),
                Font = new Font("Segoe UI", 16, FontStyle.Bold),
                ForeColor = Color.FromArgb(0, 102, 204)
            };

            // Version label
            var lblVersion = new Label
            {
                Location = new Point(100, 55),
                Size = new Size(360, 20),
                Font = new Font("Segoe UI", 9)
            };

            // Description
            var lblDescription = new Label
            {
                Text = "Multi-Method Remote Log Collector",
                Location = new Point(100, 80),
                Size = new Size(360, 20),
                Font = new Font("Segoe UI", 9, FontStyle.Italic)
            };

            // Copyright
            var lblCopyright = new Label
            {
                Location = new Point(20, 120),
                Size = new Size(440, 20),
                Font = new Font("Segoe UI", 8)
            };

            // .NET Framework version
            var lblFramework = new Label
            {
                Location = new Point(20, 145),
                Size = new Size(440, 20),
                Font = new Font("Segoe UI", 8)
            };

            // Features list
            var lblFeatures = new Label
            {
                Text = "Features:",
                Location = new Point(20, 175),
                Size = new Size(440, 20),
                Font = new Font("Segoe UI", 9, FontStyle.Bold)
            };

            var txtFeatures = new TextBox
            {
                Location = new Point(20, 195),
                Size = new Size(440, 100),
                Multiline = true,
                ReadOnly = true,
                ScrollBars = ScrollBars.Vertical,
                Text = "• Domain scanning for network computers\r\n" +
                       "• Manual PC input (hostname or IP)\r\n" +
                       "• Multiple collection methods (SMB, WinRM, PSExec)\r\n" +
                       "• System information collection\r\n" +
                       "• Windows Event Logs (Application, System, Security)\r\n" +
                       "• SQL Server log collection\r\n" +
                       "• Agilent/OpenLab application log collection\r\n" +
                       "• Automatic log organization with timestamps",
                Font = new Font("Segoe UI", 8),
                BorderStyle = BorderStyle.FixedSingle
            };

            // OK button
            var btnOK = new Button
            {
                Text = "OK",
                Location = new Point(385, 310),
                Size = new Size(75, 30),
                DialogResult = DialogResult.OK
            };
            btnOK.Click += (s, e) => this.Close();

            this.Controls.Add(picIcon);
            this.Controls.Add(lblAppName);
            this.Controls.Add(lblVersion);
            this.Controls.Add(lblDescription);
            this.Controls.Add(lblCopyright);
            this.Controls.Add(lblFramework);
            this.Controls.Add(lblFeatures);
            this.Controls.Add(txtFeatures);
            this.Controls.Add(btnOK);

            // Store references for LoadAboutInformation
            _lblVersion = lblVersion;
            _lblCopyright = lblCopyright;
            _lblFramework = lblFramework;
        }

        private Label _lblVersion;
        private Label _lblCopyright;
        private Label _lblFramework;

        private void LoadAboutInformation()
        {
            try
            {
                var assembly = Assembly.GetExecutingAssembly();
                var version = assembly.GetName().Version;
                var versionString = $"Version {version.Major}.{version.Minor}.{version.Build}.{version.Revision}";
                
                var attributes = assembly.GetCustomAttributes(typeof(AssemblyCopyrightAttribute), false);
                var copyright = attributes.Length > 0 
                    ? ((AssemblyCopyrightAttribute)attributes[0]).Copyright 
                    : "Copyright © 2026";

                var frameworkVersion = Environment.Version.ToString();
                var frameworkString = $".NET Framework {frameworkVersion}";

                if (_lblVersion != null)
                {
                    _lblVersion.Text = versionString;
                }
                if (_lblCopyright != null)
                {
                    _lblCopyright.Text = copyright;
                }
                if (_lblFramework != null)
                {
                    _lblFramework.Text = frameworkString;
                }
            }
            catch (Exception ex)
            {
                Logger.Warning($"Error loading about information: {ex.Message}");
            }
        }
    }
}
