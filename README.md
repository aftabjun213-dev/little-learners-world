# 🌈 Little Learners World — Automatic Kids Cartoon Channel

This makes **one children's educational cartoon every day** and uploads it to
YouTube automatically, for **free**, using GitHub Actions. You don't need to
turn your computer on — it runs in the cloud.

Each day it:
1. 🧠 Writes a gentle story with **Claude Haiku** (very cheap)
2. 🎤 Records a warm voiceover with **edge-tts** (free)
3. 🎨 Draws cartoon pictures with **Pollinations.ai** (free)
4. 🎬 Animates them with pan/zoom + crossfades using **FFmpeg** (free)
5. 📤 Uploads to YouTube, marked **Made for Kids**, scheduled to publish at **8am**

---

## ✅ One-time setup (about 30 minutes)

You only do this once. Take it slowly, step by step.

### Step 1 — Put this project on GitHub
1. Create a **free** GitHub account if you don't have one.
2. Create a **new repository** (call it `little-learners-world`). Make it **Private**.
3. Upload all these files into it (drag and drop works on github.com).

### Step 2 — Get your YouTube refresh token (on your computer, once)
This lets the robot log in to YouTube without you.

1. Install Python 3.11+ from python.org (tick "Add to PATH" during install).
2. Open a terminal in this folder and run:
   ```
   pip install -r requirements.txt
   python scripts/get_token.py "C:\Users\YOU\Desktop\credentials.json"
   ```
   (Use the real path to your `credentials.json` from your Desktop.)
3. A browser opens — sign in with the Google account that owns your channel.
   - If it warns "Google hasn't verified this app", click **Advanced → Go to … (unsafe)**.
     This is YOUR app, it's safe.
4. The terminal prints **three values**. Keep them handy:
   - `YT_CLIENT_ID`
   - `YT_CLIENT_SECRET`
   - `YT_REFRESH_TOKEN`

### Step 3 — Add your secret keys to GitHub
In your repo on github.com: **Settings → Secrets and variables → Actions → New repository secret**.

Add these **4 secrets** (name on the left, value on the right):

| Secret name        | Value |
|--------------------|-------|
| `ANTHROPIC_API_KEY`| your Anthropic API key |
| `YT_CLIENT_ID`     | from Step 2 |
| `YT_CLIENT_SECRET` | from Step 2 |
| `YT_REFRESH_TOKEN` | from Step 2 |

Then click the **Variables** tab and add **1 variable**:

| Variable name | Value (your timezone) |
|---------------|-----------------------|
| `TIMEZONE`    | `America/Los_Angeles` |

### Step 4 — Test it
1. Go to the **Actions** tab in your repo.
2. Click **Daily Kids Video → Run workflow**.
3. Wait ~10 minutes. If it's green ✅, check YouTube — a private video
   scheduled to publish at 8am will be there!

That's it. From now on it runs **every night at 2am** by itself. 🎉

---

## 💰 Cost
- GitHub Actions, edge-tts, Pollinations, FFmpeg: **$0**
- Claude Haiku: roughly **a fraction of a cent per video** (~a few cents per month).

## 🔧 Common tweaks (optional)
- **Change the voice / speed / scene count:** edit `scripts/config.py`.
- **Change run time:** edit the `cron` line in `.github/workflows/daily.yml`.
- **Change publish hour:** add a `PUBLISH_HOUR` variable (e.g. `7`).
- **Add more episodes:** add entries to `topics.json`.

## ⚠️ Notes
- Never commit `credentials.json` or your keys — `.gitignore` already blocks them.
- YouTube allows ~6 uploads/day for new channels; 1/day is well within limits.
