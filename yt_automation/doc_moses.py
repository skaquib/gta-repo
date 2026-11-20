"""
doc_moses.py — documentary #2. "The Boy Who Was Playing Football When
They Came for His Family"

WHY THIS STORY, AND WHY THE OTHERS WERE WRONG (2026-09-11):
The brief was player-related real-life stories -- untold, shocking, hidden
talent, motivation, something an audience opens out of curiosity. Three
earlier drafts were checked against that and discarded:
  1. Portsmouth FC collapse   -> business analysis, no player at its centre.
  2. MS Dhoni ticket collector -> not untold. It has a 2016 Bollywood film.
  3. Valentino Dixon           -> extraordinary, but he is not a player.
     Sports-adjacent (golf as a motif), not a sports story about an athlete.
This one is a player, and it is the rarest combination: genuinely shocking,
genuinely motivating, and genuinely under-told.

AUDIENCE FIT (measured, 90 days): IN 64.4%, US 9.5%, PH 7.4%, ID 4.1%.
Chelsea and the Premier League carry real weight in India. Most viewers
know Moses as a wing-back in a blue shirt and have no idea about any of
this, which is exactly the curiosity gap the brief asked for.

VERIFIED (2026-09-11: Premier League official; Tribuna; Sporting Tribune;
This is Africa; Chronicle NG; Malay Mail):
- Victor Moses was born in Nigeria. His father Austin was a Christian
  pastor; his mother was Josephine.
- In 2002 both parents were killed in their home in Kaduna during
  religious riots. Moses was 11.
- He was playing football in the street when he was told.
- An uncle kept him hidden for about a week out of fear for his safety,
  while money was raised to send him out of the country.
- He arrived in England as an orphaned asylum seeker and was placed in
  foster care.
- He played for a local league side, Cosmos, and was picked up by Crystal
  Palace.
- He signed for Chelsea in 2012.
- He represented England at youth level, then accepted the call to play
  senior international football for Nigeria.
- He helped Nigeria win the 2013 Africa Cup of Nations -- their first in
  19 years -- and was named in the team of the tournament.

NOT CLAIMED: no invented dialogue, no speculation about the riots beyond
what is reported, no embellished detail about the foster placement.
"""
import config
from longform_creator import DocScript, Chapter, Beat, build_narration_file

