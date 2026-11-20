"""
doc_rinku.py — documentary #4 (2026-09-17).
"He Was Offered a Job Mopping Floors. Now He's a World Cup Champion"

WHY THIS STORY:
Owner's brief: real player life stories -- untold, shocking, motivating
("like Ronaldo cleaning the road"), not a copy of a common movie.
2026-09-17 trend scans (YouTube API, region IN):
  - top Shorts: named current stars recur (Surya Kumar Yadav, Bumrah,
    Harmanpreet, Mandhana); the closest match to our format was a "Why did
    <famous players>..." history Short at 696K.
  - top long-form (last 30 days): star life stories win -- "Untold Story"
    1.7M, Brazil 7-1 419K, "Deadliest Batsman the World Forgot" 108K.
    Median length ~10 min; about a third in Hindi.
Rinku Singh is a famous current Indian star, the mop-job detail is the
brief almost word for word, and there is no feature film about him.

VERIFIED (2026-09-17):
  Wikipedia (Rinku Singh (cricketer)):
  - Born 12 Oct 1997, Aligarh, Uttar Pradesh; third of five siblings.
  - Father Khanchand Singh worked for a gas cylinder distribution company;
    the family lived in two-room accommodation provided by the employer.
  - List A debut 5 Mar 2014 v Vidarbha, 83 runs. UP's leading run-scorer
    in 2018-19 Ranji Trophy: 953 runs in 10 matches.
  - Bought by Kings XI Punjab (2017); by KKR in 2018 for Rs 8 million.
  - 9 Apr 2023 v Gujarat Titans: five sixes in the final over, bowled by
    Yash Dayal -- the most runs scored in a last over to win an IPL match.
  - T20I debut 18 Aug 2023 v Ireland; ODI debut 19 Dec 2023 v South Africa.
  - 190-run partnership with Rohit Sharma, India's highest T20I stand.
  - 2025 Asia Cup winner; 2026 T20 World Cup champion.
  The Quint (IPL 2023 profile): father delivered LPG cylinders; a brother
  drove an auto-rickshaw; tin-roofed two-room house; heavy debt; practised
  up to 14 hours a day; the five sixes were consecutive; KKR paid Rs 80 lakh.
  ESPNcricinfo (Brar) / search summary: ~Rs 5 lakh of debt around 2015;
  Rinku saved his UP Under-19 daily allowance towards it.
  Sportskeeda: Harbhajan Singh -- "There was a time when he was offered a
  job to mop the floor"; Rinku gifted his father a bike; a viral video
  showed his father delivering LPG cylinders; retained by KKR for Rs 13
  crore ahead of the IPL 2025 auction; bought a new bungalow in Aligarh.
  CricTracker: quote headline "Every ball that I hit out of the ground was
  dedicated to people who sacrificed so much for me"; Khanchand Singh died
  27 Feb 2026 of stage four liver cancer during the Super 8 stage of the
  2026 T20 World Cup; Rinku was not in the XI v Zimbabwe, fielded as a
  substitute, then left the team camp for Aligarh.

NOT CLAIMED / HANDLED:
  - The mop job: The Quint says he took it, other accounts say he turned it
    down. The script says accounts differ.
  - No venue, no runs-required figure for the 2023 last over, no claim that
    Rinku returned or played in the World Cup knockouts, no claim about his
    role in India winning -- none of it is in the sources above.
  - The viral cylinder video is not dated, so it is not tied to a year.
"""
import config
from longform_creator import DocScript, Chapter, Beat, build_narration_file

