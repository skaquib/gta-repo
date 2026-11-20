# FramedFacts viral playbook (long videos)

> **Read LESSONS.md first** (our mistakes and what the winners do, 2026-11-05).
>
> **Owner, 2026-11-05:** video making resumed for free 3D Shorts only (Blender on this machine, the local Kokoro voice, our own music): the food-critic rating format. No paid credit, no long videos, and no upload without the owner's approval.
> **Owner, later on 2026-11-05:** the food-critic Short was rejected; the owner approved the "Animals Complain" panda Short step by step (script A, sample frame, voice 1), then said "Now don't ask push video live": it is published as soon as it passes QA (`run_panda_short.py publish`).

Owner, 2026-11-04: "make sure high quality with trending and viral script and visual so people get the
connection and story ... keep checking this too."

Built from the videos breaking out in our niche right now (notes/2026-11-03_niche_research.md). Every
long video passes `python script_check.py run_<name>_long.py` (no MUST failures) and the visual QA below
before upload. This file gets updated when the daily trend check finds a new pattern.

## What the current hits look like (11 recent hits with chapters, Nov 2026)
- 10-19 minutes. Intro before the first chapter: **20-70 s** (median 69 s; the best run 20-50 s).
- **About 10 chapters, 60-120 s each.** Each chapter title is a mini-hook on its own:
  "The Essex: the whale that fought back", "800m: the fish that melts", "#1 Reticulated Python".
- Three structures win:
  1. **Countdown with a verdict.** #8 to #1, and a twist at the end ("only one actually can").
  2. **A journey down a scale.** Depth (200 m, 400 m, 800 m...), size, or time (era by era).
  3. **One animal, escalating facts.** "Why you'd never want to meet a ___": each chapter worse than the last.

## Script: story and connection
1. **Cold open in second person, with stakes, in the first 10 seconds.** Put the viewer inside the
   scene: "You're 2,000 metres down. It's completely dark. Something the size of a bus just changed direction."
   Never open with "Hi", "Today we", or "In this video".
2. **A promise or open question by second 30.** It tells the viewer why to stay to the end: "Only one of
   these could actually swallow you, and it's not the one you think."
3. **Each chapter: hook, fact, picture, twist.** Open with a question or a surprising line. Give one hard
   fact with a number. Make the number visible against a human. End on a line that pulls into the next
   chapter ("...and that's the small one").
4. **Re-hook at least every 2 minutes**: a question, "but here's the problem", "it gets worse".
5. **Make every number human-sized.** Not "18 metres", but "18 metres: four cars nose to tail, and you're
   this dot". Use feet as well as metres for US/UK viewers.
6. **One real story per video**: a historic event, an expedition, a study, with the year and who.
   People remember stories, not lists.
7. **Short spoken sentences** (about 10-15 words), no filler ("basically", "literally", "fun fact").
8. **Payoff at the end.** Answer the opening question and give the verdict. Then a call to action of
   1-2 lines, asking a specific question the viewer can answer in the comments.
9. **Facts:** 2+ sources each, listed in the description. No made-up "scientists say". If science is
   unsure, say so in one line; it builds trust.
10. **Every video is its own work.** New research, new script, new visuals. A series format is fine;
    copy-paste is not (YouTube's inauthentic-content rule).

## Owner rules (2026-11-04, after reviewing the first realistic video)
- **No zoom-only images.** Every shot must have real motion: animals swimming, turning, opening jaws, the camera
  diving or tracking. Stills only become shots through image-to-video (Veo); a slow zoom on a still is not motion.
- **The first seconds decide.** Open on the strongest *moving* shots, with stakes in the first words
  ("This eye is the size of a dinner plate."), and the promise of the payoff within ~10 s. No calm establishing shots
  and no scene-setting first line.
- Test 1-2 videos and read the response before making more (GROWTH_PLAN.md).

## Visuals
- **Realistic, dark and cinematic** (Vertex AI on the free credit: gemini-3.1-flash-image stills and
  veo-3.1-fast clips; see genai_clients.py). Deep blues, light shafts, particles, shallow focus.
- **A new picture every 2-4 seconds, all in motion.** Every still is animated with Veo (Lite for most shots, ~$0.03-0.05/s;
  Fast for hero shots); repeated uses of a clip show different parts of it. QA every clip and trim the part where
  the animal's anatomy drifts.
- **Scale on screen**, drawn in code so it's exact and spelled right: a human or diver silhouette next to
  the animal, size bars, a depth meter (0 m to 11,000 m), a counter for the countdown.
- **Labels, numbers and titles are drawn by our code, never by the AI.**
- **Anatomy QA on every image and clip.** Check the number of fins, legs and eyes, the teeth and the
  proportions against a real reference. Regenerate anything wrong. A wrong animal costs trust and comments.
- **Every shot must fit its place in the story, not just look good.** The AI adds animals to "empty" scenes:
  the first deep-ocean render had two fish at 10,935 m (right after "fish can't live this deep"), a shark at
  8 km and an ice ceiling at 1-11 km. Filler and establishing shots get "completely empty: no animals, no
  fish..." in both the image and the motion prompt, and the QA checks each shot against the depth, era or
  place the narration is at that moment.
- **No frozen frames.** A clip that is too short for its slot starts earlier and drifts back rather than
  stopping; the render QA runs ffmpeg freezedetect (nothing over 1 s may hold still).
- **Label it:** turn on YouTube's altered/synthetic content setting, and put "AI-generated visuals" in
  the description.

## Sound
- Natural narrator (Google Cloud Chirp 3 HD on the free credit; Charon for documentaries) at **150-165 words a
  minute**, with a breath between lines and a beat of silence on each chapter card. Charon at full speed reads
  ~186 wpm: too rushed, and it pushed the video under 8:00. Long videos stay **8:00+** (mid-roll ads).
- Calm, confident narrator, with quieter, slower lines at the scary moments. Low ambient music (deep drones
  for the deep sea), and sound effects on reveals (sonar ping, low boom). Music never louder than the voice.

## Title and thumbnail (the click)
- Title: 70 characters or fewer, with "you", a stake or superlative, or a number. Our own wording, never a
  competitor's.
- Thumbnail: one huge creature face or jaws coming out of the dark, a tiny human for scale, 2-4 words
  that **add to** the title rather than repeat it. Check it at phone size (`thumb_kit.small_preview`).
- The title and thumbnail must be true to the video. Misleading clicks lead to early exits, which hurts more.

## Before upload (QA)
1. `python script_check.py run_<name>_long.py`: no MUST failures. Fix the warnings where possible.
2. Contact sheet of every shot: anatomy, scale, no AI text, no repeats next to each other.
3. Rendered video: no black frames, no frozen frames, loudness about -15 LUFS with peaks below -1 dB, captions
   in sync, chapters in the description. A frame sheet of the hook and every chapter start.
4. Title, thumbnail, description, sources, AI label, category 27 (Education), clean tags, keyword-rich first 2 lines of the description, 3 hashtags.

## Keep checking (daily task)
- **Our numbers:** views, click-through rate, average view %, and where viewers drop off. When a chapter
  loses viewers, the next script fixes that pattern.
- **Trends:** each week, re-run the niche scan for new breakouts in the last 30 days. When a new structure
  or topic is winning, note it here and in GROWTH_PLAN.md.
- **Comments:** what viewers ask about becomes the next topics.
