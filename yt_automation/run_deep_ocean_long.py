"""
run_deep_ocean_long.py — "The Biggest Monster in Every Ocean Layer, Shown Next to You"

First video of the "___, Shown Next to You" series (main niche from 2026-11-03: extreme
animals shown to scale). Why this topic: creatures-per-ocean-layer videos are pulling
millions right now (2.2M, 2.7M) while "what would kill you at every depth" copies are
flopping, so we take the layer journey and add our own angle: every monster next to you.

Realistic visuals: Gemini stills + Veo clips on the Vertex free credit (realistic_video.py),
labelled as AI. Every number on screen is drawn in code. Facts: 2+ sources each (SOURCES).

  python run_deep_ocean_long.py assets     # stills + cut-outs (cached), contact sheet
  python run_deep_ocean_long.py clips      # Veo clips from the chosen stills
  python run_deep_ocean_long.py preview    # one tile per shot with overlays
  python run_deep_ocean_long.py build      # thumbnail + full render
"""
import os
import sys

import config

config.assert_safe_pipeline()

import motion_shorts as ms
import realistic_video as rv

VIDEO_ID = "deep_ocean_long"
VOICE = "en-US-Chirp3-HD-Charon"     # Google Cloud natural voice on the free credit (deep, calm documentary read)
# Pacing: at rate 1.0 Charon reads ~186 words/min (too fast, 7:56 total). 0.85 + a breath between lines and a
# pause before each chapter gives ~160 wpm, the documentary norm; the hook keeps shorter gaps so it stays punchy.
VOICE_RATE, LINE_GAP, CHAPTER_PAUSE, HOOK_GAP = 0.85, 0.45, 0.8, 0.3
HERE = os.path.dirname(os.path.abspath(__file__))
THUMB = os.path.join(HERE, "output", "thumbnails", f"{VIDEO_ID}.jpg")


def S(line, *shots, chapter=None, depth=None, label=None, sfx=None, chapter_card=True, cta=None):
    return dict(line=line, shots=list(shots), chapter=chapter, depth=depth, label=label, sfx=sfx, chapter_card=chapter_card,
                cta=cta)


