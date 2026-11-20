"""
run_anime_dino.py: "The Dinosaur With Four Wings", an anime story of Kiro the Microraptor (long video, 16:9).

Owner, 2026-11-18: an anime-style dinosaur story based on true history. They liked the sample frames, approved the
script (notes/anime_dino_script.md) and picked thumbnail C ("3 SECONDS TO FLY"). The first 3 seconds come from the
END of the story (LESSONS.md checklist). Pictures come from Google's image and Veo models on the Vertex free credit
only (genai_clients caps the spend). Nothing is uploaded until the owner approves.

  python run_anime_dino.py images     # keyframes (Kiro's sheet as the reference)  -> contact sheet in scratchpad
  python run_anime_dino.py clips      # Veo lite image-to-video, 6 s each
  python run_anime_dino.py build      # voice, music, sound, frames -> output/videos/anime_dino_kiro.mp4
"""
import concurrent.futures as cf
import os
import sys
import time

import numpy as np
from PIL import Image, ImageDraw

import config
import realistic_video as rv
import motion_shorts as ms

VIDEO_ID = "anime_dino_kiro"
HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "output", "anime_dino", "style", "1_kiro.png")
THUMB = os.path.join(HERE, "output", "anime_dino", "thumbnail_final.jpg")
W, H = rv.W, rv.H
NARRATOR, KIRO = "bm_george", "am_puck"   # free local Kokoro voices (owner, 2026-11-19); the first video used Google voices
STYLE = ("Japanese 2D TV anime style: clean confident line art, cel shading, soft hand-painted watercolor backgrounds, "
         "warm cinematic lighting, expressive faces, 16:9 widescreen film frame, no text, no letters, no watermark, "
         "no logos, not photorealistic, not 3D")
CLIP_STYLE = ("2D anime animation, cel-shaded, hand-painted background, smooth expressive character animation, keep the "
              "exact anime art style, line art and colours of the starting image, widescreen 16:9, no text, no captions, "
              "no logos, no morphing")
K = "the little four-winged dinosaur Kiro from the reference image (same design, colours and big amber eyes)"
FAM = ("adult Microraptors of the same species and colours as the reference, larger than Kiro")