SCRIPT = DocScript(
    title="He Was Playing Football in the Street When They Told Him",
    hook_card="HE WAS 11 YEARS OLD",
    description=(
        "Most people know Victor Moses as a Chelsea wing-back. Almost nobody knows "
        "that he was 11 years old, playing football in the street in Kaduna, when he "
        "was told his parents had been killed. He was hidden for a week, sent out of "
        "the country as an orphaned asylum seeker, and placed in foster care in "
        "England. Eleven years later he signed for Chelsea, and then chose to play "
        "for the country where it happened."
    ),
    tags=["victor moses", "chelsea", "nigeria", "football", "true story",
          "untold story", "motivation", "premier league", "documentary"],
    # SOCCER, not American football. Without this the shared "football"
    # theme resolves to NFL terms and the documentary opens on a gridiron.
    theme_queries={
        "football": ["soccer match stadium", "soccer players pitch",
                     "soccer ball goal net"],
        "crowd":    ["soccer fans stadium crowd", "crowd cheering match",
                     "stadium supporters"],
        "home":     ["suburban houses street", "empty room window light",
                     "airport terminal travellers"],
        "mood":     ["empty street evening", "children playing outside",
                     "silhouette walking sunset"],
    },
    sources=[
        "Victor Moses: A story of triumph over adversity -- Premier League official",
        "The Victor Moses story -- Tribuna",
        "Victor Moses: refugee aged 11, parents murdered, now Chelsea's unlikely hero -- Sporting Tribune",
        "Overcoming tragedy: The story of Victor Moses -- This is Africa",
        "Victor Moses: the asylum-seeking orphan who conquered the Premier League -- Chronicle NG",
    ],
    chapters=[
        Chapter("Cold Open", [
            Beat("If you watched the Premier League in the twenty-tens, you have seen "
                 "this man play.", "football stadium premier league", "stock"),
            Beat("A wing-back. Blue shirt. Chelsea. Up and down the right side for "
                 "ninety minutes.", "football player running pitch", "stock"),
            Beat("Solid, useful, easy to take for granted.",
                 "football match action", "stock"),
            Beat("The kind of player you would struggle to say anything memorable "
                 "about, if someone asked.", "football player close up", "stock"),
            Beat("He won a Premier League title. He played in a Europa League winning "
                 "side. He was, by any measure, a successful professional.",
                 "football trophy lifted", "stock"),
            Beat("Almost nobody watching knew what had happened to him.",
                 "empty stadium seats", "stock"),
            Beat("Subscribe before this one, because it is not the story you expect.",
                 "football stadium floodlights night", "stock"),
            Beat("When Victor Moses was eleven years old, he was playing football in "
                 "the street.", "children playing football street", "stock"),
            Beat("That is where they found him, to tell him his mother and father were "
                 "dead.", "empty street evening", "stock"),
            Beat("Not at school. Not at home. In the street, mid-game, the way any "
                 "child that age spends an afternoon.",
                 "street football children", "stock"),
            Beat("What happened between that moment and a Premier League title is one "
                 "of the least told stories in modern football.",
                 "trophy silver close up", "stock"),
        ]),

        Chapter("Act 1 - Kaduna, 2002", [
            Beat("Moses was born in Nigeria. His father, Austin, was a Christian "
                 "pastor. His mother was called Josephine.",
                 "church building exterior", "stock"),
            Beat("In 2002, religious riots reached their home in Kaduna.",
                 "empty street unrest", "stock"),
            Beat("Both of his parents were killed there.",
                 "empty house doorway", "stock"),
            Beat("He was not at home. He was outside, playing the game he would end up "
                 "doing for a living.", "football on street ground", "stock"),
            Beat("Think about the shape of that for a second.",
                 "football lying still", "stock"),
            Beat("The thing that later gave him a career is also, in the simplest "
                 "possible way, the reason he was not in the house.",
                 "empty football pitch dusk", "stock"),
            Beat("He was eleven.",
                 "child silhouette", "stock"),
            Beat("At eleven you are still being walked places. You are still being "
                 "told when to come inside.", "empty playground", "stock"),
            Beat("And in a single afternoon, both of the people whose job that was "
                 "were gone.", "empty family home", "stock"),
            Beat("There is no version of that a child processes properly. There is "
                 "only what happens next.", "child walking alone", "stock"),
            Beat("Kaduna in 2002 was not a quiet place for this to happen in.",
                 "empty street buildings", "stock"),
            Beat("Religious violence there had been killing people in numbers, in "
                 "waves, for years.", "empty road barricade", "stock"),
            Beat("His father was a pastor. That was not an incidental detail about "
                 "the family. In that context it was a position, and positions get "
                 "people targeted.", "church interior empty", "stock"),
            Beat("Which is why what came next was not grief management. It was a "
                 "security problem.", "locked door", "stock"),
        ]),

        Chapter("Act 2 - A Week in Hiding", [
            Beat("What happened next is the part that most retellings skip.",
                 "closed door dark room", "stock"),
            Beat("An uncle kept him hidden for about a week.",
                 "dark interior window", "stock"),
            Beat("Not out of grief. Out of fear that whoever had come for his parents "
                 "would come for him.", "empty corridor dark", "stock"),
            Beat("A boy who had just lost both parents, hidden in a room, because "
                 "being found would have meant the same thing.",
                 "small window light", "stock"),
            Beat("While he was hidden, money was being raised.",
                 "hands counting money", "stock"),
            Beat("Enough to get him out of the country entirely.",
                 "airport departure", "stock"),
            Beat("He arrived in England as an asylum seeker. An orphan, eleven years "
                 "old, with no family there.", "airport terminal arrivals", "stock"),
            Beat("He was placed into foster care.",
                 "suburban house england", "stock"),
            Beat("New country. New language environment. New family. Nothing he had "
                 "chosen.", "empty room window", "stock"),
            Beat("And no way back. There was nothing in Kaduna to go back to.",
                 "empty road distance", "stock"),
            Beat("Everyone he had known was either gone, or thousands of miles away, "
                 "or had just been part of getting him out.",
                 "airplane window clouds", "stock"),
            Beat("He was starting from actual zero, in a place he had never seen, at "
                 "an age where most children cannot make their own dinner.",
                 "child alone window", "stock"),
            Beat("And consider what asylum actually means at that age.",
                 "government building exterior", "stock"),
            Beat("It is a legal process. Interviews, paperwork, decisions made about "
                 "you by people you will never meet.",
                 "office paperwork desk", "stock"),
            Beat("A child does not navigate that. A child simply waits while it "
                 "happens to them.", "empty waiting room chairs", "stock"),
            Beat("Every part of his life was now being decided by strangers, in a "
                 "language and a system he had arrived into weeks earlier.",
                 "empty corridor office", "stock"),
        ]),

        Chapter("Act 3 - The Only Thing That Carried Over", [
            Beat("There was exactly one thing that came with him.",
                 "football ball close up", "stock"),
            Beat("The football.",
                 "football on grass", "stock"),
            Beat("He started playing for a local league side called Cosmos.",
                 "amateur football match", "stock"),
            Beat("Local. Nothing glamorous. The level almost every English child plays "
                 "at and stops.", "local football pitch", "stock"),
            Beat("Except that people started noticing him.",
                 "football training session", "stock"),
            Beat("Crystal Palace picked him up.",
                 "football academy training", "stock"),
            Beat("And this is the part where the story stops being about tragedy and "
                 "starts being about how good he actually was.",
                 "football player skill", "stock"),
            Beat("Because getting from foster care to a professional academy is not "
                 "luck. It is a level of talent that makes people move for you.",
                 "football coach watching", "stock"),
            Beat("In 2012, he signed for Chelsea.",
                 "football stadium big crowd", "stock"),
            Beat("Ten years after he was hidden in a room in Kaduna, he was a Chelsea "
                 "player.", "premier league stadium", "stock"),
            Beat("Understand how narrow that path is.",
                 "football academy pitch", "stock"),
            Beat("Thousands of talented children go through English academies every "
                 "year. Most never play a professional minute.",
                 "youth football training", "stock"),
            Beat("They have families, stability, someone driving them to training "
                 "twice a week.", "parent child football", "stock"),
            Beat("He had none of that, and he made it anyway.",
                 "lone footballer training", "stock"),
            Beat("There is a version of this story where the football is just a nice "
                 "detail. A hobby that happened to work out.",
                 "football ball still", "stock"),
            Beat("It is not that.",
                 "football boots close up", "stock"),
            Beat("For a child with no parents, no country, and no permanent home, a "
                 "football pitch is one of the only places where none of that is "
                 "relevant.", "empty pitch markings", "stock"),
            Beat("On the pitch he was not the orphan, or the asylum case, or the "
                 "foster placement. He was just the best player there.",
                 "footballer running with ball", "stock"),
            Beat("That is a very powerful thing to have when everything else about "
                 "your identity has been decided for you.",
                 "football under floodlights", "stock"),
        ]),

        Chapter("Act 4 - The Choice", [
            Beat("Then comes a decision most people never hear about, and it is the "
                 "most remarkable thing in this entire story.",
                 "football pitch centre circle", "stock"),
            Beat("Moses had played for England at youth level.",
                 "youth football team", "stock"),
            Beat("That was an option. He had grown up there. He had been raised there. "
                 "England was, by any normal definition, his football home.",
                 "england flag stadium", "stock"),
            Beat("He chose Nigeria.",
                 "nigeria flag", "stock"),
            Beat("The country where his parents were killed. The country he had been "
                 "smuggled out of as a child.",
                 "african stadium crowd", "stock"),
            Beat("Nobody would have blamed him for choosing England. He owed Nigeria "
                 "nothing.", "empty stadium tunnel", "stock"),
            Beat("Whatever his reasoning was, it was not the easy option.",
                 "football boots on grass", "stock"),
            Beat("England would have meant a bigger stage and an easier press.",
                 "press conference microphones", "stock"),
            Beat("Nigeria meant long flights, a different federation, and returning "
                 "again and again to the country he had been taken out of.",
                 "airport runway plane", "stock"),
            Beat("He did it anyway, and he kept doing it for years.",
                 "national anthem lineup", "stock"),
            Beat("He accepted the call to play senior international football for it.",
                 "national team lineup", "stock"),
            Beat("And in 2013, Nigeria won the Africa Cup of Nations.",
                 "football trophy celebration", "stock"),
            Beat("Their first in nineteen years.",
                 "football fans celebrating", "stock"),
            Beat("Moses was named in the team of the tournament.",
                 "football player celebrating", "stock"),
            Beat("The boy who was hidden in a room so nobody would find him, standing "
                 "in front of a whole country, wearing its shirt.",
                 "national team celebration", "stock"),
        ]),

        Chapter("Close", [
            Beat("It would be easy to end this by saying football saved him. That is "
                 "the version that fits neatly.", "football on pitch", "stock"),
            Beat("But look at what actually happened, in order.",
                 "empty stadium wide", "stock"),
            Beat("He was outside playing because he was eleven and that is what "
                 "eleven year olds do.", "children playing football", "stock"),
            Beat("He survived because of where he happened to be standing.",
                 "empty street", "stock"),
            Beat("He got out because people who were not rich put money together to "
                 "move him.", "hands giving money", "stock"),
            Beat("He got a career because a local coach, and then a professional club, "
                 "looked at a foster child and saw a footballer.",
                 "football coach training", "stock"),
            Beat("None of that was owed to him. All of it had to happen.",
                 "football stadium empty night", "stock"),
            Beat("And then, given the choice between the country that took him in and "
                 "the country that took his parents, he chose to represent the one "
                 "that hurt him.", "flag waving stadium", "stock"),
            Beat("Most people who watched him play for a decade never knew any of it.",
                 "football crowd watching", "stock"),
            Beat("He did not talk about it every week. There was no documentary "
                 "running alongside his career.", "empty press room", "stock"),
            Beat("He just turned up, played right wing-back, and went home.",
                 "football player tunnel", "stock"),
            Beat("Every squad in world football has someone carrying something like "
                 "this quietly.", "football team line up", "stock"),
            Beat("You will not know which one. They do not announce it.",
                 "football players walking out", "stock"),
            Beat("They just play, and let you assume the shirt is the whole person.",
                 "football shirt hanging", "stock"),
            Beat("Which is worth remembering the next time you watch a player you have "
                 "already decided is ordinary.",
                 "football player walking pitch", "stock"),
        ]),
    ],
)


