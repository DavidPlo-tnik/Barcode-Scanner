# MD Scanner — Marché Décarie inventory PWA

A phone scanner that pulls up sales history for any product in your store.

## What it does

- Open it on your Android phone in Chrome, point the camera at a barcode
- Shows: shelf price, average weekly units & dollars, 4-week trend (up/down %),
  52-week chart (units or dollars), quarterly breakdown
- Search by name or code if scanning fails
- Works offline once installed (cached locally)

## What's in this folder

```
index.html              — the app (HTML+CSS+JS in one file)
products_compact.json   — your product data (8,082 products, 52 weeks of sales)
manifest.webmanifest    — Add-to-Home-Screen config
sw.js                   — service worker (offline support)
icon.svg / icon-192.png / icon-512.png  — app icons
```

## Deploy in 5 minutes (recommended: Hostinger)

You already have Hostinger for the e-commerce site. Easiest path:

1. Log into Hostinger → File Manager → go to your domain's `public_html`
2. Make a folder called `scanner` (or whatever)
3. Upload all 7 files from this zip into that folder
4. On your Android phone, open Chrome and go to `https://yourdomain.com/scanner/`
5. Tap the menu (⋮) → **Add to Home screen**. Done — opens like a real app.

**HTTPS is required** for camera access. Hostinger gives you SSL by default
so you're fine. If you're hosting somewhere else, the camera will silently
refuse on plain http.

### Alternative: any free static host

GitHub Pages, Netlify Drop, Cloudflare Pages, Vercel — all give you instant
HTTPS. Just drag the folder onto Netlify Drop (https://app.netlify.com/drop)
and it gives you a URL in 10 seconds.

## Updating the data

Each month, when you have a new POS export:

1. Drop the new monthly XLS file into the project alongside the others
2. Ask Claude to rebuild the dataset (`build_dataset.py` is in the project)
3. Replace `products_compact.json` on your host
4. The app will auto-update next time it has internet (service worker
   refreshes the data file in the background)

## Notes on the data

- Period covered: April 2025 → April 2026 (52 weeks)
- 8,082 products with sales activity, 99.8% matched to your price list
- "Most recent week" = the 7 days ending April 30, 2026
- March 2026 was distributed across its 5 weekly buckets proportionally
  (the March file was monthly-only, no daily breakdown — known POS quirk)
- Codes are matched flexibly: scans of UPC-A (12 digits) match POS codes
  with leading zeros stripped, and vice versa

## What's NOT in this version (by design)

- Reorder suggestions, forecasting, supplier ordering — kept out of v1
  per the "scan + show sales (simplest)" choice. Easy to add to v2.
- Live data — this is bundled. Updating means re-uploading the JSON.
- Pickup option — irrelevant here, this isn't the storefront.

## Troubleshooting

**"Camera access needed"** — Chrome blocked it. Tap the lock icon in the
address bar → Site settings → Camera → Allow.

**Scanner sees a barcode but says "Not in dataset"** — That product had
no sales in the past 52 weeks, OR your POS uses a totally different
internal code (some weighed items use store-generated PLUs). Use search
to find it by name.

**Slow to open** — First load downloads the 4MB data file. After that,
it's instant (cached). On a clean phone budget ~3 seconds first load.