SEGMENTS = [
    # ── cold open: the three strongest moving shots first, stakes from the first word ──
    S("This eye is the size of a dinner plate.", "clip:giantsquid_eye", chapter="Intro", depth=0, chapter_card=False, sfx="boom"),
    S("This whale hunts two kilometres down, in total darkness.", "clip:sperm_whale_shadow", sfx="boom"),
    S("And this shark could be four hundred years old.", "clip:greenland_shark", sfx="boom"),
    S("They all live in the ocean right below you.", "clip:surface_pov", "clip:surface_below"),
    S("And what's waiting at the very bottom, eleven kilometres down? Not what anyone expected.",
      "clip:trench_dark", "clip:challenger_deep"),     # no spoiler: the bag is only revealed at the end
    S("So let's sink, one layer at a time, and put every monster right next to you.", "clip:diver_descend_blue", "clip:descend_twilight"),

    # ── 0 m ──────────────────────────────────────────────────────────────────
    S("Look down. Something the length of a basketball court is gliding underneath you.",
      "img:bluewhale_wide", "img:montage_whale", chapter="The biggest animal that ever lived", depth=0, label="BLUE WHALE"),
    S("A blue whale. It can grow to about thirty metres, the largest animal known to have ever existed.",
      "img:bluewhale_close", "img:bluewhale_court", label="BLUE WHALE"),
    S("Lie down next to one, and it would take about seventeen of you, head to toe, to match it.", "scale:bluewhale"),
    S("And it lives on krill, animals about as long as your little finger.", "img:krill_swarm", "img:bluewhale_feeding"),
    S("When it dives, its heart can slow to just two beats a minute. Yours beats about sixty times in that time.",
      "img:bluewhale_close", "img:bluewhale_wide"),
    S("But the blue whale won't hurt you. The thing up here you should actually worry about is almost invisible.",
      "img:box_jelly_dark", "img:box_jelly_tentacles"),
    S("The Australian box jellyfish. Its tentacles can trail up to three metres behind it.",
      "clip:box_jelly_close", label="BOX JELLYFISH"),
    S("Most stings aren't deadly. But in the cases that were, death usually came within minutes.",
      "img:box_jelly_tentacles", "img:box_jelly_dark"),
    S("And this is the friendly part of the ocean. Let's go down.", "img:diver_descend_blue"),

    # ── 40 m ─────────────────────────────────────────────────────────────────
    S("Ten metres down, the water above you has already doubled the pressure on your body.",
      "img:diver_10m", chapter="Where your brain gets drunk", depth=40),
    S("Your body is mostly water, and water barely squeezes. But the air inside you does.",
      "img:diver_lungs", "img:diver_dark_blue"),
    S("At ten metres, the air in your lungs is pressed to half its size. At thirty metres, to a quarter.",
      "img:diver_dark_blue", "img:diver_lungs"),
    S("Movies show people crushed flat by the deep. That's not really what happens. It's the air spaces in you that collapse.",
      "img:diver_dizzy", "img:surface_below"),
    S("And below about thirty metres, something stranger begins: nitrogen narcosis.", "img:diver_narcosis"),
    S("Divers call it Martini's law. Every ten metres deeper can feel like another drink.",
      "img:diver_narcosis", "img:diver_dizzy"),
    S("It's one big reason most recreational dive courses stop at forty metres.", "img:diver_40m", "img:diver_dark_blue"),
    S("The deepest anyone has ever gone on scuba? In 2014, Ahmed Gabr reached three hundred and thirty-two metres, off Egypt.",
      "img:scuba_record", "img:descend_twilight", depth=332),
    S("Going down took about twelve minutes. Coming back up safely took around fourteen hours.",
      "img:diver_decompression", "img:scuba_record"),
    S("And for the ocean, three hundred metres is barely the beginning.", "img:descend_twilight"),

    # ── 200-1,000 m ──────────────────────────────────────────────────────────
    S("This is the twilight zone. The sunlight is almost gone, and everything is a deep, cold blue.",
      "img:twilight_wide", chapter="Where the light runs out", depth=500),
    S("Switch on a torch here and it lights a few metres of water. Beyond that, nothing.", "img:twilight_wide", "img:descend_twilight"),
    S("So the animals make their own light. In one seventeen-year survey off California, about three quarters of the animals filmed in open water could glow.",
      "clip:biolum_jellies", "img:biolum_fish", "img:biolum_jellies"),
    S("And most of that light is blue, because blue travels farthest through seawater.", "img:biolum_fish", "img:biolum_jellies"),
    S("And somewhere in this gloom lives the animal sailors called the kraken.", "img:kraken_shadow"),
    S("The giant squid. Eight arms, two long hunting tentacles, and it can reach around twelve metres.",
      "clip:giantsquid_wide", label="GIANT SQUID"),
    S("Put it next to you, and it's about as long as a city bus.", "scale:giantsquid"),
    S("Its eyes are the biggest of any animal: up to about twenty-five centimetres across. Dinner plates, in the dark.",
      "img:giantsquid_eye", "img:giantsquid_eye"),
    S("For centuries, nobody had filmed one alive in the deep. Then in 2012, a Japanese team finally did, hundreds of metres down.",
      "img:giantsquid_filmed", "img:kraken_shadow", "img:giantsquid_wide"),
    S("So why does a squid need eyes that big? Scientists think they help it spot one particular hunter from about a hundred and twenty metres away.",
      "img:giantsquid_eye", "img:sperm_whale_shadow", "img:kraken_shadow"),
    S("Because even the kraken has something it should fear.", "img:sperm_whale_shadow"),

    # ── 1,000 m ──────────────────────────────────────────────────────────────
    S("Past a thousand metres, there's no sunlight at all. Ever. This is the midnight zone.",
      "img:midnight_black", "img:deep_cold", chapter="The war in the dark", depth=1000),
    S("Turn off your light down here, and you couldn't see your own hand in front of your face.", "img:midnight_black"),
    S("And diving through it, on a single breath, comes the biggest predator with teeth on Earth.",
      "img:spermwhale_dive", "img:spermwhale_deep", label="SPERM WHALE"),
    S("A big male sperm whale can reach about sixteen metres. Its head alone is about a third of its body.",
      "scale:spermwhale"),
    S("They hunt more than a kilometre down, often much deeper, in complete darkness.",
      "img:spermwhale_deep", "img:midnight_black"),
    S("And we know they fight giant squid, because so many sperm whales carry round scars from squid suckers.",
      "img:spermwhale_scars", "img:spermwhale_vs_squid"),
    S("No one has ever actually watched one of those fights. It happens where no camera has been waiting.",
      "img:spermwhale_vs_squid", "img:spermwhale_deep"),
    S("But the deepest diving mammal isn't the sperm whale. It's this: Cuvier's beaked whale.",
      "img:beaked_whale", "img:beaked_whale_deep", label="CUVIER'S BEAKED WHALE"),
    S("One was tracked to almost three kilometres down. Another stayed under for three hours and forty-two minutes, on one breath.",
      "img:beaked_whale_deep", "img:beaked_whale_deep", depth=2992),
    S("Try holding yours.", "img:diver_dark_blue"),

    # ── Greenland shark ──────────────────────────────────────────────────────
    S("Now meet something slower. And much, much older.",
      "img:greenland_ice", chapter="The shark older than a country", depth=1200),
    S("The Greenland shark drifts through icy water more than a kilometre deep, in no hurry at all.",
      "clip:greenland_shark", "img:greenland_ice", label="GREENLAND SHARK"),
    S("So how do you work out a shark's age? It has no hard bones with growth rings to count.",
      "img:greenland_shark_close", "img:greenland_shark"),
    S("In 2016, scientists used a trace of radiocarbon from 1950s nuclear tests, locked inside the lenses of the sharks' eyes.",
      "img:greenland_shark_close", "img:greenland_ice"),
    S("They dated twenty-eight sharks. These animals live at least two hundred and seventy years.",
      "img:greenland_shark", "img:greenland_shark_close"),
    S("The oldest was probably around four hundred. It could have been born when ships like this still sailed the Arctic.",
      "img:old_ship", "img:greenland_shark_close"),
    S("Before the United States existed, that shark may already have been swimming.", "img:old_ship", "img:greenland_ice"),
    S("They're only ready to have young at around one hundred and fifty years old.", "img:greenland_shark"),
    S("And some grow past five metres. Here it is, next to you.", "scale:greenland"),

    # ── 2,000 m ──────────────────────────────────────────────────────────────
    S("Deeper down, food gets scarce. And many of the scariest hunters turn out to be tiny.",
      "img:deep_food", chapter="The monster that fits in your hand", depth=2000),
    S("This is a deep-sea anglerfish. It dangles a glowing lure in front of a mouth full of needle teeth.",
      "clip:anglerfish_lure", "img:anglerfish_face", label="DEEP-SEA ANGLERFISH"),
    S("It looks like a nightmare. But many anglerfish are smaller than your phone.", "scale:anglerfish"),
    S("And the males are even stranger. In some species, a tiny male bites onto a female and never lets go.",
      "img:anglerfish_pair", "img:anglerfish_face"),
    S("His body fuses with hers, and her blood keeps him alive for the rest of his life.", "img:anglerfish_pair", "img:anglerfish_face"),
    S("Some females end up carrying several males at once.", "img:anglerfish_pair"),
    S("One male measured just six millimetres. About the size of a grain of rice.", "img:anglerfish_face"),

    # ── 3,800 m ──────────────────────────────────────────────────────────────
    S("At about three thousand eight hundred metres lies the wreck of the Titanic.",
      "img:titanic_bow", chapter="The weight on your fingernail", depth=3800),
    S("Every ten metres of water adds about one more atmosphere of pressure. Down here, that's around three hundred and eighty.",
      "img:titanic_dark", "img:titanic_bow"),
    S("So what does that feel like? Nearly four hundred kilograms pressing on every fingernail-sized patch of you. A grand piano, on your fingernail.",
      "img:deep_cold", "img:titanic_dark"),
    S("The water is just a few degrees above freezing, and it is completely black.", "img:deep_cold", "img:titanic_bow"),
    S("And we still aren't even halfway to the bottom.", "img:trench_edge"),

    # ── 4,000-7,000 m ────────────────────────────────────────────────────────
    S("Below four thousand metres begins the abyss: huge, flat plains of mud, in a darkness that never ends.",
      "img:abyssal_plain", chapter="The deepest octopus", depth=4000),
    S("Then, past six thousand metres, the sea floor splits open into trenches. The hadal zone.",
      "img:trench_edge", "img:lander_camera", depth=6000),
    S("In 2019, a camera dropped into the Java Trench filmed an octopus at almost seven thousand metres.",
      "img:lander_camera", "img:trench_edge", depth=6957),
    S("A dumbo octopus, flapping two ear-like fins. The deepest octopus ever seen.",
      "clip:dumbo_octopus", label="DUMBO OCTOPUS"),
    S("Before that, the deepest one anyone had seen was at about five thousand one hundred metres, back in 1971.",
      "img:dumbo_octopus", "img:abyssal_plain"),
    S("It's less than half a metre long, living under almost seven hundred atmospheres.", "scale:dumbo"),
    S("But it's not the deepest animal we've found. Not even close.", "img:trench_edge", "img:lander_camera"),

    # ── 8,336 m ──────────────────────────────────────────────────────────────
    S("Then, at eight thousand three hundred and thirty-six metres, the deepest fish ever filmed.",
      "clip:snailfish", chapter="The last fish", depth=8336, label="HADAL SNAILFISH"),
    S("That's like twenty-five Eiffel Towers of water stacked on top of you.", "img:trench_edge", "img:deep_cold"),
    S("A small, pale snailfish, caught on camera in a trench off Japan in 2022. It beat the old record by about a hundred and sixty metres.",
      "img:snailfish_group", "img:snailfish", "img:snailfish_group"),
    S("So how does a fish survive down here? Snailfish have no swim bladder, the gas-filled bag most fish use to float. No air space to crush.",
      "img:snailfish", "img:snailfish_group"),
    S("And scientists think fish simply can't live much deeper than this.", "img:trench_edge"),

    # ── 10,935 m ─────────────────────────────────────────────────────────────
    S("About two and a half kilometres further down is the deepest point on Earth: the Challenger Deep.",
      "img:challenger_deep", chapter="The bottom of the world", depth=10935),
    S("Drop Mount Everest in here, and its peak would still be more than two kilometres underwater.",
      "img:everest_trench", "img:challenger_deep"),
    S("The pressure is over a thousand times what you feel right now. Like a small car balanced on your fingernail.",
      "img:challenger_deep", "img:deep_cold"),
    S("In January 1960, two men rode a vessel called the Trieste all the way down.", "clip:trieste_descent"),
    S("Sinking to the bottom took them almost five hours.", "img:trieste_descent", "img:deep_cold"),
    S("But on the way, there was a loud crack. One of the outer windows had split.", "img:trieste_window", "img:deep_cold"),
    S("Jacques Piccard and Don Walsh kept going anyway, and touched the bottom.", "img:trieste_bottom"),
    S("They stayed only about twenty minutes, then began the long climb back to the light.",
      "img:trieste_bottom", "img:ascent_light"),
    S("So what is waiting at the very bottom of the world?", "img:challenger_deep"),

    # ── payoff ───────────────────────────────────────────────────────────────
    S("Tiny scavengers called amphipods, picking through the mud.",
      "img:amphipods", chapter="What was waiting at the bottom", depth=10935),
    S("And something else, first seen in 1998, and reported by Japanese scientists twenty years later.",
      "img:challenger_deep"),
    S("At ten thousand eight hundred and ninety-eight metres, on the floor of the Mariana Trench: a plastic bag.",
      "img:challenger_deep", "clip:plastic_bag", sfx="boom"),
    S("Single-use plastic that could stay down there for hundreds, maybe thousands of years.", "img:plastic_bag_close"),
    S("So here's the strange truth of the deep. The monsters get smaller the deeper you go.",
      "img:montage_whale", "img:snailfish_group"),
    S("Thirty-metre whales near the top. A pale little fish near the bottom. And at the very bottom, what was waiting for us was us.",
      "img:bluewhale_wide", "img:plastic_bag_close"),
    S("Which layer would you turn back at? Tell me the depth in the comments.", "img:ascent_light"),
    # ── end card (owner, Nov 4): subscribe + bell + share, animated on screen ──
    S("If this dive gave you chills, subscribe to FramedFacts and tap the bell. Next time, we put the biggest "
      "predators that ever lived right next to you.", "img:surface_pov", "img:bg_sunlit", cta="subscribe", depth=0),
    S("And share this with the one friend who still thinks the ocean is safe.", "img:surface_below", cta="share"),
]

