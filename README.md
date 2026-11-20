# gta-repo: automation for the GTA clips channel

This repo holds a copy of the FramedFacts video automation (`yt_automation/`), set up as the starting point for a
new YouTube channel of edited GTA clips.

## What was copied
The video engine and its tools:
- **Scripts and voice:** `motion_shorts.py` and the free local Kokoro voices, in English and Hindi or Hinglish.
- **Edits and captions:** word-by-word captions, sound effects and original music (`sfx.py`, `music_generator.py`), and the build and compose steps.
- **Upload:** `phase5_upload.py`, which uploads with the title, thumbnail, captions, a scheduled release and a pinned question.
- **AI pictures and clips:** `genai_clients.py`, `image_gen.py` and `realistic_video.py`, on the Google Cloud free credit, with a spending cap.
- **Checks:** `copyright_compliance.py`, plus `LESSONS.md` (every rule learned on the first channel) and `VIRAL_PLAYBOOK.md`.

## What was NOT copied
- **Secrets:** no keys, tokens or the old Bedrock key file. Each channel connects its own YouTube account (see below).
- **Old-channel data:** FramedFacts uploads, branding, notes, research data and rendered videos.

## Before this channel can post
1. **Its own YouTube login.** The uploader reads the channel's OAuth token from the environment, never from git. The owner signs in to the NEW channel once; the token is stored as an environment secret, never pasted into chat.
2. **`yt_automation/POSTING_HOLD` is on.** While that file exists the uploader refuses every upload. Delete it only when the owner says the channel may start posting.
3. **Footage rules for GTA:**
   - Rockstar's video policy allows videos made from gameplay that **you record yourself**, especially edited ones with commentary or added value.
   - **Never** re-upload other creators' clips or streams. That is copyright infringement, and YouTube refuses to monetize reused content.
   - Use official trailers only in short pieces inside commentary, and expect Content ID claims.
   - Don't make AI imitations of GTA scenes or characters, or use Rockstar logos in thumbnails.
4. **Free credit is shared.** `free_credit_ledger.json` carries the spend booked so far ($124.65 on 2026-11-19), because both channels use the SAME Google Cloud free credit. Keep one total across both repos so the $260 safety cap still holds.

## Typical flow (once footage and login are set)
raw gameplay recordings → find the best moments → cut 20-60 s vertical Shorts (or 8+ min compilations) → captions,
hook text in the first second, sound, voice-over → title and thumbnail options for the owner → the owner's OK →
upload on schedule.