# key -> (image prompt, motion prompt or None for a still with a slow camera move)
SHOTS = {
    # hook: the climax first
    "h_fall": (f"{K} falling off the top of a giant conifer, eyes squeezed shut, wings half open, a towering glowing orange "
               "wall of volcanic ash and sparks rushing toward him, red sky, a lake far below", "Kiro tumbles downward through "
               "the air, ash and sparks blow past, the camera falls with him"),
    "h_fall2": (f"Close-up of {K} in mid-fall, screaming, beginning to spread all four wings, glowing ash cloud behind him",
                "his four wings snap open, feathers ruffling hard in the wind, sparks stream past"),
    "h_fossil": (f"The same falling pose of {K} now turned into a grey stone fossil skeleton with feather impressions, in a cracked "
                 "rock slab, dramatic museum spotlight", None),
    "h_press": ("A crowded 1999 press conference room in anime style, a fossil slab on a table under a cloth being pulled away, "
                "camera flashes, silhouettes of reporters from behind, no recognizable faces, no logos",
                "the cloth is pulled away and camera flashes pop all over the room"),
    "h_wings": (f"{K} on a branch, unfolding all four wings wide (two feathered arms and two feathered legs), sunlight behind",
                "he slowly spreads all four wings wide, feathers catching the light"),
    "h_crack": ("A stone slab with a bird-like fossil skeleton visibly glued together from different pieces, glowing cracks "
                "running along the glue lines", "the glued fossil splits apart along the glowing cracks, dust puffs out"),
    "h_lizard": (f"{K} swallowing a small lizard head first, comic determined face, on a mossy branch", "Kiro gulps the lizard "
                 "down, his throat bulges, he blinks proudly"),
    "h_dawn": (f"Calm golden dawn in a misty Early Cretaceous conifer forest beside a lake, {K} asleep curled on a high branch",
               "mist drifts, light rays slowly brighten, Kiro breathes gently in his sleep"),
    # 1. the forest of lakes
    "c1_aerial": ("Wide aerial view of a land of misty forests and wide quiet lakes, giant conifers, distant volcanoes with thin "
                  "smoke on the horizon, Early Cretaceous, morning", "slow aerial glide forward over the lakes and forest"),
    "c1_volcano_far": ("Distant volcanoes on the horizon gently smoking at sunrise beyond a calm lake, ferns in the foreground",
                       "smoke curls slowly from the volcanoes, ripples move on the lake"),
    "c1_dive": ("Looking down into the canopy of giant mossy conifers, sun shafts falling between trunks",
                "the camera dives down between the tree trunks through the sun shafts"),
    "c1_branch": (f"{K} perched on a high mossy branch, looking around curiously, forest below",
                  "Kiro tilts his head left and right, tail swishing"),
    "c1_crow": (f"{K} standing on the forest floor among ferns beside a large pinecone and a fallen log, low ground-level camera, showing he is only about the size of a crow",
                "Kiro hops along the branch and pecks at the pinecone"),
    "c1_feathers": (f"Close-up of {K}'s black feathers shining iridescent blue in a sunbeam", "he shakes his feathers and the "
                    "blue shine ripples across them"),
    "c1_four": (f"{K} stretching, clearly showing four wings: long flight feathers on both arms and on both legs, side view",
                "he stretches his arm wings and then his leg wings, feathers fanning out"),
    "c1_face": (f"Extreme close-up portrait of {K}'s face filling the frame, small and cute, big amber eyes, a little nervous smile, soft bokeh forest", "Kiro blinks and gives a shy smile"),
    "c1_down": (f"{K} peering over the edge of a very high branch at the dizzying drop to the forest floor far below",
                "Kiro leans over, looks down, gulps and shuffles back"),
    # 2. afraid to jump
    "c2_glide": (f"Two young Microraptors (same species and colours as {K}, a little bigger) gliding between giant trees over "
                 "a blue lake, morning light", "the two young dinosaurs glide gracefully between the trunks"),
    "c2_glide_lake": ("Two young four-winged feathered dinosaurs gliding low over a shining lake, reflections in the water, "
                      "same anime style", "they skim over the water, wingtips almost touching the surface"),
    "c2_watch": (f"{K} sitting alone on a branch watching his siblings glide away, wistful face", "Kiro's eyes follow them, he "
                 "sighs and his feathers droop"),
    "c2_sunset": (f"{K} on the same branch at sunset, silhouetted, chin on his claws", "the sun sinks, clouds drift"),
    "c2_edge": (f"View from behind {K} at the very tip of a thin branch, one foot forward over a huge drop to a lake far below, wings trembling", "he lifts one foot "
                "forward, freezes, then quickly steps back"),
    "c2_mother_glide": (f"An adult Microraptor ({FAM}) gliding in slow motion with all four wings spread, side view",
                        "slow-motion glide, every feather visible"),
    "c2_flap": ("A four-winged feathered dinosaur flapping its arm wings hard like a bird to climb into the air",
                "it flaps powerfully and rises"),
    "c2_paper": ("A four-winged feathered dinosaur gliding motionless like a paper plane, all four wings spread flat, seen "
                 "from below against the sky", "it sails smoothly across the sky without flapping"),
    "c2_feather": ("Macro view of a long asymmetric flight feather, glossy black with a blue shine, wind ruffling it",
                   "the feather vane ripples in the breeze"),
    "c2_mother_lands": (f"An adult Microraptor ({FAM}) landing softly beside {K} on a branch and nudging him with her snout",
                        "she lands, folds her wings and gently nudges Kiro"),
    "c2_fish": (f"A small silver fish dropped at the feet of {K} on a branch, his hungry happy face", "Kiro looks at the fish, "
                "then up at his mother, and smiles"),
    # 3. hunger
    "c3_rain": (f"Rain pouring on a dark forest, {K} and his family huddled thin and wet on a branch", "rain falls, they "
                "shiver and huddle closer"),
    "c3_fossil_fish": ("A stone fossil of a Microraptor skeleton with the bones of a small fish visible inside its ribcage, "
                       "museum lighting, the fish bones highlighted with a soft glow", None),
    "c3_fossil_bird": ("A stone fossil of a Microraptor skeleton with the tiny bones of a small bird inside its belly area, "
                       "museum lighting, soft glow on the bird bones", None),
    "c3_fossil_lizard": ("A stone fossil of a Microraptor skeleton with a whole small lizard skeleton inside its belly, head "
                         "pointing forward as if swallowed head first, soft glow on the lizard", None),
    "c3_lizard": (f"{K} lunging clumsily at a small lizard on a branch, the lizard dashing away", "Kiro pounces and misses as "
                  "the lizard scurries away"),
    "c3_bird": (f"{K} snapping at a small early bird that flutters away just out of reach", "the bird flutters off, Kiro "
                "snaps at empty air and wobbles"),
    "c3_below": (f"View past {K}'s shoulder down at a lake full of jumping fish far below the tree", "fish leap and splash in "
                 "the lake below, Kiro's stomach growls, he licks his snout"),
    "c3_wind": (f"{K} at the edge of the branch, wings half open, strong wind pushing his feathers", "wind gusts ruffle his "
                "feathers, he leans forward"),
    "c3_thunder": (f"Lightning flashes over the forest, {K} scrambling back to the trunk in fright", "a lightning flash, Kiro "
                   "jumps in fright and scrambles back"),
    # 4. the mountain wakes
    "c4_quiet": ("An eerily still forest at morning, motionless leaves, the lake surface trembling with tiny ripples",
                 "the lake surface trembles, then everything is still"),
    "c4_birds": ("Hundreds of small early birds bursting out of the trees all at once into the sky", "the birds explode out "
                 "of the canopy and flee"),
    "c4_erupt": ("A volcano on the horizon erupting violently, a huge column of ash and glowing lava, seen across a lake",
                 "the volcano blasts a towering ash column upward, the ground shakes"),
    "c4_ashwall": ("A towering grey-orange wall of volcanic ash rolling across the land toward the forest",
                   "the ash cloud rolls forward and swallows the distant trees"),
    "c4_snow": (f"Grey ash falling softly like snow onto {K} on his branch", "ash flakes drift down and settle on his feathers"),
    "c4_flow": ("A glowing pyroclastic flow racing over the ground, trees smoking and charring", "the hot ash surges forward "
                "and the trees blacken"),
    "c4_flee": (f"Adult and young Microraptors ({FAM}) gliding away over the lake, fleeing the ash cloud",
                "the family glides away fast over the water"),
    "c4_alone": (f"{K} alone on the treetop, ash falling, looking across the lake toward his family, crying out",
                 "Kiro calls out, ash swirls around him"),
    "c4_calls": (f"Across the lake, an adult Microraptor ({FAM}) calling out from a far ridge", "she calls out, wings raised"),
    # 5. four wings
    "c5_jump": (f"{K} closing his eyes and leaping off the treetop, all four wings opening, ash cloud behind",
                "Kiro leaps off the branch with his eyes closed"),
    "c5_fall": (f"{K} dropping fast, wings flailing, the lake rushing up below", "he drops, flailing, the water rushes closer"),
    "c5_catch": (f"{K} as the wind catches him, all four wings spread wide and steady, eyes opening in wonder",
                 "the air catches him, he stops falling and glides, his eyes open wide"),
    "c5_glide": (f"{K} gliding over a wide lake at sunset, a volcano erupting far behind, speed lines, fierce courage",
                 "Kiro glides fast over the lake, wind streaks past"),
    "c5_fish": (f"{K} swooping low over the water and snatching a fish in his jaws", "he skims the water and snaps up a fish "
                "without slowing"),
    "c5_joy": (f"{K} gliding upward with a huge joyful grin, a fish in his jaws, golden light", "he rises, laughing with joy"),
    "c5_reunion": (f"{K} landing beside his family ({FAM}) on a far ridge, his mother pressing her head to his",
                   "Kiro lands and his mother presses her head to his"),
    "c5_cloud": (f"Back view of {K} and three larger black feathered four-winged Microraptors (all black with a blue sheen, same design as the reference) sitting on a rocky ridge, watching a grey ash cloud swallow the distant forest",
                 "the ash cloud slowly covers the old forest"),
    # 6. what the ash kept
    "c6_settle": ("Ash settling over a still lake bed in soft grey layers", "ash drifts down and settles in layers"),
    "c6_layers": ("A cross-section of rock layers forming over millions of years, a time-lapse feel, a fossil in the bottom "
                  "layer", "layers stack up and harden into rock"),
    "c6_forming": ("A small four-winged dinosaur skeleton with feather outlines being pressed into fine grey stone",
                   "the stone slowly forms around the skeleton and feathers"),
    "c6_feather_fossil": ("Close-up of fossil feathers preserved in grey stone, fine detail", None),
    "c6_microscope": ("Anime scientist's view through a microscope of tiny rod-shaped pigment cells in a fossil feather, "
                      "glowing blue-black", None),
    "c6_color": ("A stone fossil of a four-winged dinosaur whose feathers fill with glossy black-and-blue colour",
                 "colour flows into the fossil feathers, shimmering blue"),
    # 7. the fake
    "c7_farmer": ("1990s rural northeast China, a farmer (seen from behind) splitting a flat stone slab with a chisel, revealing "
                  "a fossil skeleton", "the slab splits open and reveals the fossil"),
    "c7_slab": ("A flat slab with a feathered dinosaur skeleton just revealed, dust in the air", None),
    "c7_market": ("A dim 1990s back room with fossil slabs for sale on tables, hands exchanging money, no faces", None),
    "c7_glue": ("Hands gluing a fossil bird body and a separate dinosaur tail into one stone slab, glue and filler",
                "the hands press the pieces together and smear glue"),
    "c7_magazine": ("A glossy science magazine cover in anime style showing a bird-like fossil, the title area blank, "
                    "no logos, no readable text", None),
    "c7_scientist": ("A palaeontologist seen from behind in a lab, studying a fossil tail through a magnifying glass, no face "
                     "shown", "he leans in closer with the magnifying glass"),
    "c7_search": ("A palaeontologist (back view, no face) searching through shelves of fossil slabs in a private collection",
                  "he slides a slab out of a shelf"),
    "c7_match": ("Close-up on a lab table with an adult palaeontologist's gloved hands (no face, no children): two halves of a split fossil slab placed side by side, the tail on one half matching the other perfectly, a "
                 "glowing outline along the match", None),
    "c7_tail": ("A fossil dinosaur tail in stone, glowing blue", "the tail glows brighter and pulses"),
    "c7_tokiro": (f"The fossil tail transforming into the living feathered tail of {K}", "the stone tail turns into a living "
                  "feathered tail that swishes away"),
    "c7_full": ("A complete stone fossil of a four-winged dinosaur with long feathers clearly on the arms and the legs", None),
    # 8. ending
    "c8_museum": ("A museum at night, a Microraptor fossil glowing in a glass case, a child pressing their face to the glass",
                  "the child's breath fogs the glass, the fossil glows softly"),
    "c8_shadow": (f"The shadow of {K} gliding across a museum wall above a fossil case", "the shadow glides across the wall"),
    "c8_sunset": (f"{K} perched on a high branch at sunset, wings folded, smiling, looking at the viewer", "Kiro looks at "
                  "the viewer and tilts his head with a smile"),
}