# ── stills: our own prompts (anatomy written out so the AI gets the animal right) ──
PROMPTS = {
    "surface_pov": "View from just below the surface of the deep open ocean, looking up at the silhouette of a lone swimmer floating at the surface, sun rays, endless deep blue below",
    "surface_below": "Looking straight down from the surface into the bottomless deep blue open ocean, light rays fading into black",
    "montage_whale": "A blue whale gliding far beneath a tiny swimmer silhouette at the surface, enormous size difference, deep blue water",
    "montage_angler": "A deep-sea anglerfish with a glowing bioluminescent lure in total darkness, needle-like teeth, black background",
    "trench_dark": "Looking down into the black depths of a deep ocean trench, faint rock walls, drifting marine snow, ominous"
                   ", completely empty water: no animals, no fish, no creatures, no ice, no water surface visible",
    "ascent_light": "Looking up from the deep sea toward faint blue light far above, marine snow drifting",
    "diver_descend_blue": "A scuba diver slowly descending head-first into deep blue open water, bubbles rising, sunlight fading above",
    "bluewhale_wide": "A blue whale swimming near the sunlit surface of the open ocean, long slender mottled blue-grey body, tiny dorsal fin far back near the tail, broad flat U-shaped head, sun rays",
    "bluewhale_close": "Close view of a blue whale (not a humpback) near the surface: very long streamlined mottled blue-grey body, broad flat U-shaped head with a single ridge and two blowholes, small slim pectoral fins, smooth skin without knobs, sunlight dappling",
    "bluewhale_court": "Aerial drone photo of a blue whale at the ocean surface beside a small research boat for scale, deep blue water",
    "krill_swarm": "A dense swarm of Antarctic krill, small pinkish translucent shrimp-like crustaceans, in blue water, macro",
    "bluewhale_feeding": "A blue whale (not a humpback) lunge-feeding at the surface: very long streamlined mottled blue-grey body, small slim pectoral fins, broad flat head, mouth wide open and throat pleats ballooned around a pink cloud of krill",
    "box_jelly_dark": "A nearly invisible transparent box jellyfish drifting in shallow tropical water, faint glassy outline, sunbeams",
    "box_jelly_close": "Australian box jellyfish, Chironex fleckeri, transparent cube-shaped bell with bunches of long trailing tentacles from its four corners, dark blue water",
    "box_jelly_tentacles": "Long translucent box jellyfish tentacles trailing through blue water, close-up, delicate and dangerous",
    "diver_10m": "A scuba diver at about 10 metres depth beside a coral reef wall, blue water, bubbles",
    "diver_lungs": "Close-up of a scuba diver's chest, wetsuit and regulator releasing bubbles, deep blue water",
    "diver_dark_blue": "A lone scuba diver hanging motionless in dark blue open water, light fading above, sense of depth",
    "diver_narcosis": "Dreamy soft-focus view of a scuba diver drifting in deep blue water, slightly hazy, disorienting mood",
    "diver_dizzy": "A scuba diver looking up at the distant shimmering surface far above, deep water, slight motion blur",
    "diver_40m": "A scuba diver checking a wrist dive computer in deep dim blue water, the screen not readable",
    "scuba_record": "A technical diver with several tanks descending along a guide line into the dark deep blue Red Sea, dim light",
    "diver_decompression": "A technical diver waiting on a decompression stop beside a line in shallow sunlit blue water, calm",
    "descend_twilight": "Looking down along a rope line into the dark blue twilight depths of the ocean",
    "twilight_wide": "The ocean twilight zone, deep dim blue water with faint light from far above, small silver fish",
    "biolum_jellies": "Bioluminescent deep-sea jellyfish glowing blue in the dark twilight zone",
    "biolum_fish": "Lanternfish with rows of glowing blue light organs on its body, in the dark deep sea",
    "kraken_shadow": "The dark shadowy shape of a giant squid emerging from deep blue gloom, mysterious, only partly visible",
    "giantsquid_wide": "Giant squid Architeuthis in the deep sea, long reddish-brown torpedo-shaped body with two small fins at the tip, eight thick arms and two much longer thin feeding tentacles with club ends, one huge eye, dark blue water",
    "giantsquid_eye": "Extreme close-up of a giant squid's enormous dark eye, reddish skin around it, faint light reflection, deep sea",
    "giantsquid_filmed": "A deep-sea camera rig with a small light hanging in dark water while a giant squid approaches out of the darkness",
    "sperm_whale_shadow": "The huge silhouette of a sperm whale passing above in dark blue water, seen from below",
    "midnight_black": "Pitch-black midnight zone of the deep ocean, a few tiny bioluminescent sparks in the darkness",
    "spermwhale_dive": "A sperm whale swimming down into the dark depths, seen from the side: huge blunt box-shaped head making up a third of its body, the narrow lower jaw closed and tucked under the head, wrinkled dark grey skin, small paddle flippers",
    "spermwhale_deep": "A sperm whale in near-total darkness deep below the surface, faint light on its massive blunt head",
    "spermwhale_scars": "Close-up of a sperm whale's wrinkled dark grey skin marked with many circular scars from squid suckers",
    "spermwhale_vs_squid": "A sperm whale and a giant squid locked together in the dark deep sea, the squid's arms wrapped around the whale's huge blunt head",
    "beaked_whale": "Cuvier's beaked whale swimming in deep blue water, short goose-like beak, pale head, long scarred grey-brown body, small dorsal fin set far back",
    "beaked_whale_deep": "Cuvier's beaked whale descending into the dark deep sea, faint light from above",
    "greenland_ice": "A Greenland shark swimming under Arctic sea ice in dark cold water",
    "greenland_shark": "Greenland shark swimming slowly in cold dark water, thick heavy grey-brown body, small dorsal fins, small pale eyes, ancient look",
    "greenland_shark_close": "Close-up of a Greenland shark's head with a small pale eye, cold dark water, particles drifting",
    "old_ship": "A 17th-century wooden sailing ship on a cold grey Arctic sea with floating ice, overcast sky",
    "deep_food": "Marine snow drifting down through the dark deep sea, tiny particles in a beam of light",
    "anglerfish_lure": "Female humpback anglerfish Melanocetus in total darkness, dark round body, a glowing lure on a stalk growing from its head, wide mouth of long needle-like teeth",
    "anglerfish_face": "Close-up of a deep-sea anglerfish face with long needle teeth and a softly glowing lure, black background",
    "anglerfish_pair": "Deep-sea anglerfish female with a tiny parasitic male fused to her belly, black background",
    "titanic_bow": "The bow of the Titanic wreck on the dark sea floor, covered in rust and rusticles, lit by a submersible's lights",
    "titanic_dark": "A dark deep sea floor with a large shipwreck faintly visible in a beam of light",
    "deep_cold": "Pitch-black deep sea water far from any light, slow white marine snow particles drifting, cold blue-black"
                 ", completely empty water: no animals, no fish, no creatures, no ice, no water surface visible",
    "bg_sunlit": "Open blue ocean just below the surface, sun rays slanting down through clear water, tiny particles"
                 ", completely empty water: no animals, no fish, no creatures, no ice, no water surface visible",
    "abyssal_plain": "The abyssal plain, a vast flat muddy sea floor in total darkness lit by a single beam, a sea cucumber on the mud",
    "trench_edge": "The edge of a deep ocean trench dropping into blackness, steep rock walls, deep sea, completely empty: no animals, no fish, no eels, no sharks, no octopus, no creatures, no tracks",
    "lander_camera": "A deep-sea lander with a camera, lights and bait resting on the dark trench floor",
    "dumbo_octopus": "Dumbo octopus Grimpoteuthis, small pale pink-white octopus with two ear-like fins on top of its head and webbed arms, hovering above the dark sea floor",
    "snailfish": "Hadal snailfish Pseudoliparis, small pale pinkish translucent tadpole-shaped fish with a large head and no scales, swimming near the dark trench floor in a camera light",
    "snailfish_group": "Several pale translucent hadal snailfish gathering around bait on the dark trench floor in a camera light",
    "challenger_deep": "The bottom of the Challenger Deep, smooth undisturbed pale grey sediment sea floor in total darkness lit by a "
                       "submersible's lights, marine snow drifting, completely empty: no animals, no fish, no eels, no sharks, no octopus, no creatures, no tracks",
    "everest_trench": "Mount Everest's snowy peak submerged deep inside a vast dark ocean trench, deep water far above its summit, photoreal",
    "trieste_descent": "the 1960 bathyscaphe Trieste: a long rounded grey float shaped like a blimp, with a short open railing tower on top, and a small dark steel sphere for the two-man crew hanging underneath; not a submarine, no periscope, no numbers or text, descending slowly into the dark ocean, faint light from above",
    "trieste_window": "View from inside a cramped 1960s deep-sea vessel through a small thick round viewport, only empty black water and a few particles outside, a thin crack across the outer pane, no animals",
    "trieste_bottom": "the 1960 bathyscaphe Trieste: a long rounded grey float shaped like a blimp, with a short open railing tower on top, and a small dark steel sphere for the two-man crew hanging underneath; not a submarine, no periscope, no numbers or text, hovering just above a grey silty sea floor in total darkness, its floodlights on",
    "amphipods": "A swarm of small pale amphipods, shrimp-like crustaceans, scavenging on a deep trench floor, macro, camera light",
    "plastic_bag": "A single white plastic bag lying on the grey silty floor of the deepest ocean trench, lit by a submersible light, total darkness around",
    "plastic_bag_tease": "A torn white plastic bag half-hidden in darkness at the very edge of a narrow submersible beam on a grey trench floor, only a pale corner visible, no animals, mysterious",
    "plastic_bag_close": "Close-up of a plain torn white plastic bag with no printing, half buried in grey deep-sea sediment in a beam of light, eerie",
}

