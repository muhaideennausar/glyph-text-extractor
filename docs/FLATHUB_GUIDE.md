# Publishing Glyph to Flathub (Linux App Stores Guide)

This guide walks you through publishing **Glyph - Text Extractor** to [Flathub](https://flathub.org). Publishing to Flathub makes Glyph immediately discoverable and installable with one click across modern Linux distributions via:

- **GNOME Software** (Fedora, Debian, Arch Linux, Pop!\_OS, openSUSE)
- **KDE Discover** (SteamOS, Kubuntu, Fedora KDE, openSUSE KDE, Manjaro)
- **Linux Mint Software Manager**, **Zorin App Center**, **elementary AppCenter**

---

## 1. How the Flathub Pipeline Works

```
 ┌────────────────────────────────────────────────────────┐
 │ 1. You submit a Pull Request to flathub/flathub       │
 │    containing io.github.muhaideennausar.Glyph.yaml     │
 └──────────────────────┬─────────────────────────────────┘
                        ▼
 ┌────────────────────────────────────────────────────────┐
 │ 2. Flathub CI (flathubbot) builds & tests Glyph on    │
 │    x86_64 & aarch64 architectures                      │
 └──────────────────────┬─────────────────────────────────┘
                        ▼
 ┌────────────────────────────────────────────────────────┐
 │ 3. Flathub maintainers review permissions & metadata   │
 └──────────────────────┬─────────────────────────────────┘
                        ▼
 ┌────────────────────────────────────────────────────────┐
 │ 4. PR merged! A dedicated Flathub repo is created:     │
 │    https://github.com/flathub/io.github.muhaideennausar.Glyph │
 └──────────────────────┬─────────────────────────────────┘
                        ▼
 ┌────────────────────────────────────────────────────────┐
 │ 5. Glyph is live on Flathub.org and synchronizes into  │
 │    distro Software Centers worldwide                   │
 └────────────────────────────────────────────────────────┘
```

---

## 2. Pre-Submission Checklist

Before submitting, verify that the following requirements are met:

- [x] **App ID Format:** `io.github.muhaideennausar.Glyph` matches your GitHub profile domain (`muhaideennausar.github.io` / `github.com/muhaideennausar`).
- [x] **AppStream MetaInfo Valid:** `data/io.github.muhaideennausar.Glyph.metainfo.xml` passes `appstreamcli validate --pedantic`.
- [x] **Desktop Entry Valid:** `data/io.github.muhaideennausar.Glyph.desktop` passes `desktop-file-validate`.
- [x] **Tagged Release on GitHub:** Release `v0.2.2` exists on `https://github.com/muhaideennausar/glyph-text-extractor`.
- [x] **Manifest Sources:** Manifest references the public git tag `v0.2.2`.

---

## 3. Step-by-Step Submission Walkthrough

### Step 1: Fork the Flathub Repository

1. Navigate to **[https://github.com/flathub/flathub](https://github.com/flathub/flathub)** in your browser.
2. Click the **Fork** button (top right).
3. **Important:** Make sure the checkbox **"Copy the master branch only"** is **UNCHECKED**. Flathub new app submissions must go to the `new-pr` branch.

---

### Step 2: Clone Your Fork Locally

Clone your fork and specifically check out the `new-pr` branch:

```bash
# Replace with your GitHub username if different
git clone --branch=new-pr git@github.com:muhaideennausar/flathub.git ~/flathub-submission
cd ~/flathub-submission
```

_(Alternatively using GitHub CLI: `gh repo fork --clone flathub/flathub ~/flathub-submission && cd ~/flathub-submission && git checkout --track origin/new-pr`)_

---

### Step 3: Create a Submission Branch

Create a new feature branch based off `new-pr`:

```bash
git checkout -b add-glyph new-pr
```

---

### Step 4: Add the Manifest

Copy the refined manifest from the Glyph repository into your submission branch:

```bash
cp /home/nauzz/Desktop/glyph/io.github.muhaideennausar.Glyph.yaml ./io.github.muhaideennausar.Glyph.yaml
```

Check the status to ensure only this manifest file is staged:

```bash
git status
```

---

### Step 5: Commit and Push to Your Fork

```bash
git add io.github.muhaideennausar.Glyph.yaml
git commit -m "Add io.github.muhaideennausar.Glyph"
git push -u origin add-glyph
```

---

### Step 6: Open the Pull Request on Flathub

1. Go to **[https://github.com/flathub/flathub](https://github.com/flathub/flathub)**.
2. GitHub will typically show a banner: _"add-glyph had recent pushes - Compare & pull request"_. Click it.
3. **CRITICAL CHECK:** Ensure the **base repository** is `flathub/flathub` and the **base branch** is `new-pr` (do **NOT** target `master`).
4. Set the PR title:
   ```text
   Add io.github.muhaideennausar.Glyph
   ```
5. In the description, provide a brief overview:

   ```markdown
   ### Application Summary

   - **Name:** Glyph - Text Extractor
   - **ID:** `io.github.muhaideennausar.Glyph`
   - **Upstream Repository:** https://github.com/muhaideennausar/glyph-text-extractor
   - **License:** GPL-3.0-or-later
   - **Description:** Lightning-fast screen text extractor for Linux desktops inspired by PowerToys Text Extractor.
   ```

6. Click **Create pull request**.

---

## 4. What to Expect During the Review

1. **Automated CI Build (`flathubbot`):**
   - Within minutes, `flathubbot` will comment on your PR and trigger a build for `x86_64` and `aarch64`.
   - If the build succeeds, `flathubbot` will provide a one-line Flatpak install command allowing reviewers (and you) to test the exact build artifacts:
     ```bash
     flatpak install --user https://dl.flathub.org/build-repo/.../io.github.muhaideennausar.Glyph.flatpakref
     ```
2. **Review Comments:**
   - A Flathub reviewer will inspect permissions and metadata. If any adjustment is requested, simply commit and push the change to your `add-glyph` branch—the PR updates automatically.
3. **Approval & Merging:**
   - Once approved and merged by the Flathub team:
     - Flathub automatically creates a repository named `flathub/io.github.muhaideennausar.Glyph`.
     - You will receive a GitHub invitation to become a collaborator/maintainer on that repository.
     - Your app will be indexed into the Flathub CDN within 1-3 hours.

---

## 5. Managing Future Releases (v0.2.2+)

Once your app is accepted on Flathub, you will never need to touch `flathub/flathub` again.

For each future release (e.g. `v0.2.2`):

1. In your personal repo, tag and release `v0.2.2`.
2. Go to your dedicated repository at `https://github.com/flathub/io.github.muhaideennausar.Glyph`.
3. Update `io.github.muhaideennausar.Glyph.yaml`:
   - Change `tag: v0.2.1` to `tag: v0.2.2`.
   - Update `commit: <new-commit-hash>`.
4. Commit directly or open a PR to `master`. Flathub will automatically build and distribute the update to all users worldwide!
