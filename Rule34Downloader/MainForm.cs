using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Xml.Linq;
using static System.Windows.Forms.VisualStyles.VisualStyleElement;
using System.Web;
using System.IO;


namespace Rule34Downloader
{
    public partial class MainForm : Form
    {

        private readonly HttpClient http;
        ManualResetEventSlim pauseEvent = new(true);

        List<ApiPost> searchResults = new();

        HashSet<int> downloadedPostIds = new();
        HashSet<int> blacklistedPostIds = new();

        HashSet<string> negativeTags;

        const string ConfigFile = "config.json";

        Dictionary<string, int> tagTypeCache = new();
        const string TagCacheFile = "tag_cache.json";

        SemaphoreSlim tagSemaphore = new SemaphoreSlim(4);

        Config settings;

        public MainForm()
        {
            InitializeComponent();

            http = new HttpClient { Timeout = TimeSpan.FromSeconds(30) };
            http.DefaultRequestHeaders.UserAgent.ParseAdd("Rule34Downloader/1.0 (.NET)");

            LoadConfig();
            LoadExistingFiles();
            LoadBlacklist();
            LoadTagCache();

            btnTestApi.Click += async (_, _) => await TestApi();
            btnSearch.Click += async (_, _) => await SearchAllPages();
            btnDownload.Click += async (_, _) => await DownloadAll();
            btnPause.Click += (_, _) => TogglePause();
            btnFolder.Click += (_, _) => ChooseFolder();
            btnForceDownload.Click += async (_, _) => await ForceDownload();

            btnBrowseBlacklist.Click += (_, _) => ChooseBlacklist();

            numMaxDownloads.ValueChanged += (_, _) =>
            {
                settings.MaxDownloads = (int)numMaxDownloads.Value;
                SaveConfig();
            };

        }