# Cut-outs for the scale cards (isolated on black, side profile)
CUTOUTS = {
    "cut_bluewhale": "A blue whale, long slender mottled blue-grey body, tiny dorsal fin far back, broad flat U-shaped head",
    "cut_giantsquid": "A giant squid Architeuthis, reddish torpedo body with small tail fins, eight arms and two much longer feeding tentacles stretched out",
    "cut_spermwhale": "A sperm whale, huge blunt box-shaped head about a third of its body, mouth closed with the narrow lower jaw tucked under the head and no teeth visible, wrinkled dark grey skin, small paddle flippers",
    "cut_greenland": "A Greenland shark, thick heavy grey-brown body, small dorsal fins, small eyes",
    "cut_anglerfish": "A female deep-sea humpback anglerfish, dark round body, glowing lure on a stalk from its head, needle teeth",
    "cut_dumbo": "A dumbo octopus, pale pink-white, two ear-like fins on its head, webbed arms spread",
}
PROMPTS.update(CUTOUTS)

SCALES = {
    "bluewhale": dict(cut="cut_bluewhale", name="Blue whale", length_m=30, size_text="up to ~30 m", note="ABOUT 17 OF YOU, HEAD TO TOE",
                      bg="bg_sunlit"),                        # the scale cards play over moving, empty water
    "giantsquid": dict(cut="cut_giantsquid", name="Giant squid", length_m=12, size_text="~12 m", note="AS LONG AS A CITY BUS"),
    "spermwhale": dict(cut="cut_spermwhale", name="Sperm whale", length_m=16, size_text="~16 m", note="THE BIGGEST PREDATOR WITH TEETH"),
    "greenland": dict(cut="cut_greenland", name="Greenland shark", length_m=5, size_text="5 m+", note="AND MAYBE 400 YEARS OLD"),
    "anglerfish": dict(cut="cut_anglerfish", name="Anglerfish", length_m=0.1, size_text="often ~10 cm", ref="phone", note="SMALLER THAN YOUR PHONE"),
    "dumbo": dict(cut="cut_dumbo", name="Dumbo octopus", length_m=0.4, size_text="< 0.5 m", note="UNDER ~700 ATMOSPHERES"),
}

