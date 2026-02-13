using System;
using System.Drawing;
using System.Security;
using System.Windows.Forms;

namespace Remotecollect
{
    public partial class CredentialDialog : Form
    {
        public string Username { get; private set; } = string.Empty;
        public SecureString Password { get; private set; }
        public string Domain { get; private set; } = string.Empty;

        private TextBox txtUsername;
        private TextBox txtPassword;
        private TextBox txtDomain;
        private Button btnOK;
        private Button btnCancel;
        private Label lblMessage;

        public CredentialDialog()
        {
            InitializeComponent();
        }

        private void InitializeComponent()
        {
            this.Text = "Domain Administrator Credentials Required";
            this.Size = new Size(450, 280);
            this.StartPosition = FormStartPosition.CenterScreen;
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.MinimizeBox = false;
            this.ShowInTaskbar = false;

            // Message label
            lblMessage = new Label
            {
                Text = "This application requires Domain Administrator privileges.\n\n" +
                       "Required Privileges:\n" +
                       "• Domain Administrator account\n" +
                       "• Active Directory read access\n" +
                       "• Network administrative share access (C$)\n\n" +
                       "Please enter your Domain Administrator credentials:",
                Location = new Point(12, 12),
                Size = new Size(410, 100),
                AutoSize = false
            };
            this.Controls.Add(lblMessage);

            // Domain label and textbox
            var lblDomain = new Label
            {
                Text = "Domain:",
                Location = new Point(12, 120),
                Size = new Size(80, 20)
            };
            this.Controls.Add(lblDomain);

            txtDomain = new TextBox
            {
                Location = new Point(100, 118),
                Size = new Size(320, 23),
                Text = Environment.UserDomainName
            };
            this.Controls.Add(txtDomain);

            // Username label and textbox
            var lblUsername = new Label
            {
                Text = "Username:",
                Location = new Point(12, 150),
                Size = new Size(80, 20)
            };
            this.Controls.Add(lblUsername);

            txtUsername = new TextBox
            {
                Location = new Point(100, 148),
                Size = new Size(320, 23),
                Text = Environment.UserName
            };
            this.Controls.Add(txtUsername);

            // Password label and textbox
            var lblPassword = new Label
            {
                Text = "Password:",
                Location = new Point(12, 180),
                Size = new Size(80, 20)
            };
            this.Controls.Add(lblPassword);

            txtPassword = new TextBox
            {
                Location = new Point(100, 178),
                Size = new Size(320, 23),
                UseSystemPasswordChar = true,
                PasswordChar = '*'
            };
            this.Controls.Add(txtPassword);

            // OK button
            btnOK = new Button
            {
                Text = "OK",
                Location = new Point(265, 210),
                Size = new Size(75, 30),
                DialogResult = DialogResult.OK
            };
            btnOK.Click += BtnOK_Click;
            this.Controls.Add(btnOK);
            this.AcceptButton = btnOK;

            // Cancel button
            btnCancel = new Button
            {
                Text = "Cancel",
                Location = new Point(345, 210),
                Size = new Size(75, 30),
                DialogResult = DialogResult.Cancel
            };
            this.Controls.Add(btnCancel);
            this.CancelButton = btnCancel;

            // Set focus to password field
            txtPassword.TabIndex = 0;
            txtUsername.TabIndex = 1;
            txtDomain.TabIndex = 2;
        }

        private void BtnOK_Click(object sender, EventArgs e)
        {
            if (string.IsNullOrWhiteSpace(txtDomain.Text))
            {
                MessageBox.Show("Please enter a domain name.", "Validation Error", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                txtDomain.Focus();
                this.DialogResult = DialogResult.None;
                return;
            }

            if (string.IsNullOrWhiteSpace(txtUsername.Text))
            {
                MessageBox.Show("Please enter a username.", "Validation Error", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                txtUsername.Focus();
                this.DialogResult = DialogResult.None;
                return;
            }

            if (string.IsNullOrWhiteSpace(txtPassword.Text))
            {
                MessageBox.Show("Please enter a password.", "Validation Error", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                txtPassword.Focus();
                this.DialogResult = DialogResult.None;
                return;
            }

            Domain = txtDomain.Text.Trim();
            Username = txtUsername.Text.Trim();
            
            // Convert password to SecureString
            Password = new SecureString();
            foreach (char c in txtPassword.Text)
            {
                Password.AppendChar(c);
            }
            Password.MakeReadOnly();
        }
    }
}