def S(line, *shots, voice=None, chapter=None, label=None, sfx=None, cta=None, gap=None, card=None):
    d = dict(line=line, shots=list(shots), chapter=chapter, label=label, sfx=sfx, cta=cta, card=card)
    if voice:
        d.update(voice=voice, speed=1.12)
    if gap is not None:
        d["gap"] = gap
    return d


SEGMENTS = [
    # ── hook: the most exciting moment first (owner rule, 2026-11-18) ──
    S("Mama!", "clip:h_fall", voice=KIRO, sfx="boom", gap=0.15),
    S("This little dinosaur has three seconds to learn to fly... or he dies.", "clip:h_fall2", gap=0.25),
    S("And a hundred and twenty million years later, his kind would expose one of the biggest fossil frauds in history.",
      "img:h_fossil", "clip:h_press", sfx="flash"),
    S("A dinosaur with four wings.", "clip:h_wings", gap=0.2),
    S("A fake that fooled the world.", "clip:h_crack", sfx="crack", gap=0.2),
    S("And it's all true.", "clip:h_lizard", gap=0.3),
    S("To see how he got here, we have to go back to the morning he was too scared to jump.", "clip:h_dawn", card="title",
      sfx="rewind"),
    # ── 1 ──
    S("One hundred and twenty million years ago, in what is now northeast China, there was a land of forests and wide, "
      "quiet lakes,", "clip:c1_aerial", chapter="120 million years ago", label="NORTHEAST CHINA"),
    S("with volcanoes always smoking at the edge of the sky.", "clip:c1_volcano_far"),
    S("In the treetops lived one of the strangest dinosaurs that ever lived: Microraptor.", "clip:c1_dive", "clip:c1_branch",
      label="MICRORAPTOR"),
    S("About the size of a crow.", "clip:c1_crow"),
    S("Black feathers that shone blue in the sun.", "clip:c1_feathers"),
    S("And not two wings, but four: long flight feathers on its arms, and on its legs too.", "clip:c1_four", label="4 WINGS"),
    S("This one is Kiro. He is small, even for a Microraptor.", "clip:c1_face", label="KIRO"),
    S("And he has a secret. He has never once left the branch.", "clip:c1_down"),
    # ── 2 ──
    S("His brother and sister glide from tree to tree, as if the air were a road.", "clip:c2_glide", "clip:c2_glide_lake",
      chapter="Afraid to jump"),
    S("Kiro watches. Every day, he watches.", "clip:c2_watch", "clip:c2_sunset"),
    S("Tomorrow. I'll do it tomorrow.", "clip:c2_edge", voice=KIRO),
    S("Scientists today still argue about exactly how Microraptor flew.", "clip:c2_mother_glide"),
    S("Did it flap like a bird, or mostly glide, using all four wings like a paper plane?", "clip:c2_flap", "clip:c2_paper"),
    S("Its feathers were built for the air. Kiro just has to trust them.", "clip:c2_feather", "clip:c2_mother_lands",
      "clip:c2_fish"),
    # ── 3 ──
    S("We know what Microraptors ate, because some of them died with their last meal still inside.", "clip:c3_rain",
      "img:c3_fossil_fish", chapter="Hunger"),
    S("Paleontologists have found Microraptor fossils with a fish in the stomach.", "img:c3_fossil_fish", label="FISH"),
    S("Another with a small bird.", "img:c3_fossil_bird", label="BIRD"),
    S("Another with a whole lizard, swallowed head first.", "img:c3_fossil_lizard", label="LIZARD"),
    S("I can't catch anything from up here.", "clip:c3_lizard", "clip:c3_bird", voice=KIRO),
    S("The food is down by the lake, and the fastest way there is through the air.", "clip:c3_below", "clip:c3_wind",
      "clip:c3_thunder", sfx="thunder"),
    # ── 4 ──
    S("Then, one morning, the forest went quiet.", "clip:c4_quiet", "clip:c4_birds", chapter="The mountain wakes"),
    S("This land sat beside some of the busiest volcanoes on Earth.", "clip:c4_erupt", sfx="boom"),
    S("Again and again, they buried the forests and lakes under clouds of ash.", "clip:c4_ashwall", sfx="rumble"),
    S("Some of the ash fell softly, like snow.", "clip:c4_snow"),
    S("Some came racing over the ground, hot enough to char wood.", "clip:c4_flow", sfx="fire"),
    S("Every animal had one choice: get away, now.", "clip:c4_flee"),
    S("Across the lake, his family was calling him.", "clip:c4_calls", "clip:c4_alone"),
    S("Mama!", "clip:c4_alone", voice=KIRO),
    # ── 5 ──
    S("Kiro jumped.", "clip:c5_jump", chapter="Four wings", sfx="whoosh", gap=0.35),
    S("For one terrible second, he fell.", "clip:c5_fall", sfx="wind", gap=0.35),
    S("Then the air caught him: four wings, spread wide, holding him up like the open hand of the sky.", "clip:c5_catch",
      "clip:c5_glide", sfx="riser"),
    S("I'm flying! I'm actually flying!", "clip:c5_fish", "clip:c5_joy", voice=KIRO, sfx="splash"),
    S("He landed beside his family, safe, as the grey cloud swallowed the old forest.", "clip:c5_reunion", "clip:c5_cloud"),
    # ── 6 ──
    S("Not every animal escaped the ash.", "clip:c6_settle", chapter="What the ash kept"),
    S("And that is the strange gift of this place.", "clip:c6_layers"),
    S("The eruptions that killed them also buried them so fast that their bones, and even their feathers, were kept in "
      "stone.", "clip:c6_forming", "img:c6_feather_fossil"),
    S("That is why today we know Microraptor's colour: scientists found its tiny pigment cells, still preserved, and they "
      "matched shiny black feathers with a blue shine.", "img:c6_microscope", "clip:c6_color"),
    # ── 7 ──
    S("One hundred and twenty million years later, farmers in this part of China split open slabs of rock and found "
      "feathered skeletons.", "clip:c7_farmer", "img:c7_slab", chapter="The fake that hid a real dinosaur", label="1990s"),
    S("Some were sold.", "img:c7_market"),
    S("In the 1990s, one fossil was glued together from the body of an early bird and the tail of something else, and sold "
      "as a single animal.", "clip:c7_glue", "img:h_fossil"),
    S("In 1999 it was shown to the world as the missing link.", "clip:h_press", "img:c7_magazine", label="1999", sfx="flash"),
    S("A Chinese scientist, Xu Xing, looked at that tail and didn't believe it.", "clip:c7_scientist", label="XU XING"),
    S("He searched private collections in China and found the matching other half of the slab.", "clip:c7_search",
      "img:c7_match"),
    S("The tail had never belonged to a bird at all.", "clip:c7_tail", sfx="boom"),
    S("It belonged to a small, unknown dinosaur. In 2000, it was given a name: Microraptor.", "clip:c7_tokiro",
      label="MICRORAPTOR, 2000"),
    S("A few years later, more complete fossils showed something no one expected: four wings.", "img:c7_full",
      "clip:c1_four"),
    # ── 8 ──
    S("The fake was forgotten. The little dinosaur with four wings was not.", "clip:c8_museum", "clip:c8_shadow"),
    S("Which dinosaur should get their story next? Tell us in the comments, and subscribe so you don't miss it.",
      "clip:c8_sunset", cta="subscribe"),
]