# Veo image-to-video: animate these stills (motion prompts)
CLIPS = {
    "diver_descend_blue": "The diver sinks slowly deeper, bubbles rise past the camera, light fades above",
    "bluewhale_wide": "The blue whale glides slowly forward beneath the surface, tail beating gently, light rays shimmer",
    "box_jelly_close": "The box jellyfish pulses gently and drifts, tentacles trailing and swaying",
    "biolum_jellies": "The jellyfish pulse slowly and their blue glow flickers in the dark",
    "giantsquid_wide": "The giant squid drifts forward out of the gloom, arms and tentacles moving slowly",
    "spermwhale_dive": "The sperm whale dives slowly downward into darkness, flukes moving",
    "beaked_whale": "The beaked whale swims forward and begins to angle downward into the depths",
    "greenland_shark": "The Greenland shark swims very slowly past the camera, tail sweeping lazily",
    "anglerfish_lure": "The anglerfish hangs almost still, its glowing lure sways and pulses in the dark",
    "dumbo_octopus": "The dumbo octopus flaps its ear-like fins and hovers gently above the sea floor",
    "snailfish": "The small snailfish wriggles slowly through the camera light near the sea floor",
    "trieste_descent": "The bathyscaphe sinks slowly downward into deeper darkness, small particles drift past",
    "plastic_bag": "The camera light slowly reveals the plastic bag on the sea floor, sediment drifting",
}

