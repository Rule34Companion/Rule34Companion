using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Net.Sockets;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Xml.Linq;
using System.Web;

namespace Rule34Downloader
{
    static class Program
    {
        [STAThread]
        static void Main()
        {
            ApplicationConfiguration.Initialize();
            Application.Run(new MainForm());
        }
    }

    public class ApiPost
    {
        public int id { get; set; }
        public string file_url { get; set; }
        public string tags { get; set; }
        public string rating { get; set; }
    }

    public class Config
    {
        public string ApiKey { get; set; } = "";
        public string UserId { get; set; } = "";
        public string DownloadFolder { get; set; } = "";
        public string PositiveTags { get; set; } = "";
        public string NegativeTags { get; set; } = "";

        public int MaxDownloads { get; set; } = 0;
        public string BlacklistPath { get; set; } = "";
    }
}
