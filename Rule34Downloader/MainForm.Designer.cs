namespace Rule34Downloader
{
    partial class MainForm
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            label1 = new Label();
            txtApiKey = new TextBox();
            txtUserId = new TextBox();
            label2 = new Label();
            txtPositiveTags = new TextBox();
            label3 = new Label();
            txtNegativeTags = new TextBox();
            label4 = new Label();
            btnFolder = new Button();
            btnBrowseBlacklist = new Button();
            txtForceUrl = new TextBox();
            btnForceDownload = new Button();
            label5 = new Label();
            numMaxDownloads = new NumericUpDown();
            btnTestApi = new Button();
            btnSearch = new Button();
            btnDownload = new Button();
            btnPause = new Button();
            lblResults = new Label();
            lblSearchStatus = new Label();
            lblProgressText = new Label();
            txtBlacklist = new TextBox();
            progressBar = new ProgressBar();
            downloadFolder = new TextBox();
            ((System.ComponentModel.ISupportInitialize)numMaxDownloads).BeginInit();
            SuspendLayout();
            // 
            // label1
            // 
            label1.AutoSize = true;
            label1.Location = new Point(58, 24);
            label1.Name = "label1";
            label1.Size = new Size(47, 15);
            label1.TabIndex = 0;
            label1.Text = "API Key";
            // 
            // txtApiKey
            // 
            txtApiKey.Location = new Point(111, 21);
            txtApiKey.Name = "txtApiKey";
            txtApiKey.Size = new Size(115, 23);
            txtApiKey.TabIndex = 1;
            txtApiKey.Text = "API key goes here";
            // 
            // txtUserId
            // 
            txtUserId.Location = new Point(450, 21);
            txtUserId.Name = "txtUserId";
            txtUserId.Size = new Size(115, 23);
            txtUserId.TabIndex = 3;
            txtUserId.Text = "User ID goes here";
            // 
            // label2
            // 
            label2.AutoSize = true;
            label2.Location = new Point(397, 24);
            label2.Name = "label2";
            label2.Size = new Size(44, 15);
            label2.TabIndex = 2;
            label2.Text = "User ID";
            // 
            // txtPositiveTags
            // 
            txtPositiveTags.Location = new Point(111, 85);
            txtPositiveTags.MaxLength = 0;
            txtPositiveTags.Multiline = true;
            txtPositiveTags.Name = "txtPositiveTags";
            txtPositiveTags.ScrollBars = ScrollBars.Vertical;
            txtPositiveTags.Size = new Size(233, 110);
            txtPositiveTags.TabIndex = 5;
            txtPositiveTags.Text = "Positive tags go here (space seperated)";
            // 
            // label3
            // 
            label3.AutoSize = true;
            label3.Location = new Point(31, 88);
            label3.Name = "label3";
            label3.Size = new Size(74, 15);
            label3.TabIndex = 4;
            label3.Text = "Positive Tags";
            // 
            // txtNegativeTags
            // 
            txtNegativeTags.Location = new Point(450, 85);
            txtNegativeTags.MaxLength = 0;
            txtNegativeTags.Multiline = true;
            txtNegativeTags.Name = "txtNegativeTags";
            txtNegativeTags.ScrollBars = ScrollBars.Vertical;
            txtNegativeTags.Size = new Size(233, 110);
            txtNegativeTags.TabIndex = 7;
            txtNegativeTags.Text = "Negative Tags (spece seperated, with a leading \"-\")";
            // 
            // label4
            // 
            label4.AutoSize = true;
            label4.Location = new Point(370, 88);
            label4.Name = "label4";
            label4.Size = new Size(80, 15);
            label4.TabIndex = 6;
            label4.Text = "Negative Tags";
            // 
            // btnFolder
            // 
            btnFolder.Location = new Point(31, 224);
            btnFolder.Name = "btnFolder";
            btnFolder.Size = new Size(165, 23);
            btnFolder.TabIndex = 8;
            btnFolder.Text = "Set Download Location";
            btnFolder.UseVisualStyleBackColor = true;
            // 
            // btnBrowseBlacklist
            // 
            btnBrowseBlacklist.Location = new Point(31, 298);
            btnBrowseBlacklist.Name = "btnBrowseBlacklist";
            btnBrowseBlacklist.Size = new Size(165, 23);
            btnBrowseBlacklist.TabIndex = 9;
            btnBrowseBlacklist.Text = "Set Blacklist File";
            btnBrowseBlacklist.UseVisualStyleBackColor = true;
            // 
            // txtForceUrl
            // 
            txtForceUrl.Location = new Point(58, 415);
            txtForceUrl.Name = "txtForceUrl";
            txtForceUrl.Size = new Size(383, 23);
            txtForceUrl.TabIndex = 10;
            txtForceUrl.Text = "Force download link goes here";
            // 
            // btnForceDownload
            // 
            btnForceDownload.Location = new Point(450, 414);
            btnForceDownload.Name = "btnForceDownload";
            btnForceDownload.Size = new Size(115, 23);
            btnForceDownload.TabIndex = 11;
            btnForceDownload.Text = "Force Download";
            btnForceDownload.UseVisualStyleBackColor = true;
            // 
            // label5
            // 
            label5.AutoSize = true;
            label5.Location = new Point(370, 228);
            label5.Name = "label5";
            label5.Size = new Size(92, 15);
            label5.TabIndex = 12;
            label5.Text = "Max Downloads";
            // 
            // numMaxDownloads
            // 
            numMaxDownloads.Location = new Point(468, 224);
            numMaxDownloads.Maximum = new decimal(new int[] { 1000000, 0, 0, 0 });
            numMaxDownloads.Name = "numMaxDownloads";
            numMaxDownloads.Size = new Size(120, 23);
            numMaxDownloads.TabIndex = 13;
            numMaxDownloads.Value = new decimal(new int[] { 100, 0, 0, 0 });
            // 
            // btnTestApi
            // 
            btnTestApi.Location = new Point(676, 21);
            btnTestApi.Name = "btnTestApi";
            btnTestApi.Size = new Size(75, 23);
            btnTestApi.TabIndex = 14;
            btnTestApi.Text = "Test API";
            btnTestApi.UseVisualStyleBackColor = true;
            // 
            // btnSearch
            // 
            btnSearch.Location = new Point(370, 278);
            btnSearch.Name = "btnSearch";
            btnSearch.Size = new Size(75, 23);
            btnSearch.TabIndex = 15;
            btnSearch.Text = "Search";
            btnSearch.UseVisualStyleBackColor = true;
            // 
            // btnDownload
            // 
            btnDownload.Location = new Point(370, 319);
            btnDownload.Name = "btnDownload";
            btnDownload.Size = new Size(75, 23);
            btnDownload.TabIndex = 16;
            btnDownload.Text = "Download";
            btnDownload.UseVisualStyleBackColor = true;
            // 
            // btnPause
            // 
            btnPause.Location = new Point(370, 358);
            btnPause.Name = "btnPause";
            btnPause.Size = new Size(75, 23);
            btnPause.TabIndex = 17;
            btnPause.Text = "Pause";
            btnPause.UseVisualStyleBackColor = true;
            // 
            // lblResults
            // 
            lblResults.AutoSize = true;
            lblResults.Location = new Point(636, 282);
            lblResults.Name = "lblResults";
            lblResults.Size = new Size(47, 15);
            lblResults.TabIndex = 18;
            lblResults.Text = "Found: ";
            // 
            // lblSearchStatus
            // 
            lblSearchStatus.AutoSize = true;
            lblSearchStatus.Location = new Point(468, 282);
            lblSearchStatus.Name = "lblSearchStatus";
            lblSearchStatus.Size = new Size(77, 15);
            lblSearchStatus.TabIndex = 19;
            lblSearchStatus.Text = "Search Status";
            // 
            // lblProgressText
            // 
            lblProgressText.AutoSize = true;
            lblProgressText.Location = new Point(468, 323);
            lblProgressText.Name = "lblProgressText";
            lblProgressText.Size = new Size(77, 15);
            lblProgressText.TabIndex = 20;
            lblProgressText.Text = "Downloaded:";
            // 
            // txtBlacklist
            // 
            txtBlacklist.Location = new Point(31, 327);
            txtBlacklist.Name = "txtBlacklist";
            txtBlacklist.Size = new Size(165, 23);
            txtBlacklist.TabIndex = 21;
            txtBlacklist.Text = "Blacklist file location";
            // 
            // progressBar
            // 
            progressBar.Location = new Point(616, 319);
            progressBar.Name = "progressBar";
            progressBar.Size = new Size(172, 23);
            progressBar.TabIndex = 22;
            // 
            // downloadFolder
            // 
            downloadFolder.Location = new Point(31, 253);
            downloadFolder.Name = "downloadFolder";
            downloadFolder.Size = new Size(165, 23);
            downloadFolder.TabIndex = 23;
            downloadFolder.Text = "Download folder location";
            // 
            // MainForm
            // 
            AutoScaleDimensions = new SizeF(7F, 15F);
            AutoScaleMode = AutoScaleMode.Font;
            ClientSize = new Size(800, 450);
            Controls.Add(downloadFolder);
            Controls.Add(progressBar);
            Controls.Add(txtBlacklist);
            Controls.Add(lblProgressText);
            Controls.Add(lblSearchStatus);
            Controls.Add(lblResults);
            Controls.Add(btnPause);
            Controls.Add(btnDownload);
            Controls.Add(btnSearch);
            Controls.Add(btnTestApi);
            Controls.Add(numMaxDownloads);
            Controls.Add(label5);
            Controls.Add(btnForceDownload);
            Controls.Add(txtForceUrl);
            Controls.Add(btnBrowseBlacklist);
            Controls.Add(btnFolder);
            Controls.Add(txtNegativeTags);
            Controls.Add(label4);
            Controls.Add(txtPositiveTags);
            Controls.Add(label3);
            Controls.Add(txtUserId);
            Controls.Add(label2);
            Controls.Add(txtApiKey);
            Controls.Add(label1);
            FormBorderStyle = FormBorderStyle.FixedSingle;
            MaximizeBox = false;
            Name = "MainForm";
            StartPosition = FormStartPosition.CenterScreen;
            Text = "Rule34Downloader";
            ((System.ComponentModel.ISupportInitialize)numMaxDownloads).EndInit();
            ResumeLayout(false);
            PerformLayout();
        }

        #endregion

        private Label label1;
        private TextBox txtApiKey;
        private TextBox txtUserId;
        private Label label2;
        private TextBox txtPositiveTags;
        private Label label3;
        private TextBox txtNegativeTags;
        private Label label4;
        private Button btnFolder;
        private Button btnBrowseBlacklist;
        private TextBox txtForceUrl;
        private Button btnForceDownload;
        private Label label5;
        private NumericUpDown numMaxDownloads;
        private Button btnTestApi;
        private Button btnSearch;
        private Button btnDownload;
        private Button btnPause;
        private Label lblResults;
        private Label lblSearchStatus;
        private Label lblProgressText;
        private TextBox txtBlacklist;
        private ProgressBar progressBar;
        private TextBox downloadFolder;
    }
}