# Motion for every still (Veo 3.1 Lite, 8 s, image-to-video): no zoom-only images (owner, 2026-11-04)
MOTION = {
    'surface_pov': 'The swimmer floats and slowly kicks at the surface, sunlight ripples, the camera drifts downward away from the surface',
    'surface_below': 'The camera slowly descends looking down into the blue, light rays sway, a few fish drift past',
    'montage_whale': 'The whale glides slowly forward far below the swimmer, its tail beating gently, light rays shimmer',
    'montage_angler': 'The anglerfish hangs in the dark, its glowing lure pulses and sways, its jaw opens slightly',
    'trench_dark': 'The camera sinks slowly into the empty dark trench, particles drift upward past the lens; no animals appear',
    'ascent_light': 'Particles drift slowly upward toward the faint light far above, the camera tilts up',
    'plastic_bag_tease': 'The narrow beam sweeps slowly across the dark floor, sediment drifts, the pale corner of the bag stays at the edge of the light, nothing moves',
    'bluewhale_wide': 'The blue whale glides slowly forward beneath the surface, tail beating gently, light rays shimmer on its back',
    'bluewhale_close': "The blue whale's huge head glides past the camera, sunlight dapples its skin, the camera tracks alongside",
    'bluewhale_court': 'Aerial drone shot slowly orbiting the blue whale at the surface as it exhales a tall blow beside the small boat',
    'krill_swarm': 'The krill swarm swirls and flickers, thousands of tiny bodies darting in the blue, the camera pushes through them',
    'bluewhale_feeding': 'The blue whale surges forward with its mouth open, throat pleats expanding as it engulfs the krill cloud',
    'box_jelly_dark': 'The almost invisible box jellyfish pulses gently and drifts over the reef, light rays shift',
    'box_jelly_tentacles': 'Long transparent tentacles trail and sway slowly through the water, the camera follows them',
    'diver_10m': 'The diver finns slowly along the reef wall, bubbles rising, small fish dart away',
    'diver_lungs': 'Close-up: the diver breathes out, a stream of bubbles rushes up from the regulator, the chest rises and falls',
    'diver_dark_blue': 'The lone diver hangs in the dark blue, slowly turning, bubbles rising, the light above dims',
    'diver_narcosis': 'Dreamy slow motion: the diver drifts and turns lazily, the image gently wavers and blurs at the edges',
    'diver_dizzy': 'The diver looks up at the distant surface and slowly drifts backward, bubbles spiral upward',
    'diver_40m': 'The diver checks the wrist computer, then looks down into the dark, bubbles rising',
    'scuba_record': 'The technical diver descends steadily along the guide line into the dark, torch beam swinging',
    'diver_decompression': 'The diver waits beside the line, breathing slowly, bubbles rising, sunlight flickering from above',
    'descend_twilight': 'The camera slides slowly down along the rope into the darkening blue, particles drifting past',
    'twilight_wide': 'A school of small silver fish turns and flashes in the dim blue, the camera drifts deeper',
    'biolum_fish': 'The lanternfish swims slowly past, its rows of blue lights blinking, the camera tracks with it',
    'kraken_shadow': "The giant squid's shadowy shape slowly emerges from the gloom toward the camera, arms trailing",
    'giantsquid_filmed': "The giant squid approaches the camera rig, its arms reaching toward the light, the rig's lamp flickers",
    'midnight_black': 'Tiny blue sparks of bioluminescence flicker and drift in the total darkness',
    'spermwhale_dive': 'The sperm whale swims slowly downward into the darkness, its flukes beating, the camera follows',
    'spermwhale_deep': 'The sperm whale glides slowly through near-darkness, its massive head catching faint light',
    'spermwhale_scars': "The camera slides slowly along the sperm whale's scarred skin as the whale moves",
    'spermwhale_vs_squid': "The sperm whale twists slowly as the giant squid's arms tighten and writhe around its head, sediment swirls",
    'beaked_whale': 'The beaked whale swims forward and begins to angle downward into the depths',
    'beaked_whale_deep': 'The beaked whale descends steadily into the dark, the faint light above fading',
    'greenland_ice': 'The Greenland shark glides slowly under the ice, its tail sweeping lazily, light filters through the ice',
    'greenland_shark_close': "The Greenland shark's head moves slowly past the camera, its small eye passing close",
    'old_ship': 'The old sailing ship rolls slowly on the cold grey sea, sails flapping, ice drifting past',
    'deep_food': 'Marine snow drifts slowly down through the beam of light',
    'anglerfish_face': 'The anglerfish slowly opens its needle-toothed jaws, the lure glowing and swaying',
    'anglerfish_pair': 'The anglerfish drifts slowly in the dark, fins fluttering, the lure pulsing',
    'titanic_bow': "The submersible's lights sweep slowly across the rusted bow of the wreck, particles drifting in the beams",
    'titanic_dark': 'A beam of light slowly reveals the wreck in the darkness, small fish drift past',
    'deep_cold': 'Marine snow drifts slowly through the empty black water as the camera sinks; no animals appear',
    'bg_sunlit': 'Sun rays shimmer and sway through the empty blue water, particles drift slowly; no animals appear',
    'abyssal_plain': 'The light beam glides slowly across the flat muddy plain, the sea cucumber inches forward',
    'trench_edge': 'The camera drops slowly over the edge of the empty trench into blackness; no animals appear',
    'lander_camera': 'The deep-sea rig rests on the trench floor, its lights flicker on, sediment puffs up, a small creature moves',
    'snailfish_group': 'The pale snailfish wriggle slowly around the bait in the camera light',
    'challenger_deep': "The camera glides steadily forward, low over the empty silty floor of the deepest point, its lights sweeping "
                       "from left to right, marine snow streaming past the lens, sediment puffing up; no animals appear",
    'everest_trench': 'The camera rises slowly up the sunken mountain toward its peak, deep water far above, particles drifting',
    'trieste_window': 'Through the round window, particles drift past in the black water, the crack catches the light',
    'trieste_bottom': 'The bathyscaphe hovers just above the floor, its floodlights stirring a slow cloud of silt',
    'amphipods': 'The pale amphipods scurry and swarm over the mud in the camera light',
    'plastic_bag_close': 'The plastic bag stirs slightly in the faint current, silt drifting across it in the beam',
}

