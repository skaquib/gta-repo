"""
doc_garrincha.py — documentary #3.
"Doctors Said He Would Never Walk. He Won the World Cup Without Pele."

WHY THIS STORY (2026-09-13):
The brief: player-related real-life stories -- untold, shocking, hidden
talent, motivation, the kind of thing an audience opens out of curiosity.
Checked and rejected first:
  1. Luka Modric (war childhood)    -> told constantly, every tournament.
  2. Alphonso Davies (refugee camp) -> heavily covered by Bayern/Bundesliga
     media, and the subject of many existing videos.
  3. Bert Trautmann (POW keeper)    -> extraordinary, but there is a 2018
     feature film ("The Keeper"), and "you are copying a common movie" was
     the exact note that killed the Dhoni draft.
Garrincha has no mainstream global film, is barely known to viewers under
thirty, and is the rarest combination the brief asks for: a man written off
as disabled at birth who became the best player at a World Cup, then died
broke at 49. Motivation and tragedy in one story.

AUDIENCE FIT: soccer is this channel's core sport and its largest
geography (IN ~64%) follows it. Brazil/World Cup history carries there.

VERIFIED (2026-09-13 -- Wikipedia (Garrincha); FIFA official "100 great
World Cup moments"; Medium/Amit Katwala "The angel with bent legs";
Football Whispers; Telegrafi):
- Born Manuel Francisco dos Santos, 28 October 1933, Pau Grande, Brazil.
- Born with one leg six centimetres shorter than the other, the legs
  bending in opposite directions, a deformed spine and pelvic imbalance.
  A doctor certified him crippled in childhood and advised no physical
  activity at all.
- "Garrincha" is the name of a small Brazilian bird, a wren.
- Signed by Botafogo in 1953 at 19; scored a hat-trick on his first-team
  debut against Bonsucesso on 19 July 1953.
- Botafogo: 238 appearances, 84 goals, 1953-1965.
- Brazil: 50 caps, 12 goals, 1955-1966.
- Brazil never lost a single match in which both Garrincha and Pele played.
- 1958 World Cup: named to the All-Star team; set up two goals for Vava in
  the final against Sweden.
- 1962 World Cup: Pele was injured after the second match. Garrincha scored
  four goals, including two against England and two against Chile, and
  became the first player to win the World Cup, the Golden Ball and the
  Golden Boot in the same tournament.
- 1962 semi-final v Chile (4-2): a 20-yard left-foot shot and a header;
  sent off in the 83rd minute, yet played in the final.
- Clubs had him sign blank contracts and filled in the figures later. Bank
  officials who visited his home found cash rotting in cupboards, fruit
  bowls and behind furniture.
- April 1969: he crashed into a lorry; his mother-in-law was killed.
- Died 20 January 1983, aged 49, of cirrhosis of the liver, in an alcoholic
  coma, after eight hospitalisations in his final year.
- His funeral procession from the Maracana to Pau Grande drew millions.
- Epitaph: "Here rests in peace the one who was the Joy of the People --
  Mane Garrincha."

NOT CLAIMED: no invented dialogue. Sources disagree on WHICH leg was the
shorter one, so the script says "one leg" and never picks a side.
"""
import config
from longform_creator import DocScript, Chapter, Beat, build_narration_file

