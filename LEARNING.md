# Learning Log

## PDF Parsing

**Q: Why does `annot.get("uri", "")` return `None` instead of `""`?**  
A: pdfplumber stores annotation fields explicitly as `None` when not present. Python's `dict.get(key, default)` only returns the default if the key is **missing** — if the key exists but has value `None`, it returns `None`. The fix is: `annot.get("uri") or ""`.

**Q: What's the most reliable way to extract part numbers from the Johnstone Supply PDF?**  
A: Use annotation hyperlinks, not regex on text. The PDF embeds clickable links that point to `product-view.ep?pID=PART_NUM`. Regex on page text produces too many false positives (page numbers, table headers, etc.).

## Git / GitHub

**Q: How to create a GitHub repo from the command line without `gh` CLI?**  
A: Use the GitHub REST API with `Invoke-RestMethod`:
```powershell
$headers = @{ Authorization = "token YOUR_TOKEN"; Accept = "application/vnd.github.v3+json" }
Invoke-RestMethod -Uri "https://api.github.com/user/repos" -Method Post -Headers $headers -Body '{"name":"repo-name"}'
```

## Libraries

**Q: How to install packages when Python is managed by uv?**  
A: Don't use `pip install` directly. Create a venv with `uv venv .venv`, activate it, then use `uv pip install package_name`.
