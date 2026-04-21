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

## Web Scraping

**Q: Why was the Scrapy spider getting 0 items?**  
A: The site's `robots.txt` has `Disallow: /` for `User-agent: *`, blocking all unknown bots. Since the product pages are public (allowed for Google/Bing), set `ROBOTSTXT_OBEY = False` and use a browser-like User-Agent.

**Q: Why were the CSS selectors not matching any data?**  
A: The page uses specific HTML structure:
- Title: `<meta property="og:title">` (not `<h1>`)
- Brand: `<strong id="productBrand">`
- Mfg #: `<strong id="productManufacturerNumber">`
- Specs: `<table class="table"> <tr> <th>key</th> <td>value</td> </tr>` (uses `<th>` not `<td>` for keys)

**Q: Why were product images returning 404?**  
A: The Sirv viewer uses `data-productimage="WEB/10097/N99-394cl.jpg"` which is a path for the `renderImage` endpoint, NOT a direct Sirv CDN URL. Correct URL: `https://www.johnstonesupply.com/images/renderImage?imageName=WEB/...&width=800&height=600`

## CDK / AWS

**Q: What caused the cyclic dependency error in CDK?**  
A: The VectorStack imported `dataBucket` from StorageStack (dependency: Vector → Storage), then called `dataBucket.addEventNotification()` which creates a Lambda permission that references the Lambda ARN (dependency: Storage → Vector). Fix: remove S3 event notification and use batch script instead, and use `s3.IBucket` type + explicit IAM policies to avoid cross-stack references.

**Q: What packages are needed for CDK TypeScript?**  
A: Must install `@types/node` (devDep) and `source-map-support` in addition to `aws-cdk-lib` and `constructs`.
