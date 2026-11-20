# YT Automation — Setup & Run Guide

## Folder structure
```
yt_automation/
├── .env                  ← YOUR KEYS GO HERE (rename .env.template)
├── client_secrets.json   ← Downloaded from Google Cloud Console
├── requirements.txt
├── main.py               ← Run once manually to test
├── scheduler.py          ← Run to go fully automated (weekly)
├── config.py
├── logger.py
├── phase1_research.py
├── phase2_script.py
├── phase3_voiceover.py
├── phase4_assembly.py
├── phase5_upload.py
└── output/
    ├── scripts/          ← Generated JSON scripts
    ├── audio/            ← ElevenLabs .mp3 files
    ├── videos/           ← Final rendered .mp4 files
    └── logs/             ← Daily run logs
```

---

## Step 1 — Install Python dependencies
```bash
pip install -r requirements.txt
```

## Step 2 — Set up your .env file
```bash
cp .env.template .env
```
Open `.env` and paste in your API keys:
- `ANTHROPIC_API_KEY` — from console.anthropic.com
- `ELEVENLABS_API_KEY` — from elevenlabs.io profile
- `ELEVENLABS_VOICE_ID` — from ElevenLabs voice library URL
- `SHOTSTACK_API_KEY` — from shotstack.io dashboard
- `YOUTUBE_CHANNEL_ID` — UCilJ3bR8L_HCC_tEBX1ggjA (already set)

## Step 3 — Add client_secrets.json
Place your downloaded Google OAuth JSON file in the project folder.
Make sure `.env` has: `YOUTUBE_CLIENT_SECRETS=client_secrets.json`

## Step 4 — Test the pipeline once
```bash
python main.py
```
On first run, a browser window will open asking you to authorise
YouTube access. Log in with your channel's Google account.
The token is saved locally — you won't be asked again.

## Step 5 — Go fully automated
```bash
python scheduler.py
```
This runs forever. Every Monday at 09:00 it will:
1. Research a trending topic
2. Write and localise a script
3. Generate voiceover audio
4. Assemble and render the video
5. Upload to YouTube (and Rumble if configured)

Keep this terminal/process running. Use a cloud VM (e.g. Google Cloud
free tier e2-micro) or a Raspberry Pi to run it 24/7.

---

## Shotstack plan
- Sandbox (free): watermarked renders, good for testing
- Upgrade to Production ($49/mo or pay-per-render $0.05/min) when ready to publish

## ElevenLabs plan
- Free: 10,000 chars/month (~4 videos)
- Starter ($5/mo): 30,000 chars/month (~12 videos)

## Expected cost per video (at scale)
| Service       | Cost/video |
|---------------|-----------|
| Claude API    | ~$0.10    |
| ElevenLabs    | ~$0.40    |
| Shotstack     | ~$0.50    |
| Total         | ~$1.00    |

## Monetisation timeline (realistic)
- Month 1-2: Upload weekly, build library of 8+ videos
- Month 3: Hit 1,000 subscribers + 4,000 watch hours → apply for YPP
- Month 4+: AdSense revenue begins ($8-22 CPM for education niche)
- Add Rumble from day 1 — pays per view immediately, no threshold
