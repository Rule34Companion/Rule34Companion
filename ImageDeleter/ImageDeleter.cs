using System;
using System.IO;
using System.Text.Json;
using System.Collections.Generic;
using System.Linq;

class ImageDeleter
{
    static void Main()
    {
        Console.WriteLine("=== Rule34 Bulk Image Deleter Tool ===");
        Console.WriteLine();

        Console.Write("Image repository path: ");
        string folder = Console.ReadLine()!.Trim('"');

        if (!Directory.Exists(folder))
        {
            Console.WriteLine("Folder does not exist.");
            return;
        }

        Console.Write("Tags to remove (space-separated): ");
        var targetTags = Console.ReadLine()!
            .Split(' ', StringSplitOptions.RemoveEmptyEntries)
            .Select(t => t.ToLowerInvariant())
            .ToHashSet();

        if (targetTags.Count == 0)
        {
            Console.WriteLine("No tags provided.");
            return;
        }

        Console.Write("Blacklist file path: ");
        string blacklistPath = Console.ReadLine()!.Trim('"');

        if (string.IsNullOrWhiteSpace(blacklistPath))
        {
            Console.WriteLine("No blacklist path provided.");
            return;
        }

        // Ensure blacklist file exists
        if (!File.Exists(blacklistPath))
        {
            File.WriteAllText(blacklistPath, "");
        }

        // Load existing blacklist entries
        var blacklistEntries = new HashSet<string>(
            File.ReadAllLines(blacklistPath)
                .Select(l => l.Trim())
                .Where(l => !string.IsNullOrWhiteSpace(l))
        );

        int deletedCount = 0;
        int addedToBlacklist = 0;

        foreach (var jsonPath in Directory.EnumerateFiles(folder, "*.json"))
        {
            try
            {
                var text = File.ReadAllText(jsonPath);
                var sidecar = JsonSerializer.Deserialize<Sidecar>(text);

                if (sidecar?.tags == null)
                    continue;

                if (ContainsAnyTag(sidecar.tags, targetTags))
                {
                    string imagePath = jsonPath.Substring(0, jsonPath.Length - 5);
                    string fileName = Path.GetFileName(imagePath);

                    if (File.Exists(imagePath))
                    {
                        File.Delete(imagePath);
                    }

                    File.Delete(jsonPath);

                    deletedCount++;
                    Console.WriteLine($"Deleted: {fileName}");

                    // Add to blacklist if not already present
                    if (!blacklistEntries.Contains(fileName))
                    {
                        blacklistEntries.Add(fileName);
                        addedToBlacklist++;
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error reading {Path.GetFileName(jsonPath)}: {ex.Message}");
            }
        }

        // Write updated blacklist back to file
        File.WriteAllLines(blacklistPath, blacklistEntries.OrderBy(x => x));

        Console.WriteLine();
        Console.WriteLine($"Done. Deleted {deletedCount} item(s).");
        Console.WriteLine($"Added {addedToBlacklist} new item(s) to blacklist.");
    }

    static bool ContainsAnyTag(
        Dictionary<string, List<string>> tags,
        HashSet<string> targets)
    {
        foreach (var category in tags.Values)
        {
            foreach (var tag in category)
            {
                if (targets.Contains(tag.ToLowerInvariant()))
                    return true;
            }
        }
        return false;
    }
}

class Sidecar
{
    public Dictionary<string, List<string>>? tags { get; set; }
}