SOURCES = (
    "Sources:\n"
    "- Blue whale size: Guinness World Records (largest animal); Pacific Community (SPC) ocean science fact\n"
    "- Blue whale heart rate of two beats a minute: Goldbogen et al. (2019), PNAS; Stanford News\n"
    "- Box jellyfish: Life in the Fast Lane (Chironex fleckeri); Medical Journal of Australia (2005) Northern Territory sting study\n"
    "- Pressure and the body: University of Western Australia, 'Problems with pressure'; McGill Office for Science and Society\n"
    "- Nitrogen narcosis and the 40 m recreational limit: Wikipedia (Nitrogen narcosis); The Diving Blog\n"
    "- Deepest scuba dive (Ahmed Gabr, 332.35 m, 2014): Guinness World Records; Live Science\n"
    "- Bioluminescence (76% of animals in the water column; mostly blue light): Martini & Haddock (2017), Scientific Reports; MBARI\n"
    "- Giant squid eyes, first deep-sea footage (2012), spotting sperm whales ~120 m away: Smithsonian Ocean; NPR; Live Science; Nilsson et al. (2012), Current Biology\n"
    "- Sperm whales and squid sucker scars: American Museum of Natural History; A-Z Animals\n"
    "- Cuvier's beaked whale dive records: Guinness World Records; Science News (Journal of Experimental Biology, 2020)\n"
    "- Greenland shark age: Nielsen et al. (2016), Science; ScienceDaily\n"
    "- Anglerfish sexual parasitism and the 6.2 mm male: Natural History Museum; University of Washington\n"
    "- Dumbo octopus at 6,957 m (Java Trench; previous record 5,145 m in 1971): Jamieson & Vecchione (2020), Marine Biology; Guinness World Records; Live Science\n"
    "- Deepest fish filmed (snailfish, 8,336 m, 2022; previous 8,178 m): Smithsonian Magazine; ITV News\n"
    "- Challenger Deep depth and pressure, Everest comparison: EarthDate; WorldAtlas\n"
    "- Trieste dive, January 1960: U.S. Naval History and Heritage Command (H-Gram 041); USNI Proceedings\n"
    "- Plastic bag at 10,898 m: Chiba et al. (2018), Marine Policy (JAMSTEC Deep-sea Debris Database); Euronews; ScienceAlert"
)

SCRIPT = {
    "format": "long",
    "hook": " ".join(s["line"] for s in SEGMENTS[:5]),
    "body": " ".join(s["line"] for s in SEGMENTS[5:-2]),
    "cta": "Which layer would you turn back at? Tell me the depth in the comments!",
    "title": "The Biggest Monster in Every Ocean Layer, Shown Next to You",
    "category_id": "27",          # Education: what most hit videos on this topic use (Nov 4 research)
    "tags": ["deep sea creatures", "ocean layers", "mariana trench", "deep sea", "deep ocean", "ocean zones",
             "ocean depth comparison", "sea creatures", "sea monsters", "giant sea creatures", "thalassophobia",
             "challenger deep", "giant squid", "sperm whale", "greenland shark", "anglerfish", "dumbo octopus",
             "blue whale", "kraken", "size comparison", "animals to scale", "ocean documentary",
             "deep sea documentary", "trieste bathyscaphe", "plastic in the mariana trench"],
    "ai_generated_visuals": True,
    "topic_category": "Animals",
    "thumbnail_path": THUMB,
}

# Clip QA (2026-11-04): the whale clips drift into humpback-like knobbly flippers later in the clip,
# so the blue, sperm and beaked whale clips are not used (checked stills instead).
rv.CLIP_TRIM.update({"greenland_shark": 4.2, "dumbo_octopus": 4.0, "sperm_whale_shadow": 4.0,
                     # motion-clip QA (Nov 4): whales drift into humpback flippers after ~2 s
                     "montage_whale": 2.0, "bluewhale_wide": 2.0, "bluewhale_close": 2.0, "bluewhale_court": 2.0,
                     "bluewhale_feeding": 1.8, "spermwhale_dive": 1.8, "spermwhale_deep": 1.8, "spermwhale_scars": 1.8,
                     "beaked_whale": 1.8, "beaked_whale_deep": 2.0,
                     # other drift: squid turns octopus-like, shark changes species, a fish appears at 10,935 m,
                     # tropical fish in the deep, clips that fade to black
                     "kraken_shadow": 4.0, "greenland_shark_close": 5.0,
                     "ascent_light": 2.5, "trench_edge": 2.8,
                     "trench_dark": 3.2, "trieste_descent": 2.7})                     # fades to black after ~3.5 s
CLIPS.pop("bluewhale_wide", None)     # the flipper drifts into a humpback's even in the first seconds
CLIPS.pop("spermwhale_dive", None)
CLIPS.pop("beaked_whale", None)

render_shot = None
frame = rv.frame_fn(SEGMENTS, VIDEO_ID, SCALES)
sound_events = rv.section_sounds(SEGMENTS)


def make_thumbnail(path=THUMB):
    """Realistic huge-creature background + code-drawn arrow and 2-3 words (thumb_kit)."""
    import thumb_kit as tk
    from PIL import Image
    bg = Image.open(os.path.join(rv.asset_dir(VIDEO_ID), "thumb_bg.png")).convert("RGBA").resize((1920, 1080), Image.LANCZOS)
    c = bg.copy()
    tk.headline(c, [("THIS IS", 110, tk.WHITE), ("YOU", 230, tk.YELLOW)], 470, 250, rotate=-3)
    lay, d = tk.layer()
    tk.arrow(d, (520, 420), (470, 560), (THUMB_DIVER[0], THUMB_DIVER[1] - 40))
    tk.stick(c, lay, outline=10, shadow=(8, 10))
    return tk.save(c, path)


THUMB_DIVER = (330, 795)     # where the tiny diver sits in thumb_bg (checked on the contact sheet)
THUMB_PROMPT = ("A gigantic sperm whale's blunt head and small eye looming out of pitch-black deep water on the right two thirds "
                "of the frame, a tiny scuba diver with a torch on the lower left for scale, dramatic beam of light, dark cinematic")