SCRIPT = {
    "title": "The Dinosaur With Four Wings 🦖 An Anime Story From 120 Million Years Ago",
    "hook": SEGMENTS[1]["line"],
    "body": " ".join(s["line"] for s in SEGMENTS[2:]),
    "cta": SEGMENTS[-1]["line"],
    "format": "long",
}


# ── assets ────────────────────────────────────────────────────────────────────
def gen_images(workers=3):
    from google.genai import types
    import genai_clients as g
    c = dict(g.clients())["vertex"]
    ref = open(REF, "rb").read()
    d = rv.asset_dir(VIDEO_ID)

    def one(key):
        out = os.path.join(d, f"{key}.png")
        if os.path.exists(out):
            return key, "cached"
        prompt = SHOTS[key][0]
        modern = key.startswith(("c7_", "c8_", "h_press", "h_crack", "c6_microscope"))
        extra = "" if modern else (" Prehistoric scene 120 million years ago: absolutely NO humans, NO people, NO children, "
                                   "NO buildings, NO boats, no man-made objects.")
        parts = [prompt + "." + extra + " Style: " + STYLE]
        if "Kiro" in prompt or "Microraptor" in prompt or "four-winged" in prompt:
            parts = [types.Part.from_bytes(data=ref, mime_type="image/png"),
                     ("Use the reference image ONLY for the character design and the art style. Do NOT copy its composition, pose, "
                      "branch or background: use the new camera angle, pose and setting described here. ")] + parts
        last = None
        for model in ("gemini-3-pro-image", "gemini-3.1-flash-image"):
            for attempt in range(5):
                try:
                    g.charge("image", 1, f"{VIDEO_ID}/{key}")
                    r = c.models.generate_content(model=model, contents=parts, config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"], image_config=types.ImageConfig(aspect_ratio="16:9")))
                    data = next(p for p in r.candidates[0].content.parts if p.inline_data).inline_data.data
                    with open(out, "wb") as f:
                        f.write(data)
                    return key, model
                except Exception as e:
                    last = e
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        time.sleep(20 * (attempt + 1))
                        continue
                    break
        return key, f"FAILED {str(last)[:120]}"

    with cf.ThreadPoolExecutor(workers) as ex:
        return dict(ex.map(one, SHOTS))


def gen_clips():
    clips = {k: v[1] for k, v in SHOTS.items() if v[1]}
    return rv.gen_clips(clips, VIDEO_ID, seconds=6, model="veo-3.1-lite-generate-001", batch=6, style=CLIP_STYLE)


# ── picture: our own overlays on top of the anime shots ───────────────────────
def chapter_card(title):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    band = np.zeros((H, W, 4), np.uint8)
    yy = np.linspace(0, 1, H)[:, None]
    band[..., 3] = (np.clip((yy - 0.62) / 0.38, 0, 1) * 190).astype(np.uint8)
    im.alpha_composite(Image.fromarray(band, "RGBA"))
    d = ImageDraw.Draw(im)
    d.text((110, 900), title.upper(), font=rv.font(66, 900), fill=(255, 214, 70), stroke_width=5, stroke_fill=(0, 0, 0))
    return im


def title_card(p):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    a = int(255 * min(1.0, p / 0.15) * min(1.0, (1 - p) / 0.15))
    d.text((W / 2, H / 2 - 40), "THE DINOSAUR WITH FOUR WINGS", font=rv.font(92, 900), fill=(255, 214, 70, a),
           anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0, a))
    d.text((W / 2, H / 2 + 60), "Kiro is imagined. The clues are real.", font=rv.font(40, 600), fill=(255, 255, 255, a),
           anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0, a))
    return im