SCRIPT = DocScript(
    title="Doctors Said He Would Never Walk. He Won the World Cup Without Pele.",
    hook_card="THEY CALLED HIM CRIPPLED",
    description=(
        "A Brazilian doctor examined a small boy with a deformed spine, a dislocated "
        "knee and one leg six centimetres shorter than the other, and recommended he "
        "never do physical activity again. That boy became Garrincha -- the man who "
        "won Brazil the 1962 World Cup after Pele got injured, and the only player to "
        "take the World Cup, the Golden Ball and the Golden Boot in one tournament. "
        "Brazil never lost a match with him and Pele on the pitch together. He died "
        "at 49, broke, with cash rotting in his cupboards."
    ),
    tags=["garrincha", "brazil", "world cup", "1962", "pele", "football",
          "true story", "untold story", "motivation", "documentary", "soccer"],
    # SOCCER. Without this the shared "football" theme resolves to NFL terms
    # and the documentary opens on a gridiron (happened on doc #2).
    theme_queries={
        "football": ["soccer match stadium", "soccer players pitch",
                     "soccer ball goal net"],
        "crowd":    ["soccer fans stadium crowd", "crowd cheering match",
                     "stadium supporters"],
        "home":     ["poor village dirt road", "old houses street",
                     "child walking dirt path"],
        "mood":     ["empty street evening", "children playing outside",
                     "silhouette walking sunset"],
    },
    # Per-subject buckets. Order matters: specific before general. About 38
    # clips total -- 26 rendered clean on doc #2, one-reader-per-beat (90+)
    # crashed ffmpeg with Errno 22, so this stays comfortably between.
    # "old house interior" (bank officials finding cash in his house) lives
    # in decline, not childhood: childhood rendered it as an aerial of a
    # modern English town with a Tesco sign (2026-09-14 verification).
    visual_buckets={
        "referee":   {"match": ["referee", "injured player"],
                      "queries": ["soccer referee red card", "soccer referee whistle",
                                  "injured soccer player on pitch"], "n": 2},
        "trophy":    {"match": ["trophy"],
                      "queries": ["soccer trophy celebration", "gold trophy close up"], "n": 3},
        "memorial":  {"match": ["candle", "gravestone", "cemetery", "procession",
                                "large crowd street", "sunset silhouette"],
                      "queries": ["candle memorial", "cemetery gravestone",
                                  "crowd street procession", "sunset silhouette"], "n": 3},
        "medical":   {"match": ["doctor", "x ray", "hospital"],
                      "queries": ["doctor examining patient", "x ray scan",
                                  "hospital corridor", "empty hospital bed"], "n": 3},
        "contracts": {"match": ["paper documents", "signing document", "banknotes", "cash"],
                      "queries": ["old paper documents", "signing contract pen",
                                  "old banknotes cash"], "n": 3},
        "decline":   {"match": ["empty street", "empty room", "glass bar",
                                "road at night", "empty road", "house interior"],
                      "queries": ["empty street evening", "empty room window light",
                                  "empty glass bar counter", "road at night headlights"], "n": 3},
        "childhood": {"match": ["child", "village", "dirt road", "old houses",
                                "old factory", "family home"],
                      "queries": ["children playing football street", "child walking dirt road",
                                  "poor village dirt road", "old factory building",
                                  "old house interior"], "n": 4},
        "stadium":   {"match": ["stadium", "empty soccer pitch", "scoreboard",
                                "team lineup", "club badge", "fans"],
                      "queries": ["soccer stadium crowd", "empty soccer stadium seats",
                                  "stadium floodlights night", "soccer team lineup",
                                  "empty soccer pitch"], "n": 6},
        "soccer":    {"match": ["soccer", "football"],
                      "queries": ["soccer player dribbling", "soccer match action",
                                  "soccer player running pitch", "soccer goal net ball",
                                  "soccer players pitch", "soccer player celebration",
                                  "soccer header ball"], "n": 9},
        "misc":      {"match": ["bird", "brazil flag"],
                      "queries": ["small bird branch", "brazil flag waving"], "n": 2},
    },
    sources=[
        "Garrincha -- Wikipedia",
        "Chile bows to glorious Garrincha, 100 great World Cup moments -- FIFA official",
        "World Cup Stories 1962: Garrincha, the angel with bent legs -- Amit Katwala",
        "Unforgettable World Cup Moments: 1962's angel with the bent legs -- Football Whispers",
        "Garrincha had a shorter leg, but that didn't stop him -- Telegrafi",
    ],
    chapters=[
        Chapter("Cold Open", [
            Beat("In nineteen thirty three, in a small factory town in Brazil, a doctor "
                 "examined a newborn boy.", "old village houses", "stock"),
            Beat("What he wrote down was, in effect, a sentence.",
                 "doctor writing notes", "stock"),
            Beat("The child had a deformed spine. A pelvic imbalance. A dislocated knee.",
                 "x ray medical", "stock"),
            Beat("One leg was six centimetres shorter than the other.",
                 "child legs walking", "stock"),
            Beat("And the legs did not bend the same way. One turned out. One turned in.",
                 "child walking dirt path", "stock"),
            Beat("The recommendation was simple. No physical activity. None at all.",
                 "empty room window light", "stock"),
            Beat("Twenty nine years later, that boy was the best footballer on the "
                 "planet.", "soccer stadium floodlights night", "stock"),
            Beat("Not one of the best. The best.", "soccer trophy lifted", "stock"),
            Beat("He won a World Cup almost on his own, after the greatest player alive "
                 "got injured and went home.", "soccer match action", "stock"),
            Beat("Subscribe before this one, because you have probably never heard his "
                 "name.", "soccer fans stadium crowd", "stock"),
            Beat("He was called Garrincha. It means a little bird. A wren.",
                 "small bird branch", "stock"),
            Beat("And this is what happened to him.", "empty street evening", "stock"),
        ]),

        Chapter("Act 1 - The boy they wrote off", [
            Beat("His real name was Manuel Francisco dos Santos.",
                 "old houses street", "stock"),
            Beat("He was born on the twenty eighth of October, nineteen thirty three, "
                 "in Pau Grande.", "poor village dirt road", "stock"),
            Beat("A company town, built around a textile factory, outside Rio de "
                 "Janeiro.", "old factory building", "stock"),
            Beat("Poor. Small. The kind of place nobody leaves.",
                 "dirt road village", "stock"),
            Beat("The doctors were not being cruel. By the medicine of the time, they "
                 "were being accurate.", "doctor examining", "stock"),
            Beat("A child with that spine and those legs was not supposed to run.",
                 "child legs walking", "stock"),
            Beat("He ran anyway.", "children playing football street", "stock"),
            Beat("And here is the part nobody could have predicted.",
                 "soccer ball grass", "stock"),
            Beat("The legs that were supposed to cripple him turned out to be a weapon.",
                 "soccer player dribbling", "stock"),
            Beat("Because they bent in opposite directions, his balance did not work "
                 "like other people's.", "soccer player close up", "stock"),
            Beat("When he leaned one way, his body did not have to follow.",
                 "soccer player dribbling", "stock"),
            Beat("Defenders read the hips. The hips lied.",
                 "soccer defender tackle", "stock"),
            Beat("He could send a full grown professional the wrong way and simply walk "
                 "past him.", "soccer player running pitch", "stock"),
            Beat("Not once in a game. Again, and again, and again, in the same game.",
                 "soccer match action", "stock"),
            Beat("He was not fast in the way we measure fast now.",
                 "soccer players pitch", "stock"),
            Beat("He was unreadable. Which is worse.",
                 "soccer player close up", "stock"),
            Beat("Think about what that actually means for a moment.",
                 "soccer player close up", "stock"),
            Beat("Every coaching manual ever written treats a body like his as a "
                 "problem to be corrected.", "old paper documents", "stock"),
            Beat("Something to brace, to operate on, to keep off a field.",
                 "hospital corridor", "stock"),
            Beat("Nobody imagined it could be an advantage, because nobody had ever "
                 "seen one used that way.", "soccer player dribbling", "stock"),
            Beat("He was not overcoming his body. He was using it.",
                 "soccer player running pitch", "stock"),
            Beat("That distinction is the whole story.",
                 "soccer ball grass", "stock"),
        ]),

        Chapter("Act 2 - Botafogo, and a hat-trick nobody expected", [
            Beat("He did not go to a famous academy. There was no academy.",
                 "empty soccer pitch", "stock"),
            Beat("He played in the factory town, for the factory team, into his late "
                 "teens.", "amateur soccer match", "stock"),
            Beat("In nineteen fifty three, at nineteen years old, Botafogo signed him.",
                 "soccer club stadium", "stock"),
            Beat("He was already married. He already had children.",
                 "family home old", "stock"),
            Beat("On the nineteenth of July, nineteen fifty three, he made his first "
                 "team debut against Bonsucesso.", "soccer stadium crowd", "stock"),
            Beat("He scored a hat-trick.", "soccer goal net ball", "stock"),
            Beat("Three goals. On debut. From the boy who was told never to do physical "
                 "activity.", "soccer celebration players", "stock"),
            Beat("He stayed at Botafogo for twelve years.",
                 "soccer club badge", "stock"),
            Beat("Two hundred and thirty eight appearances. Eighty four goals.",
                 "soccer match action", "stock"),
            Beat("For a winger, in that era, those are absurd numbers.",
                 "soccer goal net ball", "stock"),
            Beat("And he was doing it while walking, every day, on legs that were not "
                 "the same length.", "child legs walking", "stock"),
            Beat("Nobody at the club fixed that. Nobody could.",
                 "doctor examining", "stock"),
            Beat("It was simply how he was built, and how he played.",
                 "soccer player dribbling", "stock"),
            Beat("And then Brazil called him up.", "brazil flag", "stock"),
        ]),

        Chapter("Act 3 - 1958, and the statistic that should not exist", [
            Beat("Nineteen fifty eight. The World Cup in Sweden.",
                 "vintage stadium crowd", "stock"),
            Beat("Brazil had never won it. Not once.",
                 "soccer trophy close up", "stock"),
            Beat("In that squad was a seventeen year old named Pele.",
                 "young soccer player", "stock"),
            Beat("And on the right wing was Garrincha.",
                 "soccer player running pitch", "stock"),
            Beat("In the final against Sweden, he set up two goals for Vava.",
                 "soccer player crossing ball", "stock"),
            Beat("Brazil won their first World Cup. Garrincha was named in the team of "
                 "the tournament.", "soccer trophy lifted", "stock"),
            Beat("But the number that really tells you what he was is this one.",
                 "scoreboard stadium", "stock"),
            Beat("Across his entire international career, Brazil never lost a single "
                 "match in which both Garrincha and Pele played.",
                 "soccer team lineup", "stock"),
            Beat("Not one. Not a friendly, not a qualifier, not a World Cup game.",
                 "soccer players pitch", "stock"),
            Beat("Two men on the same pitch, and defeat simply did not happen.",
                 "soccer match action", "stock"),
            Beat("Pele is remembered as the greatest of all time, and he earned that.",
                 "young soccer player", "stock"),
            Beat("But that record is not a record about one player.",
                 "soccer team lineup", "stock"),
            Beat("It took both of them on the field for Brazil to become unbeatable.",
                 "soccer players pitch", "stock"),
            Beat("One half of the most dominant partnership in football history is a "
                 "household name.", "soccer fans stadium crowd", "stock"),
            Beat("The other half, most people under thirty have never heard of.",
                 "empty stadium seats", "stock"),
        ]),

        Chapter("Act 4 - 1962, the tournament he took", [
            Beat("Nineteen sixty two. Chile.", "vintage stadium crowd", "stock"),
            Beat("Brazil arrive as champions. Pele is now the most famous footballer in "
                 "the world.", "soccer fans stadium crowd", "stock"),
            Beat("And in the second match, Pele is injured.",
                 "injured player pitch", "stock"),
            Beat("His tournament is over.", "empty stadium seats", "stock"),
            Beat("Brazil should have been finished. The best player alive was gone.",
                 "empty soccer pitch", "stock"),
            Beat("Instead, Garrincha decided to win it himself.",
                 "soccer player running pitch", "stock"),
            Beat("Against England, he scored twice.",
                 "soccer goal net ball", "stock"),
            Beat("In the semi-final against the host nation, Chile, he scored twice "
                 "again.", "soccer celebration players", "stock"),
            Beat("A twenty yard shot with his left foot. And a header.",
                 "soccer header ball", "stock"),
            Beat("A header, from the small man with the broken legs.",
                 "soccer player jumping", "stock"),
            Beat("Brazil won that semi-final four two.",
                 "scoreboard stadium", "stock"),
            Beat("And then, in the eighty third minute, he was sent off.",
                 "referee red card", "stock"),
            Beat("Which should have ruled him out of the World Cup final.",
                 "referee whistle", "stock"),
            Beat("He played in the final anyway.",
                 "soccer stadium floodlights night", "stock"),
            Beat("Brazil retained the World Cup.", "soccer trophy lifted", "stock"),
            Beat("Garrincha finished as the tournament's best player, and its joint top "
                 "scorer.", "soccer player celebration", "stock"),
            Beat("He became the first player in history to win the World Cup, the Golden "
                 "Ball and the Golden Boot in the same tournament.",
                 "soccer trophy close up", "stock"),
            Beat("He had carried a nation through a World Cup with legs a doctor once "
                 "said should never run.", "soccer player running pitch", "stock"),
        ]),

        Chapter("Act 5 - What it cost", [
            Beat("And this is where the story stops being triumphant.",
                 "empty street evening", "stock"),
            Beat("Garrincha could not read a contract.",
                 "old paper documents", "stock"),
            Beat("His clubs had him sign blank ones, and filled in the figures "
                 "afterwards.", "signing document pen", "stock"),
            Beat("He did not understand money, and nobody around him had any reason to "
                 "teach him.", "old banknotes cash", "stock"),
            Beat("When bank officials came to his house, they found cash rotting.",
                 "old house interior", "stock"),
            Beat("In cupboards. In fruit bowls. Behind the furniture.",
                 "old banknotes cash", "stock"),
            Beat("Money he had earned and simply never spent, because he did not know "
                 "what it was for.", "empty room window light", "stock"),
            Beat("He drank. Heavily, for most of his adult life.",
                 "empty glass bar", "stock"),
            Beat("In April nineteen sixty nine, he crashed into a lorry.",
                 "road at night headlights", "stock"),
            Beat("His mother-in-law was killed.", "empty road rain", "stock"),
            Beat("His career trailed off through smaller and smaller clubs.",
                 "empty soccer pitch", "stock"),
            Beat("The man Brazil could not lose with became a man nobody called.",
                 "empty stadium seats", "stock"),
            Beat("There is a version of this story that stops at the trophy.",
                 "soccer trophy lifted", "stock"),
            Beat("It is the version that gets shared, because it is comfortable.",
                 "soccer fans stadium crowd", "stock"),
            Beat("Boy is told he cannot. Boy does. The end.",
                 "children playing football street", "stock"),
            Beat("But that version leaves out what the game took back from him.",
                 "empty street evening", "stock"),
            Beat("He was protected by nobody. Advised by nobody. Educated by nobody.",
                 "old house interior", "stock"),
            Beat("A man who could not be stopped on a football pitch was completely "
                 "defenceless off it.", "empty room window light", "stock"),
            Beat("The same world that cheered him took everything he earned, and "
                 "handed it back as paper he could not read.",
                 "old paper documents", "stock"),
        ]),

        Chapter("Close - The Joy of the People", [
            Beat("On the twentieth of January, nineteen eighty three, Garrincha died.",
                 "candle memorial", "stock"),
            Beat("He was forty nine years old.", "empty stadium seats", "stock"),
            Beat("Cirrhosis of the liver. An alcoholic coma.",
                 "hospital corridor", "stock"),
            Beat("He had been admitted to hospital eight times in his final year.",
                 "hospital bed empty", "stock"),
            Beat("He died with almost nothing.", "empty room window light", "stock"),
            Beat("And then Brazil remembered who he was.",
                 "soccer fans stadium crowd", "stock"),
            Beat("His funeral procession ran from the Maracana back to Pau Grande. Back "
                 "to the factory town.", "crowd street procession", "stock"),
            Beat("Millions of people lined the route.",
                 "large crowd street", "stock"),
            Beat("The boy the doctors wrote off went home past millions of people "
                 "standing in the road.", "crowd street procession", "stock"),
            Beat("On his grave they wrote a single line.",
                 "gravestone cemetery", "stock"),
            Beat("Here rests in peace the one who was the Joy of the People.",
                 "sunset silhouette", "stock"),
            Beat("Mane Garrincha.", "soccer ball grass", "stock"),
            Beat("He was told, before he could walk, that his body would never let him "
                 "run.", "child legs walking", "stock"),
            Beat("It turned out his body was the reason nobody could stop him.",
                 "soccer player dribbling", "stock"),
            Beat("If this one got to you, subscribe. There is a story like this every "
                 "week.", "soccer stadium floodlights night", "stock"),
        ]),
    ],
)