SCRIPT = DocScript(
    title="He Was Offered a Job Mopping Floors. Now He's a World Cup Champion 🏏",
    hook_card="OFFERED A MOP. CHOSE A BAT.",
    description=(
        "Rinku Singh's father delivered gas cylinders. His family of seven lived in two "
        "rooms and owed around five lakh rupees. As a teenager he saved his Under-19 "
        "allowance to help pay it back -- and at one point he was offered a job mopping "
        "floors. Five years after KKR bought him for 80 lakh, he hit five sixes in a row "
        "in the last over. In 2026, during the T20 World Cup, his father died. India "
        "went on to win it."
    ),
    tags=["rinku singh", "rinku singh story", "kkr", "indian cricket", "t20 world cup",
          "five sixes", "motivation", "true story", "untold story", "cricket documentary"],
    # Specific buckets first: the first bucket whose match terms appear in a
    # beat's visual query wins.
    visual_buckets={
        "cylinder": {"match": ["cylinder", "gas", "delivery"],
                     "queries": ["gas cylinder delivery", "lpg gas cylinder",
                                 "delivery man carrying load"], "n": 3},
        "mop":      {"match": ["mop", "sweep", "floor"],
                     "queries": ["mopping floor", "sweeping floor broom"], "n": 2},
        "money":    {"match": ["rupee", "money", "cash", "debt"],
                     "queries": ["indian rupee notes", "counting money"], "n": 3},
        "hospital": {"match": ["hospital", "candle", "alone"],
                     "queries": ["hospital corridor", "candle memorial",
                                 "man sitting alone sad"], "n": 3},
        "trophy":   {"match": ["trophy", "celebration", "fireworks"],
                     "queries": ["trophy celebration", "fireworks stadium",
                                 "team celebration"], "n": 3},
        "sixes":    {"match": ["six", "batsman", "batting"],
                     "queries": ["cricket batsman hitting six", "cricket batsman batting",
                                 "cricket batsman shot"], "n": 7},
        "stadium":  {"match": ["stadium", "crowd", "floodlights"],
                     "queries": ["cricket stadium crowd", "stadium floodlights night",
                                 "cheering crowd"], "n": 6},
        "family":   {"match": ["family", "father", "motorcycle", "home"],
                     "queries": ["indian family home", "father and son",
                                 "man riding motorcycle india"], "n": 3},
        "town":     {"match": ["town", "street", "rickshaw", "roof", "house"],
                     "queries": ["indian town street", "auto rickshaw india",
                                 "small house india", "tin roof houses"], "n": 5},
        "mood":     {"match": ["sunset", "road", "clock", "window", "silhouette"],
                     "queries": ["sunset silhouette", "empty road evening",
                                 "clock ticking", "window light room"], "n": 4},
        "cricket":  {"match": ["cricket", "bowler", "nets"],
                     "queries": ["cricket match", "cricket bowler bowling",
                                 "cricket practice nets"], "n": 8},
    },
    sources=[
        "Rinku Singh (cricketer) -- Wikipedia",
        "IPL 2023: How Rinku Singh rose from Aligarh's streets of struggle to KKR's poster boy -- The Quint",
        "Brar: For Uttar Pradesh's Rinku Singh, hardships are opportunities -- ESPNcricinfo",
        "\"There was a time when he was offered a job to mop the floor\" - Harbhajan Singh -- Sportskeeda",
        "Rinku Singh's father passes away after battle with liver cancer -- CricTracker",
        "\"Every ball that I hit out of the ground was dedicated to people who sacrificed so much for me\" -- CricTracker",
        "Rinku Singh buys new bungalow in Aligarh after being retained by KKR for Rs 13 crore -- Sportskeeda",
    ],
    chapters=[
        Chapter("Cold Open", [
            Beat("April twenty twenty three. Kolkata against Gujarat. The last over, and "
                 "the game looks gone.", "cricket stadium crowd night", "stock"),
            Beat("A left-hander from Aligarh hits a six.", "cricket batsman hitting six", "stock"),
            Beat("Then another. And another. And another. And one more.",
                 "cricket batsman batting", "stock"),
            Beat("Five sixes in a row. Kolkata win.", "trophy celebration", "stock"),
            Beat("No one in IPL history had scored more runs in a final over to win a "
                 "match.", "stadium floodlights night", "stock"),
            Beat("His name was Rinku Singh, and most people watching had never heard it.",
                 "cheering crowd", "stock"),
            Beat("What they did not know is where he came from.", "indian town street", "stock"),
            Beat("His father delivered gas cylinders for a living.", "gas cylinder delivery", "stock"),
            Beat("His family of seven lived in two rooms.", "small house india", "stock"),
            Beat("And at one point, the job on offer to him was mopping floors.",
                 "mopping floor", "stock"),
            Beat("Subscribe before this one, because this is not the story the highlights "
                 "show you.", "cricket stadium crowd", "stock"),
            Beat("This is how he got from those two rooms to a World Cup.",
                 "sunset silhouette", "stock"),
        ]),

        Chapter("Act 1 - Two rooms in Aligarh", [
            Beat("Rinku Singh was born on the twelfth of October, nineteen ninety seven, "
                 "in Aligarh, in Uttar Pradesh.", "indian town street", "stock"),
            Beat("He was the third of five children.", "indian family home", "stock"),
            Beat("His father, Khanchand Singh, worked for a gas cylinder distribution "
                 "company.", "lpg gas cylinder", "stock"),
            Beat("The job came with somewhere to live. Two rooms, provided by his father's "
                 "employer, under a tin roof.", "tin roof houses", "stock"),
            Beat("One of his brothers drove an auto-rickshaw.", "auto rickshaw india", "stock"),
            Beat("In a house like that, every rupee already has somewhere to go.",
                 "indian rupee notes", "stock"),
            Beat("And cricket, for a family like that, does not look like a career.",
                 "cricket practice nets", "stock"),
            Beat("It looks like a boy who is not earning.", "empty road evening", "stock"),
            Beat("He came up through the system anyway. Under sixteen, under nineteen, "
                 "under twenty three, all for Uttar Pradesh.", "cricket match", "stock"),
            Beat("He played for Central Zone at under nineteen level too.",
                 "cricket bowler bowling", "stock"),
            Beat("By around twenty fifteen, the family owed roughly five lakh rupees.",
                 "counting money", "stock"),
            Beat("For that household, that was not a number. It was a wall.",
                 "window light room", "stock"),
            Beat("By then, Rinku was playing for Uttar Pradesh at under nineteen level.",
                 "cricket match", "stock"),
            Beat("He did not spend his daily allowance. He saved it, to help pay back the "
                 "debt.", "counting money", "stock"),
            Beat("Stop on that for a second.", "clock ticking", "stock"),
            Beat("A teenager, picked to represent his state, putting his match money "
                 "towards his family's loans.", "cricket bowler bowling", "stock"),
        ]),

        Chapter("Act 2 - The mop", [
            Beat("And then comes the moment that has since become part of his legend.",
                 "window light room", "stock"),
            Beat("Rinku was offered a job sweeping and mopping floors at a coaching "
                 "centre.", "sweeping floor broom", "stock"),
            Beat("Harbhajan Singh has told the story too. There was a time, he said, when "
                 "Rinku was offered a job to mop the floor.", "mopping floor", "stock"),
            Beat("Accounts differ on what happened next. Some say he took the job for a "
                 "while. Others say he turned it down.", "sweeping floor broom", "stock"),
            Beat("Plenty of boys in that position would have taken the steady wage and never "
                 "looked back. Nobody would have blamed them.", "indian town street", "stock"),
            Beat("Every version agrees on one thing. He did not stay there. He went back "
                 "to cricket.", "cricket practice nets", "stock"),
            Beat("Reports say he practised for as long as fourteen hours a day.",
                 "cricket batsman batting", "stock"),
            Beat("There is a cruel maths to sport in a family like his.", "clock ticking", "stock"),
            Beat("Every hour you spend training is an hour you are not earning.",
                 "cricket bowler bowling", "stock"),
            Beat("If it works, everyone calls it a sacrifice.", "cheering crowd", "stock"),
            Beat("If it does not, everyone calls it a waste.", "empty road evening", "stock"),
            Beat("Rinku kept betting the hours anyway.", "cricket practice nets", "stock"),
            Beat("Uttar Pradesh gave him his List A debut in March twenty fourteen, "
                 "against Vidarbha.", "cricket match", "stock"),
            Beat("He scored eighty three.", "cricket batsman shot", "stock"),
            Beat("In the twenty eighteen nineteen Ranji Trophy, he was his state's leading "
                 "run scorer.", "cricket batsman batting", "stock"),
            Beat("His first class debut had come in November twenty sixteen, in the Ranji "
                 "Trophy, against Hyderabad.", "cricket stadium crowd", "stock"),
            Beat("Two seasons later, he was the one carrying his state's batting.",
                 "cricket batsman shot", "stock"),
            Beat("Nine hundred and fifty three runs in ten matches.", "cricket match", "stock"),
        ]),

        Chapter("Act 3 - A contract is not a career", [
            Beat("IPL scouts had noticed.", "cricket stadium crowd", "stock"),
            Beat("Kings Eleven Punjab picked him up first, in twenty seventeen.",
                 "stadium floodlights night", "stock"),
            Beat("Then, in twenty eighteen, Kolkata Knight Riders bought him for eighty "
                 "lakh rupees.", "indian rupee notes", "stock"),
            Beat("For a family that had been five lakh in debt, that number was almost "
                 "impossible to picture.", "counting money", "stock"),
            Beat("But an IPL contract is not an IPL career.", "cricket match", "stock"),
            Beat("The breakthrough took years.", "clock ticking", "stock"),
            Beat("Think about what those years look like from the inside.",
                 "window light room", "stock"),
            Beat("Every season, new names arrive. Every auction, someone younger is "
                 "available.", "stadium floodlights night", "stock"),
            Beat("For any player stuck in that position, one question gets louder every "
                 "year. Is this ever going to work?", "empty road evening", "stock"),
            Beat("Five years passed between that contract and the night that made him "
                 "famous.", "sunset silhouette", "stock"),
            Beat("Five years of being a name on a squad list, waiting for one chance to "
                 "matter.", "cricket practice nets", "stock"),
        ]),

        Chapter("Act 4 - Five sixes", [
            Beat("The ninth of April, twenty twenty three. Kolkata against Gujarat Titans.",
                 "cricket stadium crowd night", "stock"),
            Beat("The last over was bowled by Yash Dayal.", "cricket bowler bowling", "stock"),
            Beat("By every normal measure, the game was over.", "stadium floodlights night", "stock"),
            Beat("Then Rinku Singh hit a six.", "cricket batsman hitting six", "stock"),
            Beat("And another.", "cricket batsman shot", "stock"),
            Beat("And another.", "cricket batsman hitting six", "stock"),
            Beat("And another.", "cricket batsman batting", "stock"),
            Beat("And one more.", "cricket batsman hitting six", "stock"),
            Beat("Five sixes in a row. Kolkata won.", "team celebration", "stock"),
            Beat("For context: at the twenty sixteen T20 World Cup, Carlos Brathwaite hit "
                 "four sixes in a row and became a legend.", "cricket stadium crowd", "stock"),
            Beat("Rinku hit five.", "cricket batsman hitting six", "stock"),
            Beat("No one in the history of the IPL had scored more runs in a final over to "
                 "win a match.", "fireworks stadium", "stock"),
            Beat("Overnight, the boy from two rooms in Aligarh was the most talked about "
                 "cricketer in the country.", "cheering crowd", "stock"),
            Beat("He has said that every ball he hit out of the ground was dedicated to the "
                 "people who sacrificed so much for him.", "father and son", "stock"),
        ]),

        Chapter("Act 5 - India", [
            Beat("Four months later, on the eighteenth of August, twenty twenty three, he "
                 "made his India debut, in a T20 against Ireland.", "cricket match", "stock"),
            Beat("That December, he played his first one day international, against South "
                 "Africa.", "cricket stadium crowd", "stock"),
            Beat("With Rohit Sharma, he later put on a partnership of one hundred and "
                 "ninety.", "cricket batsman batting", "stock"),
            Beat("It is India's highest ever partnership in T20 internationals.",
                 "stadium floodlights night", "stock"),
            Beat("He was part of the squad that won gold at the twenty twenty two Asian "
                 "Games, although he did not get a game.", "trophy celebration", "stock"),
            Beat("He won the Asia Cup in twenty twenty five.", "trophy celebration", "stock"),
            Beat("And Kolkata, the team that once paid eighty lakh for him, retained him for "
                 "thirteen crore.", "indian rupee notes", "stock"),
            Beat("From eighty lakh, to thirteen crore.", "counting money", "stock"),
            Beat("He bought his family a new home in Aligarh.", "indian family home", "stock"),
            Beat("Harbhajan Singh has told the story of Rinku gifting his father a bike.",
                 "man riding motorcycle india", "stock"),
            Beat("But here is the detail that says the most about that family.",
                 "window light room", "stock"),
            Beat("A video went viral showing his father still delivering gas cylinders.",
                 "delivery man carrying load", "stock"),
            Beat("The son was a star. The father kept doing the job that had carried the "
                 "family.", "gas cylinder delivery", "stock"),
        ]),

        Chapter("Act 6 - The World Cup", [
            Beat("Which brings us to twenty twenty six.", "sunset silhouette", "stock"),
            Beat("India were at the T20 World Cup, and Rinku was in the squad.",
                 "cricket stadium crowd night", "stock"),
            Beat("Back home, his father was fighting stage four liver cancer.",
                 "hospital corridor", "stock"),
            Beat("During the Super Eight stage, Rinku was left out of the playing eleven "
                 "against Zimbabwe.", "cricket match", "stock"),
            Beat("He still went onto the field, as a substitute fielder.",
                 "cricket bowler bowling", "stock"),
            Beat("After that match, he left the team camp and travelled home to Aligarh.",
                 "empty road evening", "stock"),
            Beat("On the twenty seventh of February, twenty twenty six, Khanchand Singh "
                 "died.", "candle memorial", "stock"),
            Beat("The man who carried gas cylinders so his son could keep playing did not "
                 "see the end of that tournament.", "man sitting alone sad", "stock"),
            Beat("India went on to win it.", "trophy celebration", "stock"),
            Beat("Rinku Singh is a T20 World Cup champion.", "fireworks stadium", "stock"),
        ]),

        Chapter("Close - Hours nobody filmed", [
            Beat("It is tempting to tell this as a simple story. Poor boy, big sixes, happy "
                 "ending.", "cricket batsman hitting six", "stock"),
            Beat("It is not that simple.", "window light room", "stock"),
            Beat("It is a story about a family that spent years betting on something that "
                 "almost never pays off.", "indian family home", "stock"),
            Beat("A father carrying cylinders.", "lpg gas cylinder", "stock"),
            Beat("A brother driving an auto.", "auto rickshaw india", "stock"),
            Beat("A teenager saving his match allowance to pay back a debt.",
                 "counting money", "stock"),
            Beat("And a job mopping floors that could easily have been the rest of his "
                 "life.", "mopping floor", "stock"),
            Beat("Every one of those five sixes was built on hours nobody filmed.",
                 "cricket practice nets", "stock"),
            Beat("So the next time you watch a young player hit the ball out of the ground, "
                 "it is worth asking what it took to get them there.",
                 "cricket batsman hitting six", "stock"),
            Beat("Because for a lot of them, the real story is not the six.",
                 "sunset silhouette", "stock"),
            Beat("It is everything that happened before anyone was watching.",
                 "empty road evening", "stock"),
            Beat("If this one meant something to you, subscribe. Every week, we tell the "
                 "story behind the highlights.", "cricket stadium crowd night", "stock"),
        ]),
    ],
)