_cards = {}


def frame_fn():
    uses, offset = {}, {}
    for i, s in enumerate(SEGMENTS):
        for k, sh in enumerate(s["shots"]):
            key = sh.split(":", 1)[1]
            n = uses.get(key, 0)
            offset[(i, k)] = (n * 2.5) % 4.0
            uses[key] = n + 1

    def frame(t, i, t_in, starts):
        seg = SEGMENTS[i]
        dur = (starts[i + 1] - starts[i]) if i + 1 < len(starts) else 6.0
        shots = seg["shots"]
        n = len(shots)
        k = min(n - 1, int(t_in / (dur / n)))
        sd, ts = dur / n, t_in - k * (dur / n)
        key = shots[k].split(":", 1)[1]
        if rv.has_clip(VIDEO_ID, key):
            base = rv.frame_clip(VIDEO_ID, key, ts, sd, start=offset.get((i, k), 0.0))
        else:
            base = rv.frame_still(VIDEO_ID, key, min(1.0, ts / sd), hash((i, k)) & 0xFFFF)
        if i == 1 and t_in < 0.5:                       # the freeze as his wings open, with a flash
            base = np.clip(base.astype(np.int16) + int(90 * (1 - t_in / 0.5)), 0, 255).astype(np.uint8)
        out = Image.fromarray(base).convert("RGBA")
        if seg.get("chapter"):
            a = min(1.0, t_in / 0.4) * min(1.0, max(0.0, (3.2 - t_in) / 0.5))
            if a > 0:
                c = _cards.setdefault(seg["chapter"], chapter_card(seg["chapter"]))
                out.alpha_composite(rv._fade(c, a))
        if seg.get("card") == "title":
            out.alpha_composite(title_card(min(1.0, t_in / dur)))
        if seg.get("label"):
            a = min(1.0, max(0.0, (t_in - 0.3) / 0.35)) * min(1.0, max(0.0, (dur - t_in) / 0.4))
            if a > 0:
                out.alpha_composite(rv._fade(rv.label_tag(seg["label"]), a), (90, 120))
        if seg.get("cta"):
            out.alpha_composite(rv.cta_overlay(seg["cta"], min(1.0, t_in / dur)))
        d = ImageDraw.Draw(out)
        d.text((40, 34), "FramedFacts", font=rv.font(24, 800), fill=(255, 255, 255, 120))
        return np.asarray(out.convert("RGB"))
    return frame