def build():
    import os
    import longform_creator as lf
    from logger import log

    log("Sourcing clip pool...")
    # source_pool() returns {theme: [paths]}. render() wants one clip PER BEAT.
    # assign_visuals() is the step between them -- it rotates within each
    # beat's theme so the same shot never lands on two consecutive beats, and
    # falls back across themes when one came back empty. Skipping it makes
    # every beat fail with "'<theme>' not found" and the render never starts.
    missing = lf.unmatched_beats(SCRIPT)
    if missing:
        raise RuntimeError(f"beats with no visual bucket (would render off-topic): {missing}")
    pool = lf.source_buckets(SCRIPT)
    beat_clips = lf.assign_visuals(SCRIPT, pool)
    alternates = lf.beat_alternates(SCRIPT, pool)
    log("Generating long voiceover...")
    vo_path = lf.generate_long_voiceover(SCRIPT)
    music = None
    try:
        import pro_shorts_creator as psc
        from moviepy import AudioFileClip
        music = psc.get_music(duration=AudioFileClip(vo_path).duration,
                              script={"hook": SCRIPT.title,
                                      "body": SCRIPT.description, "cta": ""})
    except Exception as e:
        log(f"music skipped ({e})")
    out = os.path.join(config.VIDEOS_DIR, "doc_garrincha.mp4")
    lf.render(SCRIPT, beat_clips, vo_path, music, out, alternates=alternates)
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