def chapters_text(starts):
    """YouTube chapters with the depth in front, e.g. '3:30 1,000 m: The war in the dark'."""
    rows = []
    for seg, st in zip(SEGMENTS, starts):
        if seg.get("chapter"):
            sec = 0 if not rows else int(st)
            name = seg["chapter"] if not rows else f"{seg['depth']:,} m: {seg['chapter']}"
            rows.append(f"{sec // 60}:{sec % 60:02d} {name}")
    return "\n".join(rows)


def description(starts):
    return (
        "Every layer of the ocean has its own monster. We sink from the surface to the bottom of the Mariana Trench "
        "and put each deep sea creature right next to you, to scale.\n\n"
        "Meet the blue whale, the giant squid (the real kraken), the sperm whale, a Greenland shark that may be 400 "
        "years old, the deep-sea anglerfish, the deepest octopus and the deepest fish ever filmed, then ride the 1960 "
        "Trieste dive to the Challenger Deep, 10,935 metres down, and see what was really waiting at the bottom. "
        "Every ocean zone, from the sunlight zone to the hadal zone, with real depths and pressures on screen. "
        "(Fair warning if you have thalassophobia.)\n\n"
        + chapters_text(starts) + "\n\n"
        "About the visuals: the animal scenes are AI-generated reconstructions (Google Gemini and Veo), checked against "
        "scientific descriptions of each species. Every number, depth and scale comparison on screen is drawn from the "
        "measurements in the sources below.\n\n"
        + SOURCES + "\n\n"
        "Next in the series: the biggest predators that ever lived, shown next to you.\n\n"
        "#deepsea #ocean #thalassophobia")


def publish(log_path, public_now=False):
    """Upload after the owner approves (never automatically). Reads segment starts from the build log."""
    import ast
    import re
    import config as cfg
    import phase5_upload as p5
    import pro_shorts_creator as psc
    starts = ast.literal_eval(re.search(r"segment starts: (\[[^\]]*\])", open(log_path).read()).group(1))
    out = os.path.join(cfg.VIDEOS_DIR, f"{VIDEO_ID}.mp4")
    vo = os.path.join(cfg.AUDIO_DIR, f"{VIDEO_ID}_vo.wav")
    script = dict(SCRIPT, video_title=SCRIPT["title"], seo_description=description(starts))
    cfg.UPLOAD_PRIVACY = "public" if public_now else "private"
    url, is_public = p5.upload_to_youtube(out, script, {"title": SCRIPT["title"], "subject": SCRIPT["hook"], "category": "Animals"})
    vid = url.rsplit("=", 1)[-1]
    p5.upload_thumbnail(vid, THUMB)
    srt = os.path.splitext(vo)[0] + ".srt"
    psc.generate_srt(psc.get_word_timestamps(vo), srt)
    p5.upload_captions(vid, srt)
    add_to_series(p5.get_youtube_client(), vid)
    if public_now:                      # YouTube refuses comments on a video that isn't public yet
        p5.post_engagement_comment(vid, PINNED_COMMENT)
    return vid


SERIES = "Shown Next to You"
SERIES_DESC = ("Extreme animals put right next to a human, to scale: deep sea monsters, giant predators and "
               "prehistoric giants, with real sizes, depths and sources.")
PINNED_COMMENT = ("Which one would you least want to meet in the dark: the giant squid, the 400-year-old Greenland "
                  "shark, or the anglerfish? And where do we go next: prehistoric predators, or the biggest animals "
                  "that ever walked on land?")


def add_to_series(yt, vid):
    """Put the video in the series playlist (created once, public), so a viewer who finishes one gets the next."""
    pl = next((p["id"] for p in yt.playlists().list(part="snippet", mine=True, maxResults=50).execute()["items"]
               if p["snippet"]["title"] == SERIES), None)
    if not pl:
        pl = yt.playlists().insert(part="snippet,status", body={
            "snippet": {"title": SERIES, "description": SERIES_DESC, "defaultLanguage": "en"},
            "status": {"privacyStatus": "public"}}).execute()["id"]
    yt.playlistItems().insert(part="snippet", body={"snippet": {
        "playlistId": pl, "resourceId": {"kind": "youtube#video", "videoId": vid}}}).execute()
    return pl


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    D = "/tmp/claude-0/-home-user-youtubeautomation/7fff9e34-920a-5cff-ba6a-cebf90c2f14e/scratchpad"
    if cmd == "check":
        import script_check
        res, total = script_check.check(SEGMENTS, SCRIPT, SOURCES)
        sys.exit(0 if script_check.report(res, total) else 1)
    if cmd == "assets":
        prompts = dict(PROMPTS, thumb_bg=THUMB_PROMPT)
        print(rv.gen_images(prompts, VIDEO_ID, cutouts=set(CUTOUTS)))
        rv.contact_sheet(VIDEO_ID, list(prompts), os.path.join(D, "deep_assets.jpg"))
    if cmd == "clips":
        print(rv.gen_clips(CLIPS, VIDEO_ID, seconds=6, model="veo-3.1-fast-generate-001"))
    if cmd == "motion":
        print(rv.gen_images({k: PROMPTS[k] for k in MOTION}, VIDEO_ID))     # any new stills first
        print(rv.gen_clips(MOTION, VIDEO_ID, seconds=8, model="veo-3.1-lite-generate-001"))
    if cmd == "preview":
        print(rv.preview(SEGMENTS, VIDEO_ID, SCALES, os.path.join(D, "deep_preview.jpg")), "tiles")
    if cmd == "build":
        make_thumbnail()
        for seg in SEGMENTS[:6]:
            seg["gap"] = HOOK_GAP
        out, _ = ms.render_short(SCRIPT, SEGMENTS, VIDEO_ID, frame, voice=VOICE, speed=VOICE_RATE, music_style="deep",
                                 sfx_fn=sound_events, music_vol=0.09, hook_hit=False, gap_s=LINE_GAP,
                                 chapter_pause_s=CHAPTER_PAUSE)
        import subprocess
        tmp = out.replace(".mp4", "_norm.mp4")       # YouTube-level loudness (about -15 LUFS)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", out, "-c:v", "copy", "-af", "loudnorm=I=-15:TP=-1.5:LRA=9",
                        "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", tmp], check=True)
        os.replace(tmp, out)