# ── sound ─────────────────────────────────────────────────────────────────────
def sound_events(starts, total):
    import sfx
    kinds = {"boom": lambda: sfx.deep_boom(0.7), "crack": lambda: sfx.crack(0.6), "flash": lambda: sfx.zap(0.4, 0.3),
             "rewind": lambda: sfx.riser(0.9, 0.35), "thunder": lambda: sfx.thunder(2.5, 0.6, 0.5),
             "rumble": lambda: sfx.deep_boom(0.5), "fire": lambda: sfx.fire(3.0, 0.18), "whoosh": lambda: sfx.whoosh(0.5, 0.5),
             "wind": lambda: sfx.wind(2.0, 0.35), "riser": lambda: sfx.riser(1.2, 0.4), "splash": lambda: sfx.splash(0.45)}
    ev = []
    for s, st in zip(SEGMENTS, starts):
        if s.get("sfx") in kinds:
            ev.append((max(0.0, st - 0.05), kinds[s["sfx"]]()))
        if s.get("chapter"):
            ev.append((st, sfx.whoosh(0.6, 0.3)))
    return ev


def build():
    out, vo = ms.render_short(SCRIPT, SEGMENTS, VIDEO_ID, frame_fn(), voice=NARRATOR, speed=0.95, music_style="emotional",
                              sfx_fn=sound_events, music_vol=0.10, hook_hit=False, gap_s=0.5, chapter_pause_s=0.7)
    import subprocess
    tmp = out.replace(".mp4", "_norm.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", out, "-c:v", "copy", "-af", "loudnorm=I=-15:TP=-1.5:LRA=9",
                    "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, out)
    return out


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    D = "/tmp/claude-0/-home-user-youtubeautomation/7fff9e34-920a-5cff-ba6a-cebf90c2f14e/scratchpad"
    missing = {sh.split(":", 1)[1] for s in SEGMENTS for sh in s["shots"]} - set(SHOTS)
    assert not missing, missing
    if cmd == "images":
        print(gen_images())
        rv.contact_sheet(VIDEO_ID, list(SHOTS), os.path.join(D, "kiro_assets.jpg"), cols=8)
    elif cmd == "clips":
        print(gen_clips())
    elif cmd == "build":
        print(build())
    else:
        print(__doc__)


# ── publishing (owner OK, 2026-11-19: "Post the long video on 9 am") ──────────
STARTS = [0.05, 0.63, 4.36, 10.44, 12.27, 14.07, 15.62, 19.66, 27.07, 30.56, 36.48, 38.04, 40.69, 46.8, 51.44, 56.4,
          61.95, 66.14, 68.63, 72.68, 78.45, 82.43, 88.4, 93.13, 95.13, 98.56, 100.54, 105.84, 109.86, 113.73, 118.88,
          122.39, 126.43, 129.66, 132.38, 133.31, 135.18, 137.6, 143.76, 146.19, 151.16, 154.57, 157.45, 163.74, 173.47,
          182.19, 183.71, 191.71, 195.39, 200.07, 204.93, 207.69, 213.67, 219.45, 225.25]     # from the build log
SOURCES = """Sources:
- Archaeoraptor (1999) and Microraptor: Wikipedia "Archaeoraptor"; Cosmos, "The great dinosaur fossil hoax"; Scientific American, "How Fake Fossils Pervert Paleontology"
- Four wings and iridescent black feathers (Li et al., Science 2012): Mental Floss, "10 Feathered Facts About Microraptor"; Pteros, "Jiufotang Formation"
- Stomach contents (fish, bird, lizard Indrasaurus): National Geographic, "There's something fishy about Microraptor"; Everything Dinosaur; Gizmodo
- Volcanic ash and the Jehol Biota: Nature Communications (2014) ncomms4151; AMNH, "Animal Pompeii"; Scientific American, "Pompeii-Like Eruption Fossilized Dinosaurs in Death Poses"; Burnham, review of the Jehol Group"""


def description():
    rows = ["0:00 Three seconds to fly"]
    for seg, st in zip(SEGMENTS, STARTS):
        if seg.get("chapter"):
            s = int(st)
            rows.append(f"{s // 60}:{s % 60:02d} {seg['chapter']}")
    return ("120 million years ago in northeast China lived Microraptor, a crow-sized dinosaur with FOUR wings and shiny "
            "black feathers. This is the anime story of Kiro, a little Microraptor too scared to jump, until the volcano "
            "woke up. And 120 million years later, his kind exposed one of the biggest fossil frauds in history: the "
            "1999 'missing link', Archaeoraptor.\n\n"
            "Kiro and his family are imagined. Everything about Microraptor, its world, its food, the volcanoes and the "
            "fossil scandal is real.\n\n" + "\n".join(rows) + "\n\n"
            "Animation: made with AI image and video tools (Google Gemini and Veo), directed and checked by FramedFacts.\n\n"
            + SOURCES + "\n\nWhich dinosaur should get their story next? Tell us in the comments!\n\n"
            "#dinosaur #anime #microraptor")


def publish():
    import config as cfg
    import phase5_upload as p5
    import pro_shorts_creator as psc
    out = os.path.join(cfg.VIDEOS_DIR, f"{VIDEO_ID}.mp4")
    vo = os.path.join(cfg.AUDIO_DIR, f"{VIDEO_ID}_vo.wav")
    script = dict(SCRIPT, video_title=SCRIPT["title"], seo_description=description(), publish_at="2026-11-19T03:35:00Z",
                  tags=["dinosaur", "dinosaur story", "anime", "microraptor", "four winged dinosaur", "archaeoraptor",
                        "fossil hoax", "jehol", "prehistoric", "dinosaur animation", "anime story"])
    cfg.UPLOAD_PRIVACY = "public"
    url, _ = p5.upload_to_youtube(out, script, {"title": SCRIPT["title"], "subject": SCRIPT["hook"], "category": "Animals"})
    vid = url.rsplit("=", 1)[-1]
    print("uploaded", vid, flush=True)
    p5.upload_thumbnail(vid, THUMB)
    srt = os.path.splitext(vo)[0] + ".srt"
    psc.generate_srt(psc.get_word_timestamps(vo), srt)
    p5.upload_captions(vid, srt)
    p5.post_engagement_comment(vid, "Kiro jumped. Would you have? 🦖 Which dinosaur should get the next anime story?")
    return vid


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "publish":
    print(publish())