def build():
    import json
    import os
    import longform_creator as lf
    from logger import log

    missing = lf.unmatched_beats(SCRIPT)
    if missing:
        raise RuntimeError(f"beats with no visual bucket (would render off-topic): {missing}")

    pool_file = os.path.join(config.OUTPUT_DIR, "rinku_bucket_pool.json")
    pool = None
    if os.path.exists(pool_file):
        pool = json.load(open(pool_file))
        if not all(os.path.exists(p) for v in pool.values() for p in v):
            pool = None
    if pool is None:
        log("Sourcing per-SUBJECT footage via visual_buckets...")
        pool = lf.source_buckets(SCRIPT)
        json.dump(pool, open(pool_file, "w"), indent=1)
    beat_clips = lf.assign_visuals(SCRIPT, pool)
    alternates = lf.beat_alternates(SCRIPT, pool)
    log(f"{len(beat_clips)} beats from {len(set(beat_clips))} distinct clips")

    vo_file = os.path.join(config.OUTPUT_DIR, "rinku_vo_path.txt")
    vo_path = open(vo_file).read().strip() if os.path.exists(vo_file) else ""
    if not (vo_path and os.path.exists(vo_path)):
        log("Generating long voiceover...")
        vo_path = lf.generate_long_voiceover(SCRIPT)
        open(vo_file, "w").write(vo_path)
    print("VO_PATH=" + vo_path, flush=True)

    music = None
    try:
        import pro_shorts_creator as psc
        from moviepy import AudioFileClip
        music = psc.get_music(duration=AudioFileClip(vo_path).duration,
                              script={"hook": SCRIPT.title, "body": SCRIPT.description, "cta": ""})
    except Exception as e:
        log(f"music skipped ({e})")

    out = os.path.join(config.VIDEOS_DIR, "doc_rinku.mp4")
    lf.render(SCRIPT, beat_clips, vo_path, music, out, alternates=alternates)
    log(f"DONE -> {out}")
    return out, vo_path


if __name__ == "__main__":
    import sys
    if "--build" in sys.argv:
        build()
    else:
        import longform_creator as lf
        print(SCRIPT.report())
        iss = SCRIPT.validate()
        print("\nValidation:", "PASSED" if not iss else "ISSUES")
        for i in iss:
            print("  -", i)
        print("unmatched visual beats:", lf.unmatched_beats(SCRIPT))
        build_narration_file(SCRIPT)