        async Task TestApi()
        {
            try
            {
                SaveConfig();

                string url =
                    "https://rule34.xxx/index.php?page=dapi&s=post&q=index&json=1" +
                    "&limit=1" +
                    $"&api_key={Uri.EscapeDataString(settings.ApiKey)}" +
                    $"&user_id={Uri.EscapeDataString(settings.UserId)}";

                string response = await http.GetStringAsync(url);

                // If authentication failed, API returns a string instead of JSON array
                if (response.StartsWith("\"Missing authentication"))
                {
                    MessageBox.Show("Authentication failed. Check API key and user ID.");
                    return;
                }

                // Try parsing JSON to ensure it is valid
                var test = JsonSerializer.Deserialize<List<ApiPost>>(response);

                if (test != null)
                {
                    MessageBox.Show("API authentication successful.");
                }
                else
                {
                    MessageBox.Show("API responded but JSON format was unexpected.");
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show("API test failed: " + ex.Message);
            }
        }

        async Task SearchAllPages()
        {
            SaveConfig();

            RefreshNegativeTagSets();
            searchResults.Clear();

            HashSet<int> seenPostIds = new();

            int maxDownloads = settings.MaxDownloads;
            int page = 0;

            lblResults.Text = "Found 0 results";
            lblSearchStatus.Text = "Searching...";
            btnDownload.Enabled = false;

            while (true)
            {
                // Stop early if we already found enough valid posts
                if (maxDownloads > 0 && searchResults.Count >= maxDownloads)
                    break;

                string json;

                try
                {
                    json = await http.GetStringAsync(BuildApiUrl(page));
                }
                catch
                {
                    break;
                }

                var pageResults = JsonSerializer.Deserialize<List<ApiPost>>(json);

                if (pageResults == null || pageResults.Count == 0)
                    break;

                int addedThisPage = 0;

                foreach (var post in pageResults)
                {
                    // Stop immediately if limit reached mid-page
                    if (maxDownloads > 0 && searchResults.Count >= maxDownloads)
                        break;

                    // Skip negative-tagged posts
                    if (ContainsAnyNegative(post))
                        continue;

                    // Skip already downloaded
                    if (downloadedPostIds.Contains(post.id))
                        continue;

                    // Skip blacklisted
                    if (blacklistedPostIds.Contains(post.id))
                        continue;

                    // Avoid duplicates inside this search session
                    if (!seenPostIds.Add(post.id))
                        continue;

                    // Valid post — keep it
                    searchResults.Add(post);
                    addedThisPage++;

                    Invoke((Delegate)(() =>
                    {
                        lblResults.Text = $"Found {searchResults.Count} results";
                    }));
                }

                // If nothing usable was found on this page, stop paging
                if (addedThisPage == 0)
                    break;

                page++;
                await Task.Yield();
            }

            lblSearchStatus.Text = "Search complete";
            btnDownload.Enabled = searchResults.Count > 0;
        }


        async Task DownloadAll()
        {
            RefreshNegativeTagSets();

            int maxDownloads = settings.MaxDownloads;
            int downloadedThisSession = 0;

            progressBar.Maximum = searchResults.Count;
            progressBar.Value = 0;

            foreach (var post in searchResults)
            {
                await WaitWhilePaused();

                if (maxDownloads > 0 && downloadedThisSession >= maxDownloads)
                    break;

                if (downloadedPostIds.Contains(post.id))
                    continue;

                if (blacklistedPostIds.Contains(post.id))
                    continue;

                if (ContainsAnyNegative(post))
                    continue;

                try
                {
                    byte[] data = await http.GetByteArrayAsync(post.file_url);
                    string ext = Path.GetExtension(post.file_url);
                    string path = Path.Combine(downloadFolder.Text, $"{post.id}{ext}");

                    await File.WriteAllBytesAsync(path, data);

                    var categorizedTags = await BuildCategorizedTags(post);

                    var sidecar = new
                    {
                        post.id,
                        post.rating,
                        post.file_url,
                        tags = categorizedTags
                    };

                    File.WriteAllText(path + ".json",
                        JsonSerializer.Serialize(sidecar, new JsonSerializerOptions
                        {
                            WriteIndented = true
                        })
                    );

                    downloadedPostIds.Add(post.id);
                    downloadedThisSession++;

                    progressBar.Value++;
                    lblProgressText.Text = $"Downloaded {downloadedThisSession} / {searchResults.Count.ToString()}";

                }
                catch
                {
                    return;
                }

                await Task.Delay(1000);
            }

            MessageBox.Show("Download complete.");
        }

        void TogglePause()
        {
            if (pauseEvent.IsSet)
            {
                pauseEvent.Reset();
                btnPause.Text = "Resume";
            }
            else
            {
                pauseEvent.Set();
                btnPause.Text = "Pause";
            }
        }

        void ChooseFolder()
        {
            using var dlg = new FolderBrowserDialog();
            if (dlg.ShowDialog() == DialogResult.OK)
            {
                downloadFolder.Text = dlg.SelectedPath;
                SaveConfig();
            }
        }

        void ChooseBlacklist()
        {
            using var dlg = new OpenFileDialog
            {
                Filter = "Text files (*.txt)|*.txt|All files (*.*)|*.*"
            };

            if (dlg.ShowDialog() == DialogResult.OK)
            {
                txtBlacklist.Text = dlg.FileName;
                settings.BlacklistPath = dlg.FileName;
                SaveConfig();
                LoadBlacklist();
            }
        }

        string BuildApiUrl(int pid)
        {
            return
                "https://rule34.xxx/index.php?page=dapi&s=post&q=index&json=1" +
                $"&limit=100&pid={pid}" +
                $"&tags={Uri.EscapeDataString(BuildApiTags())}" +
                $"&api_key={Uri.EscapeDataString(settings.ApiKey)}" +
                $"&user_id={Uri.EscapeDataString(settings.UserId)}";
        }

        void LoadConfig()
        {
            if (!File.Exists(ConfigFile))
            {
                settings = new Config();
                return;
            }

            settings = JsonSerializer.Deserialize<Config>(File.ReadAllText(ConfigFile)) ?? new Config();

            if (txtApiKey != null) txtApiKey.Text = settings.ApiKey ?? "";
            if (txtUserId != null) txtUserId.Text = settings.UserId ?? "";
            if (txtPositiveTags != null) txtPositiveTags.Text = settings.PositiveTags ?? "";
            if (txtNegativeTags != null) txtNegativeTags.Text = settings.NegativeTags ?? "";
            if (downloadFolder != null) downloadFolder.Text = settings.DownloadFolder ?? "";
            if (txtBlacklist != null) txtBlacklist.Text = settings.BlacklistPath ?? "";

            if (numMaxDownloads != null)
                numMaxDownloads.Value = settings.MaxDownloads;
        }

        void SaveConfig()
        {
            settings.ApiKey = txtApiKey.Text.Trim();
            settings.UserId = txtUserId.Text.Trim();
            settings.PositiveTags = txtPositiveTags.Text;
            settings.NegativeTags = txtNegativeTags.Text;
            settings.DownloadFolder = downloadFolder.Text;
            settings.BlacklistPath = txtBlacklist.Text;
            settings.MaxDownloads = (int)numMaxDownloads.Value;

            File.WriteAllText(ConfigFile,
                JsonSerializer.Serialize(settings, new JsonSerializerOptions
                {
                    WriteIndented = true
                }));
        }

        void LoadExistingFiles()
        {
            downloadedPostIds.Clear();

            if (!Directory.Exists(downloadFolder.Text))
                return;

            foreach (var json in Directory.GetFiles(downloadFolder.Text, "*.json"))
            {
                try
                {
                    using var doc = JsonDocument.Parse(File.ReadAllText(json));
                    if (doc.RootElement.TryGetProperty("id", out var idProp))
                    {
                        downloadedPostIds.Add(idProp.GetInt32());
                    }
                }
                catch { }
            }
        }

        void LoadBlacklist()
        {
            blacklistedPostIds.Clear();

            if (string.IsNullOrWhiteSpace(settings.BlacklistPath))
                return;

            if (!File.Exists(settings.BlacklistPath))
                return;

            foreach (var line in File.ReadAllLines(settings.BlacklistPath))
            {
                var name = Path.GetFileNameWithoutExtension(line.Trim());

                if (int.TryParse(name, out int id))
                {
                    blacklistedPostIds.Add(id);
                }
            }
        }

        static readonly char[] DashChars = { '-', '–', '—', '−' };

        HashSet<string> NormalizeTags(string input)
        {
            return input
                .Split(new[] { ' ', '\n', '\r', '\t' }, StringSplitOptions.RemoveEmptyEntries)
                .Select(t => t.Trim().ToLowerInvariant().TrimStart(DashChars))
                .Where(t => t.Length > 0)
                .ToHashSet();
        }

        string BuildApiTags()
        {
            // Positive tags as-is
            var positives = txtPositiveTags.Text
                .Split(new[] { ' ', '\n', '\r', '\t' }, StringSplitOptions.RemoveEmptyEntries)
                .Select(t => t.Trim())
                .ToList();

            // All negative tags (with dash removed for normalization)
            var allNegatives = txtNegativeTags.Text
                .Split(new[] { ' ', '\n', '\r', '\t' }, StringSplitOptions.RemoveEmptyEntries)
                .Select(t => t.Trim().TrimStart('-'))
                .Where(t => t.Length > 0)
                .ToList();

            // Take only first 100 for API
            var apiNegatives = allNegatives
                .Take(100)
                .Select(t => "-" + t)
                .ToList();

            // Combine
            var finalTags = positives
                .Concat(apiNegatives)
                .ToList();

            return string.Join(" ", finalTags);
        }

        void RefreshNegativeTagSets()
        {
            negativeTags = NormalizeTags(txtNegativeTags.Text);
        }

        bool ContainsAnyNegative(ApiPost post)
        {
            if (negativeTags == null || negativeTags.Count == 0)
                return false;

            var postTags = post.tags
                .Split(' ', StringSplitOptions.RemoveEmptyEntries)
                .Select(t => t.ToLowerInvariant());

            foreach (var tag in postTags)
            {
                if (negativeTags.Contains(tag))
                    return true;
            }

            return false;
        }

        void LoadTagCache()
        {
            if (File.Exists(TagCacheFile))
                tagTypeCache = JsonSerializer.Deserialize<Dictionary<string, int>>(
                    File.ReadAllText(TagCacheFile)
                ) ?? new();
        }

        async Task<int> GetTagTypeAsync(string tag)
        {
            if (tagTypeCache.TryGetValue(tag, out int cachedType) && cachedType != 0)
                return cachedType;

            string url =
                $"https://rule34.xxx/index.php?page=dapi&s=tag&q=index" +
                $"&name={Uri.EscapeDataString(tag)}" +
                $"&api_key={Uri.EscapeDataString(txtApiKey.Text)}" +
                $"&user_id={Uri.EscapeDataString(txtUserId.Text)}";

            int type = 0;

            try
            {
                string response = await http.GetStringAsync(url);

                try
                {
                    var doc = XDocument.Parse(response);
                    var tagElement = doc.Root?.Element("tag");

                    if (tagElement != null &&
                        int.TryParse(tagElement.Attribute("type")?.Value, out int parsed))
                    {
                        type = parsed;
                    }
                }
                catch { }

                tagTypeCache[tag] = type;
                return type;
            }
            catch
            {
                return type;
            }
        }

        async Task<object> BuildCategorizedTags(ApiPost post)
        {
            var postTags = post.tags
                .Split(' ', StringSplitOptions.RemoveEmptyEntries)
                .Select(t => WebUtility.HtmlDecode(t).ToLowerInvariant())
                .ToList();

            var unknownTags = postTags
                .Where(t => !tagTypeCache.ContainsKey(t))
                .Distinct()
                .ToList();

            foreach (var tag in unknownTags)
            {
                await tagSemaphore.WaitAsync();
                try
                {
                    await GetTagTypeAsync(tag);
                }
                finally
                {
                    tagSemaphore.Release();
                }
            }

            var categories = new Dictionary<string, List<string>>
            {
                ["copyright"] = new(),
                ["character"] = new(),
                ["artist"] = new(),
                ["general"] = new(),
                ["meta"] = new()
            };

            foreach (var tag in postTags)
            {
                int type = tagTypeCache[tag];

                switch (type)
                {
                    case 1: categories["artist"].Add(tag); break;
                    case 3: categories["copyright"].Add(tag); break;
                    case 4: categories["character"].Add(tag); break;
                    case 5: categories["meta"].Add(tag); break;
                    default: categories["general"].Add(tag); break;
                }
            }

            return categories;
        }

        void SaveTagCache()
        {
            File.WriteAllText(TagCacheFile,
                JsonSerializer.Serialize(tagTypeCache, new JsonSerializerOptions
                {
                    WriteIndented = true
                })
            );
        }

        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            SaveTagCache();
            SaveConfig();
            base.OnFormClosing(e);
        }