def build():
    import os
    import longform_creator as lf
    import pro_shorts_creator as psc
    from logger import log

    issues = SCRIPT.validate()
    if issues:
        raise RuntimeError(f"validation failed: {issues}")
    log(SCRIPT.report())

    pool = lf.source_pool(SCRIPT, per_theme=3)
    beat_clips = lf.assign_visuals(SCRIPT, pool)
    vo_path = lf.generate_long_voiceover(SCRIPT)
    from moviepy import AudioFileClip
    dur = AudioFileClip(vo_path).duration
    log(f"narration: {dur/60:.2f} min")
    music = None
    try:
        music = psc.get_music(duration=min(dur, 600),
                              script={"hook": SCRIPT.title,
                                      "body": SCRIPT.description, "cta": ""})
    except Exception as e:
        log(f"music skipped ({e})")
    out = os.path.join(config.VIDEOS_DIR, "doc_moses.mp4")
    lf.render(SCRIPT, beat_clips, vo_path, music, out)
    print("VO_PATH=" + vo_path)
    return out, vo_path


if __name__ == "__main__":
    import sys
    if "--build" in sys.argv:
        build()
    else:
        print(SCRIPT.report())
        iss = SCRIPT.validate()
        print("\nValidation:", "PASSED" if not iss else "ISSUES")
        for i in iss:
            print("  -", i)
        build_narration_file(SCRIPT)
