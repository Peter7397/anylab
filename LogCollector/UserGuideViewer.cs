using System;
using System.Drawing;
using System.IO;
using System.Reflection;
using System.Text;
using System.Windows.Forms;

namespace Remotecollect
{
    public partial class UserGuideViewer : Form
    {
        public UserGuideViewer(string guideContent, string title)
        {
            InitializeComponent(guideContent, title);
        }

        private void InitializeComponent(string guideContent, string title)
        {
            this.Text = title;
            this.Size = new Size(900, 700);
            this.StartPosition = FormStartPosition.CenterParent;
            this.MinimumSize = new Size(600, 400);

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

            // Title label
            var lblTitle = new Label
            {
                Text = title,
                Location = new Point(10, 10),
                Size = new Size(860, 25),
                Font = new Font("Segoe UI", 12, FontStyle.Bold),
                ForeColor = Color.FromArgb(0, 102, 204)
            };

            // Content text box (read-only, multi-line, with scrollbars)
            var txtContent = new RichTextBox
            {
                Location = new Point(10, 40),
                Size = new Size(860, 580),
                Text = guideContent,
                ReadOnly = true,
                Font = new Font("Consolas", 9),
                ScrollBars = RichTextBoxScrollBars.Vertical,
                BorderStyle = BorderStyle.FixedSingle,
                Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right
            };

            // Close button
            var btnClose = new Button
            {
                Text = "Close",
                Location = new Point(795, 630),
                Size = new Size(75, 30),
                Anchor = AnchorStyles.Bottom | AnchorStyles.Right,
                DialogResult = DialogResult.OK
            };
            btnClose.Click += (s, e) => this.Close();

            this.Controls.Add(lblTitle);
            this.Controls.Add(txtContent);
            this.Controls.Add(btnClose);
        }
    }
}
