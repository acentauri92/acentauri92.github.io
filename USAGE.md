# Site Usage & Reference Guide

Personal reference for maintaining and replicating dheeraj-reddy.in.
Built on [Chirpy Starter](https://github.com/cotes2020/chirpy-starter) (Jekyll theme).

---

## Table of Contents

1. [Running locally](#1-running-locally)
2. [Project structure](#2-project-structure)
3. [What changed from base Chirpy](#3-what-changed-from-base-chirpy)
4. [Adding blog posts](#4-adding-blog-posts)
5. [Adding photos](#5-adding-photos)
6. [Adding a conference talk](#6-adding-a-conference-talk)
7. [Replicating this setup on a fresh Chirpy install](#7-replicating-this-setup-on-a-fresh-chirpy-install)
8. [Generating and applying a patch](#8-generating-and-applying-a-patch)
9. [Key config values](#9-key-config-values)
10. [Third-party services](#10-third-party-services)
11. [Chirpy quirks and hard-won fixes](#11-chirpy-quirks-and-hard-won-fixes)

---

## 1. Running locally

**Prerequisites:** Ruby, Bundler, Jekyll

```bash
# Install dependencies (first time only)
bundle install

# Start local server — live reloads on file changes
bundle exec jekyll serve

# Visit
http://127.0.0.1:4000
```

If you get a port conflict:

```bash
bundle exec jekyll serve --port 4001
```

---

## 2. Project structure

```
.
├── _config.yml            # Main site config (title, URL, analytics, etc.)
├── _data/
│   ├── contact.yml        # Sidebar bottom social/contact icons
│   └── photos.yml         # Photo list for the Photography page
├── _includes/
│   ├── footer.html        # Custom footer (Chirpy attribution removed)
│   ├── metadata-hook.html # Injects style.css + external link JS into <head>
│   └── sidebar.html       # Custom sidebar (reordered tabs, # whoami fix)
├── _posts/                # Blog posts (Markdown)
├── _tabs/
│   ├── about.md           # # whoami page
│   ├── contact.md         # Contact form (Formspree)
│   ├── photography.md     # Photography grid + lightbox
│   └── talks.md           # Conference Talks page
├── assets/
│   ├── css/style.scss     # All custom CSS (MUST have --- front matter)
│   └── images/photos/     # Photo files
└── add-photo.py           # Script to add photos (see section 5)
```

---

## 3. What changed from base Chirpy

This section covers every deviation from the base Chirpy Starter so you can replicate or audit the setup.

### `_config.yml`
- `timezone: Asia/Kolkata`
- `title`, `tagline`, `description`, `url` set to personal values
- `github.username: acentauri92`
- `linkedin.username: jonnalad`
- `social.name: Dheeraj Jonnalagadda`
- `analytics.google.id` set to GA4 measurement ID
- `comments.provider: disqus` with shortname `https-acentauri92-github-io`
- `avatar` set to `assets/images/Avatar.JPEG`

### `assets/css/style.scss` ⚠️ Critical
Created from scratch. **Must have `---` front matter** at the top or Jekyll will not compile it:

```scss
---
---
/* your CSS here */
```

Without the front matter Jekyll treats it as a static file and it never gets compiled into `style.css`. Contains:
- `p { text-align: justify }` — global paragraph justification
- `.nav-label-custom` — font fix for `# whoami` sidebar label
- `.contact-*` — contact form and success state styles
- `.talks-list`, `.talk-entry`, `.talk-meta`, `.talk-video` — Conference Talks page styles
- `.photo-grid`, `.photo-item` — Photography grid
- `#photo-lightbox` — custom lightbox styles

### `_includes/metadata-hook.html`
Chirpy's extension point for injecting into `<head>` on every page. Used for:
- Loading `style.css` (the compiled version of `style.scss`)
- A JS snippet that adds `target="_blank" rel="noopener noreferrer"` to all external links

### `_includes/sidebar.html`
Full override of Chirpy's sidebar. Key changes:
- Removed Tags, Categories, and Archives nav items entirely
- Tab order controlled by `order:` front matter in each `_tabs/*.md` file
- Special case for `about` tab: renders `{{ tab.title }}` directly instead of `| upcase`, so `# whoami` shows correctly without becoming `# WHOAMI`
- The `# whoami` span gets class `nav-label-custom` for explicit font styling

### `_includes/footer.html`
Removed the "Using the Chirpy theme for Jekyll." line. Only the copyright paragraph remains. (MIT license is still satisfied — the LICENSE file in the repo is what matters, not the footer.)

### `_tabs/` — New pages
All tabs use `layout: page` and an `order:` field that controls sidebar position:

| File | Title | Order | Icon |
|---|---|---|---|
| `talks.md` | Conference Talks | 1 | `fas fa-microphone` |
| `photography.md` | Photography | 2 | `fas fa-camera` |
| `about.md` | # whoami | 3 | `fas fa-info-circle` |
| `contact.md` | Contact | 4 | `fas fa-paper-plane` |

### `_tabs/photography.md`
- Loops over `_data/photos.yml` to build a 3-column grid
- Custom JavaScript lightbox appended to `document.body` (not inside `article`) to avoid Chirpy's image-wrapping JS
- Uses capture-phase click handlers to intercept Chirpy's `.popup` behaviour
- `layout: page` is required — Chirpy only loads its image popup JS for `page` and `post` layouts

### `_data/photos.yml`
Manual list of photos. Each entry:
```yaml
- file: "slug-name.jpg"
  description: "Caption shown in lightbox"
```
Photos must exist in `assets/images/photos/`. Use `add-photo.py` to manage this — don't edit manually.

### `_data/contact.yml`
Added two entries beyond the defaults:
```yaml
- type: Hackster
  icon: 'fas fa-microchip'
  url: 'https://www.hackster.io/acentauri92'

- type: contact
  icon: 'fas fa-paper-plane'
  url: '/contact/'
  noblank: true
```

---

## 4. Adding blog posts

Create a file in `_posts/` named `YYYY-MM-DD-title.md`:

```markdown
---
title: Your Post Title
date: 2026-01-15 10:00:00 +0530
categories: [Category]
tags: [tag1, tag2]
---

Post content here.
```

Commit and push — GitHub Pages rebuilds automatically.

---

## 5. Adding photos

Use the automation script — never edit `photos.yml` or copy files manually:

```bash
python3 add-photo.py          # Add a photo interactively
python3 add-photo.py --list   # See all current photos
python3 add-photo.py --help   # Full documentation
```

The script:
1. Asks for the image file path (drag & drop into terminal works)
2. Asks for a caption
3. Suggests a slug (e.g. `rain-vortex-singapore`) — accept or override
4. Renames the file to `<slug>.<ext>`, copies it to `assets/images/photos/`
5. Appends the entry to `_data/photos.yml`
6. Optionally commits and pushes

---

## 6. Adding a conference talk

Edit `_tabs/talks.md`. Each talk follows this structure:

```html
<div class="talk-entry">
  <h2 class="talk-title">Talk Title Here</h2>
  <p class="talk-meta">
    <a class="talk-event" href="https://event-url.com" target="_blank" rel="noopener">Event Name Year</a>
    <span class="talk-details">City, Country · Month D–D, YYYY</span>
    <a class="talk-slides" href="https://slides-url.pdf" target="_blank" rel="noopener">
      <i class="fas fa-file-pdf"></i> Slides
    </a>
  </p>
  <div class="talk-video">
    <iframe
      src="https://www.youtube.com/embed/VIDEO_ID"
      title="Talk title"
      frameborder="0"
      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
      allowfullscreen
    ></iframe>
  </div>
</div>
```

Get the YouTube embed ID from the video URL: `youtube.com/watch?v=VIDEO_ID` → use `VIDEO_ID`.

---

## 7. Replicating this setup on a fresh Chirpy install

To set up from scratch on a new machine or a new Chirpy Starter fork:

### Step 1 — Fork Chirpy Starter
Fork [https://github.com/cotes2020/chirpy-starter](https://github.com/cotes2020/chirpy-starter) and clone it locally.

### Step 2 — Install dependencies
```bash
bundle install
```

### Step 3 — Apply customisations
Either apply the patch (see section 8) or manually recreate the files listed in section 3.

### Step 4 — Add your content
- Replace `assets/images/Avatar.JPEG` with your avatar
- Update `_config.yml` with your details
- Add your posts to `_posts/`
- Add photos using `python3 add-photo.py`

### Step 5 — Configure GitHub Pages
In the repo Settings → Pages → set Source to **GitHub Actions**. Chirpy's bundled workflow handles the build.

---

## 8. Generating and applying a patch

### Generate a patch against base Chirpy Starter

```bash
# Add the upstream Chirpy Starter as a remote
git remote add chirpy-upstream https://github.com/cotes2020/chirpy-starter.git
git fetch chirpy-upstream

# Generate patch of all your changes vs the upstream main
git diff chirpy-upstream/main HEAD -- \
  _config.yml \
  _data/contact.yml \
  _data/photos.yml \
  _includes/footer.html \
  _includes/metadata-hook.html \
  _includes/sidebar.html \
  _tabs/about.md \
  _tabs/contact.md \
  _tabs/photography.md \
  _tabs/talks.md \
  assets/css/style.scss \
  add-photo.py \
  > my-customisations.patch
```

### Apply the patch to a fresh Chirpy Starter

```bash
# In the new repo
git apply my-customisations.patch

# If there are conflicts (theme updated since patch was made)
git apply --reject my-customisations.patch
# Then fix the .rej files manually
```

> **Note:** Photos (`assets/images/photos/`) and `_data/photos.yml` are not included in the patch above since they're personal content. Copy those separately.

---

## 9. Key config values

| Setting | Value | Where |
|---|---|---|
| Site title | Notes to Self! | `_config.yml` → `title` |
| URL | https://dheeraj-reddy.in | `_config.yml` → `url` |
| Timezone | Asia/Kolkata | `_config.yml` → `timezone` |
| GitHub username | acentauri92 | `_config.yml` → `github.username` |
| LinkedIn username | jonnalad | `_config.yml` → `linkedin.username` |
| Google Analytics | G-P2RZBBSJTS | `_config.yml` → `analytics.google.id` |
| Disqus shortname | https-acentauri92-github-io | `_config.yml` → `comments.disqus.shortname` |
| Formspree endpoint | https://formspree.io/f/maqgovky | `_tabs/contact.md` |
| Hackster profile | https://www.hackster.io/acentauri92 | `_data/contact.yml` |

---

## 10. Third-party services

| Service | Purpose | Account needed |
|---|---|---|
| GitHub Pages | Hosting | github.com/acentauri92 |
| Formspree | Contact form email delivery | formspree.io (free tier, 50 submissions/month) |
| Google Analytics | Page view tracking | GA4 property G-P2RZBBSJTS |
| Disqus | Blog post comments | disqus.com |
| Cloudflare / domain registrar | dheeraj-reddy.in DNS | Wherever domain is registered |

---

## 11. Chirpy quirks and hard-won fixes

These are non-obvious issues that took real debugging to solve. If something seems broken, check here first.

---

### `style.scss` must have front matter

Jekyll only compiles `.scss` files into `.css` if they have a front matter block at the top. Without it, Jekyll treats the file as a static asset and copies it as-is — your CSS is never applied.

```scss
---
---

/* your styles here */
```

The compiled output is `assets/css/style.css`. The file is injected via `_includes/metadata-hook.html` using Chirpy's extension point rather than being bundled by Chirpy itself.

---

### Chirpy wraps every `article img` with a popup anchor

Chirpy's `commons.min.js` runs on every page and wraps all `<img>` elements inside `<article>` with an `<a class="popup img-link shimmer">`. This causes two problems on the photography page:

**Problem 1 — Grid gaps:** If the photo grid items were `<a>` tags, Chirpy would nest `<a>` inside `<a>` — invalid HTML — and the browser would break the grid rendering with blank cells.
**Fix:** Photo grid items are `<div class="photo-item">` not `<a>` tags.

**Problem 2 — Clicking lightbox image causes 404:** After opening the custom lightbox, Chirpy wraps the `<img>` inside it with a `.popup` anchor pointing to the image URL. Clicking the image navigates away.
**Fix:** The lightbox is built entirely in JavaScript and appended to `document.body` — outside of `<article>` — so Chirpy's selector never reaches it.

---

### Chirpy's click handler steals clicks before yours

Even with the lightbox outside `<article>`, Chirpy registers its click handlers in the bubble phase. Grid item clicks were being intercepted.
**Fix:** The photo grid's click listener uses the **capture phase** (`addEventListener(..., true)`) so it fires before Chirpy's handler and calls `e.stopPropagation()`.

---

### Shimmer animation on photos

Chirpy adds a `.shimmer::before` CSS animation to all `.popup` elements (the anchors it wraps images with). This appeared as a white diagonal line scrolling across photos.
**Fix:** Added to `style.scss`:
```scss
.photo-grid .photo-item .shimmer::before { display: none; }
#photo-lightbox .shimmer::before { display: none !important; }
```

---

### `# whoami` sidebar rendering

Chirpy's sidebar template pipes all tab titles through `| upcase`, which would render `# whoami` as `# WHOAMI`. The `#` also risked being interpreted oddly.
**Fix:** `_includes/sidebar.html` has a special case — when `tab_name == 'about'`, it renders `{{ tab.title }}` directly without `| upcase`, and applies a `nav-label-custom` CSS class to match the font weight and sizing of the other items.

---

### Photography page requires `layout: page`

Chirpy only initialises its image popup JS (GLightbox, `page.min.js`) for pages with `layout: page` or `layout: post`. If the photography tab used a custom layout extending `default`, the JS wouldn't load and clicks did nothing.
**Fix:** Always use `layout: page` in `_tabs/photography.md`.

---

### `photos.yml` vs `site.static_files`

Jekyll's `site.static_files` can list files in a folder, but provides no way to attach per-file metadata (captions). `_data/photos.yml` was chosen instead — it requires a manual entry per photo but allows descriptions. This is why the `add-photo.py` script exists: to make that manual step painless.

---

### External links opening in same tab

Markdown links and HTML links without `target="_blank"` open in the same tab by default. Rather than updating every link individually, a small JS snippet in `_includes/metadata-hook.html` runs on every page and adds `target="_blank" rel="noopener noreferrer"` to all links whose hostname differs from the site's own hostname.

---

### MIT licence and the removed footer credit

Chirpy's footer originally included "Using the Chirpy theme for Jekyll." — this was removed via `_includes/footer.html`. This is fine under MIT: the licence only requires the copyright notice to be preserved in the `LICENSE` file, which is untouched. No footer credit is legally required.