        async Task ForceDownload()
        {
            SaveConfig();

            if (string.IsNullOrWhiteSpace(txtForceUrl.Text))
            {
                MessageBox.Show("Please enter a valid Rule34 post URL.");
                return;
            }

            if (string.IsNullOrWhiteSpace(downloadFolder.Text) || !Directory.Exists(downloadFolder.Text))
            {
                MessageBox.Show("Please set a valid download folder first.");
                return;
            }

            int postId = ExtractPostId(txtForceUrl.Text.Trim());

            if (postId <= 0)
            {
                MessageBox.Show("Could not extract a valid post ID from the URL.");
                return;
            }

            try
            {
                await WaitWhilePaused();

                string url =
                    $"https://rule34.xxx/index.php?page=dapi&s=post&q=index&json=1" +
                    $"&id={postId}" +
                    $"&api_key={Uri.EscapeDataString(txtApiKey.Text)}" +
                    $"&user_id={Uri.EscapeDataString(txtUserId.Text)}";

                string json = await http.GetStringAsync(url);
                var posts = JsonSerializer.Deserialize<List<ApiPost>>(json);

                if (posts == null || posts.Count == 0)
                {
                    MessageBox.Show("Post not found.");
                    return;
                }

                var post = posts[0];

                byte[] data = await http.GetByteArrayAsync(post.file_url);
                string ext = Path.GetExtension(post.file_url);
                string path = Path.Combine(downloadFolder.Text, $"{post.id}{ext}");

                await File.WriteAllBytesAsync(path, data);

                var categorizedTags = await BuildCategorizedTags(post);

                var sidecar = new
                {
                    post.id,
                    post.rating,
                    post.file_url,
                    tags = categorizedTags
                };

                File.WriteAllText(path + ".json",
                    JsonSerializer.Serialize(sidecar, new JsonSerializerOptions
                    {
                        WriteIndented = true
                    })
                );

                downloadedPostIds.Add(post.id);

                await Task.Delay(1000); // keep 1/sec rule

                MessageBox.Show("Force download complete.");
            }
            catch (Exception ex)
            {
                MessageBox.Show("Force download failed: " + ex.Message);
            }
        }

        int ExtractPostId(string url)
        {
            try
            {
                var uri = new Uri(url);
                var query = System.Web.HttpUtility.ParseQueryString(uri.Query);

                if (int.TryParse(query["id"], out int id))
                    return id;
            }
            catch { }

            return 0;
        }

        async Task WaitWhilePaused()
        {
            while (!pauseEvent.IsSet)
            {
                await Task.Delay(100);
            }
        }

    }
}
