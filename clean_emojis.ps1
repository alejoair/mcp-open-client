# PowerShell script to remove emojis from Python files
# This handles Unicode better than Python on Windows console

$files = @(
    "mcp_open_client\main.py",
    "mcp_open_client\meta_tools\notify_user.py",
    "mcp_open_client\meta_tools\respond_to_user.py",
    "mcp_open_client\ui\chat_handlers.py",
    "mcp_open_client\ui\configure.py",
    "mcp_open_client\ui\handle_tool_call.py",
    "mcp_open_client\ui\history_settings.py",
    "mcp_open_client\ui\message_parser.py"
)

$replacements = @{
    "✅" = "[OK]"
    "❌" = "[ERROR]"
    "⚠️" = "[WARNING]"
    "💡" = "[TIP]"
    "🔄" = "Refresh"
    "📊" = "[STATUS]"
    "🔔" = "[UPDATE]"
    "🐛" = "[DEBUG]"
    "⚙️" = "[WORKING]"
    "📢" = "[NOTIFICATION]"
    "📝" = "[NOTES]"
    "✨" = "[ADVANTAGE]"
    "🚀" = "[START]"
    "📋" = "[PARAMS]"
    "🔵" = "[INFO]"
    "✓" = "[SELECTED]"
    "🔴" = "[ERROR]"
    "🔚" = "[TERMINAL]"
    "🚫" = "[FORBIDDEN]"
    "🎉" = "[SUCCESS]"
    "❓" = "[QUESTION]"
    "🔊" = "[SOUND]"
}

Write-Host "Cleaning emoji characters from Python files..." -ForegroundColor Green
Write-Host "=" * 50

$filesChanged = 0

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "Processing: $file" -ForegroundColor Yellow

        $content = Get-Content -Path $file -Encoding UTF8 -Raw
        $originalContent = $content

        foreach ($emoji in $replacements.Keys) {
            if ($content.Contains($emoji)) {
                $replacement = $replacements[$emoji]
                $content = $content.Replace($emoji, $replacement)
                Write-Host "  Replaced '$emoji' with '$replacement'" -ForegroundColor Cyan
            }
        }

        # Remove any remaining emojis using regex
        # This regex covers most emoji ranges
        $emojiPattern = '[\u2600-\u26FF\u2700-\u27BF\U0001F300-\U0001F5FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U000024C2-\U0001F251]+'

        if ($content -match $emojiPattern) {
            $content = $content -replace $emojiPattern, '[EMOJI]'
            Write-Host "  Removed remaining emojis" -ForegroundColor Cyan
        }

        if ($content -ne $originalContent) {
            Set-Content -Path $file -Value $content -Encoding UTF8
            Write-Host "  [OK] File updated" -ForegroundColor Green
            $filesChanged++
        } else {
            Write-Host "  - No changes needed" -ForegroundColor Gray
        }
    } else {
        Write-Host "WARNING: File not found: $file" -ForegroundColor Red
    }
}

Write-Host "=" * 50
Write-Host "[OK] Cleanup complete! $filesChanged files were modified." -ForegroundColor Green