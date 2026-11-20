"""
doc_asiacup.py — documentary #5 (2026-09-18).
"India Won the Asia Cup Twice. Both Times, They Refused the Trophy"

WHY THIS TOPIC -- from YouTube's own Trending chart, not search guesses:
Owner, 2026-09-18: "you didnt check the trending what you make taking low
views videos". Measured: cricket-over Short 42 views, boxing Short 197,
Garrincha doc 73, Moses doc 87 -- evergreen facts do not travel even when
cricket is hot. videos().list(chart="mostPopular", videoCategoryId="17",
regionCode="IN") on 2026-09-18 (saved: output/trending_sports_IN_2026-09-18.json)
showed the India Women trophy refusal covered by ABP Ananda, News18 Odia,
BBC News Hindi, TV9 Telugu and Republic Bharat at once -- many channels on
one story is live demand. The story also has a documented year-long back
story (the 2025 men's final), which a news clip cannot tell but a
documentary can.

TONE: India-Pakistan cricket is political. Every claim is sourced, both
boards' positions are stated, and sanctions on BOTH sides are reported.
The script does not say who was right.

VERIFIED (2026-09-18):
  Wikipedia "2025 Asia Cup":
  - India were to host; after the Pahalgam attack and the India-Pakistan
    conflict in 2025, ACC chairman Mohsin Naqvi announced in July 2025 the
    event would be held in the UAE as a neutral venue. 9-28 Sept 2025,
    Dubai and Abu Dhabi.
  - India beat Pakistan three times: 14 Sept by 7 wkts; 21 Sept by 6 wkts;
    final 28 Sept by 5 wkts (Pakistan 146; India 150/5 in 19.4 overs).
  - Captains did not shake hands at the toss, reportedly on the advice of
    match referee Andy Pycroft; India left without handshakes. Pakistan
    coach Mike Hesson expressed disappointment. PCB protested against
    Pycroft and demanded his removal; ICC rejected it. Pakistan v UAE was
    delayed an hour. PCB later said Pycroft apologised for "the
    miscommunication"; he continued.
  - Final: Sahibzada Farhan 57 off 38; Kuldeep Yadav 4/30; Tilak Varma 69*
    off 53, Player of the Match. Player of the series Abhishek Sharma
    (314 runs); Kuldeep 17 wickets. India's 9th title.
  - Article 2.21 sanctions: Haris Rauf (gestures) fined 30% + demerit
    points, then a 2-match ban; Sahibzada Farhan (bat "rifle" celebration)
    warning; Suryakumar Yadav (dedicated the win to the Indian Army; PCB
    called it political) fined 30%.
  Forbes / Gulf News / NBC / All India Radio (Sept 2025):
  - Presentation delayed more than an hour; Naqvi (ACC president, PCB
    chairman, Pakistan's Interior Minister) insisted on presenting; India
    were prepared to receive it from Emirates Cricket Board vice-chairman
    Khalid Al Zarooni; officials removed the trophy; India celebrated with
    an invisible trophy, Suryakumar lifting it.
  - BCCI secretary Devajit Saikia condemned it and said a formal protest
    would be lodged at the ICC conference in November.
  Tribune India: Naqvi said India were welcome to collect the trophy from
    him at the ACC office.
  Al Jazeera / ESPNcricinfo (13 Sept 2026): Women's final, Dubai. India
    183/5, Sri Lanka 111, India won by 72 runs; 8th title. Shafali Verma
    68 off 39 and 1/23, Player of the Match; 129 opening stand with Smriti
    Mandhana, highest for any wicket in the Women's T20 Asia Cup.
  The National / Dawn (14 Sept 2026): India refused to collect the trophy
    from Naqvi; presentation delayed; Indian players did not come out;
    Sri Lanka captain Chamari Athapaththu collected the runners-up cheque
    alone; coach Amol Muzumdar: the "stand has been taken by the BCCI...
    and we stand by it".
  Yahoo Sports: Rajeev Shukla said Naqvi "didn't object" to India refusing.
  Search summary (Sept 2026): reports say the 2025 men's trophy is still
    uncollected; Saikia confirmed an informal meeting with Naqvi.

NOT CLAIMED: no exact Pahalgam date (Wikipedia says "early 2025"), no
statement of who was right, no claim the 2025 trophy will never be handed
over -- only that reports say it has not been yet.
"""
import config
from longform_creator import DocScript, Chapter, Beat, build_narration_file

SCRIPT = DocScript(
    title="India Won the Asia Cup Twice. Both Times, They Refused the Trophy 🏆",
    hook_card="THEY WON. THEY WOULDN'T TOUCH IT.",
    description=(
        "In September 2025, India beat Pakistan in the Asia Cup final and celebrated "
        "with an invisible trophy, after refusing to take the real one from ACC "
        "president Mohsin Naqvi -- who is also Pakistan's cricket board chairman and "
        "Interior Minister. A year later, India's women won the Asia Cup and did the "
        "same thing. This is the full story: the handshake row, the fines on both "
        "sides, the hour-long standoff, and a trophy that reports say India still "
        "have not collected."
    ),
    tags=["asia cup", "asia cup trophy", "mohsin naqvi", "india vs pakistan",
          "suryakumar yadav", "invisible trophy", "women's asia cup", "shafali verma",
          "smriti mandhana", "bcci", "cricket controversy", "cricket documentary"],
    # Every crowd/celebration/stadium query names CRICKET. The first render
    # used sport-less terms and got football players, an American-football
    # stadium and Turkish club flags; the women's beats got male batsmen
    # (free stock has almost no women's cricket, so those beats use wide
    # shots where no one is identifiable).
    visual_buckets={
        "trophy":    {"match": ["trophy", "silverware"],
                      "queries": ["gold trophy close up", "trophy on stage", "cup trophy shining"], "n": 4},
        "ceremony":  {"match": ["ceremony", "stage", "podium", "presentation"],
                      "queries": ["award ceremony stage", "podium presentation", "stage lights ceremony"], "n": 4},
        "handshake": {"match": ["handshake", "hands"],
                      "queries": ["handshake close up", "business handshake", "two men shaking hands"], "n": 3},
        "officials": {"match": ["officials", "meeting", "suits", "boardroom", "press"],
                      "queries": ["business meeting table", "men in suits meeting", "press conference microphones"], "n": 4},
        "dubai":     {"match": ["dubai", "skyline", "desert", "uae"],
                      "queries": ["dubai skyline night", "dubai city aerial", "desert road uae"], "n": 3},
        "women":     {"match": ["women", "female"],
                      "queries": ["women cricket", "girls playing cricket", "cricket ground aerial"], "n": 4},
        "celebrate": {"match": ["celebrat", "cheer", "fireworks"],
                      "queries": ["cricket team celebration", "cricket players celebrating", "confetti celebration"], "n": 4},
        "crowd":     {"match": ["crowd", "fans", "flag"],
                      "queries": ["cricket stadium crowd", "cricket fans cheering", "indian cricket fans"], "n": 5},
        "stadium":   {"match": ["stadium", "floodlights", "night match"],
                      "queries": ["cricket stadium", "cricket ground aerial", "cricket stadium night"], "n": 5},
        "news":      {"match": ["newspaper", "headline", "phone", "screen", "television"],
                      "queries": ["reading news on phone", "newspaper headlines", "television news screen"], "n": 3},
        "mood":      {"match": ["clock", "silhouette", "empty", "window", "sunset"],
                      "queries": ["clock ticking", "silhouette sunset", "empty room window light"], "n": 3},
        "cricket":   {"match": ["cricket", "batsman", "bowler", "wicket"],
                      "queries": ["cricket batsman batting", "cricket bowler bowling", "cricket match action",
                                  "cricket wicket stumps"], "n": 8},
    },
    sources=[
        "2025 Asia Cup -- Wikipedia",
        "Asia Cup 2025: India refuses to receive trophy from Pakistan's Mohsin Naqvi -- Forbes",
        "Who is Mohsin Naqvi, the Asia Cup chief India snubbed for trophy? -- Gulf News",
        "Why was the Asia Cup presentation ceremony delayed? -- Gulf News",
        "BCCI condemns controversial trophy incident at Asia Cup 2025 final -- All India Radio",
        "Mohsin Naqvi rejects apology claims, offers India to collect Asia Cup trophy at ACC office -- Tribune India",
        "India defeat Sri Lanka by 72 runs: Women's Asia Cup final -- Al Jazeera",
        "Shafali, Mandhana power India to eighth Asia Cup title -- ESPNcricinfo",
        "India refuse to accept Women's Asia Cup trophy from Mohsin Naqvi -- The National",
        "Winners India refuse to collect Women's Asia Cup trophy from ACC chief Mohsin Naqvi -- Dawn",
        "Mohsin Naqvi 'didn't object' to India refusing Women's Asia Cup trophy, says Rajeev Shukla -- Yahoo Sports",
    ],
    chapters=[
        Chapter("Cold Open", [
            Beat("The twenty eighth of September, twenty twenty five. Dubai.",
                 "cricket stadium floodlights night", "stock"),
            Beat("India have just beaten Pakistan to win the Asia Cup final.",
                 "cricket fans stadium crowd", "stock"),
            Beat("The captain, Suryakumar Yadav, raises the trophy above his head, and "
                 "the team goes wild.", "team celebration", "stock"),
            Beat("Except there is no trophy.", "empty stadium seats", "stock"),
            Beat("His hands are empty. He is lifting nothing at all.", "clock ticking", "stock"),
            Beat("The real trophy had been carried away, after India refused to take it "
                 "from the man who was supposed to hand it over.", "trophy on stage", "stock"),
            Beat("Almost a year later, in the same stadium, it happened again.",
                 "stadium aerial night", "stock"),
            Beat("India's women won the Asia Cup, and they would not touch the trophy "
                 "either.", "women team celebration", "stock"),
            Beat("Two Indian teams. Two titles. Two empty stages.", "award ceremony stage", "stock"),
            Beat("Subscribe before this one, because the story behind those empty hands "
                 "is bigger than one presentation.", "cricket fans stadium crowd", "stock"),
            Beat("To understand it, you have to start with one man, and three jobs.",
                 "silhouette sunset", "stock"),
        ]),

        Chapter("Act 1 - One man, three jobs", [
            Beat("His name is Mohsin Naqvi.", "press conference microphones", "stock"),
            Beat("He is the president of the Asian Cricket Council, the body that runs the "
                 "Asia Cup.", "men in suits meeting", "stock"),
            Beat("He is the chairman of the Pakistan Cricket Board.", "business meeting table", "stock"),
            Beat("And he is Pakistan's Minister of the Interior.", "press conference microphones", "stock"),
            Beat("Keep those three roles in mind. Everything that follows comes back to "
                 "them.", "empty room window light", "stock"),
            Beat("And as president of the Asian Cricket Council, it was his role to "
                 "present the Asia Cup trophy.", "trophy on stage", "stock"),
            Beat("So whoever won in twenty twenty five was always going to be handed the "
                 "cup by a serving Pakistani government minister.", "gold trophy close up", "stock"),
            Beat("And the tournament almost did not happen where it was supposed to.",
                 "empty room window light", "stock"),
            Beat("India were meant to host it.", "cricket stadium floodlights night", "stock"),
            Beat("But in twenty twenty five, after the Pahalgam attack, and the conflict "
                 "between India and Pakistan that followed, that became impossible to "
                 "arrange.", "television news screen", "stock"),
            Beat("In July, Naqvi announced the Asia Cup would move to the United Arab "
                 "Emirates, as a neutral venue.", "dubai skyline night", "stock"),
            Beat("Dubai and Abu Dhabi. The ninth to the twenty eighth of September.",
                 "dubai city aerial", "stock"),
            Beat("And India and Pakistan were drawn to meet.", "stadium crowd night", "stock"),
        ]),

        Chapter("Act 2 - No handshakes", [
            Beat("The fourteenth of September. The group stage.", "cricket stadium floodlights night", "stock"),
            Beat("At the toss, the two captains did not shake hands.", "handshake close up", "stock"),
            Beat("Reports said it was on the advice of the match referee, Andy Pycroft.",
                 "men in suits meeting", "stock"),
            Beat("India won by seven wickets, and left the field without shaking hands "
                 "with the Pakistan players.", "cricket batsman batting", "stock"),
            Beat("Pakistan had made one hundred and twenty seven. India knocked the runs "
                 "off for the loss of three wickets.", "cricket match action", "stock"),
            Beat("Pakistan's head coach, Mike Hesson, said he was disappointed.",
                 "press conference microphones", "stock"),
            Beat("The Pakistan Cricket Board lodged a formal protest against the referee, "
                 "and demanded he be removed from the tournament.", "business meeting table", "stock"),
            Beat("It also suspended its own director of operations, Usman Wahla.",
                 "business meeting table", "stock"),
            Beat("The ICC said no.", "clock ticking", "stock"),
            Beat("Pakistan's next match, against the UAE, started an hour late while it "
                 "was sorted out.", "empty stadium seats", "stock"),
            Beat("The PCB later said Pycroft had apologised for what it called a "
                 "miscommunication. He stayed on.", "reading news on phone", "stock"),
            Beat("One week later they met again, in the Super Four.", "stadium aerial night", "stock"),
            Beat("Pakistan made one hundred and seventy one. India chased it down, and won "
                 "by six wickets. Again, no handshakes.", "cricket bowler bowling", "stock"),
            Beat("And by now, the gestures were getting sharper, on both sides.",
                 "stadium crowd night", "stock"),
            Beat("Pakistan fast bowler Haris Rauf made gestures the ICC found brought the "
                 "game into disrepute.", "cricket bowler bowling", "stock"),
            Beat("Sahibzada Farhan celebrated a fifty by pointing his bat like a rifle. He "
                 "was given an official warning.", "cricket match action", "stock"),
            Beat("And Suryakumar Yadav, after India's win, dedicated it to the Indian Army.",
                 "cricket fans stadium crowd", "stock"),
            Beat("The PCB called that a political statement. He was fined thirty percent "
                 "of his match fee.", "newspaper headlines", "stock"),
            Beat("Three players. Two countries. All three found guilty of the same offence.",
                 "press conference microphones", "stock"),
        ]),

        Chapter("Act 3 - The final", [
            Beat("And then, the twenty eighth of September. The final. India against "
                 "Pakistan, for the third time.", "stadium aerial night", "stock"),
            Beat("Sahibzada Farhan hit fifty seven off thirty eight balls.",
                 "cricket batsman batting", "stock"),
            Beat("But Kuldeep Yadav took four wickets for thirty, and Pakistan were all "
                 "out for one hundred and forty six.", "cricket wicket stumps", "stock"),
            Beat("India got there with two balls to spare.", "cricket match action", "stock"),
            Beat("Tilak Varma, sixty nine not out, player of the match.",
                 "cricket batsman batting", "stock"),
            Beat("Abhishek Sharma was player of the tournament, with three hundred and "
                 "fourteen runs.", "fans cheering", "stock"),
            Beat("Kuldeep finished with seventeen wickets, more than anyone else in the "
                 "Asia Cup.", "cricket wicket stumps", "stock"),
            Beat("Three matches against Pakistan. Three wins. India's ninth Asia Cup.",
                 "team celebration", "stock"),
            Beat("Then came the presentation.", "award ceremony stage", "stock"),
            Beat("Naqvi, as president of the Asian Cricket Council, was there to hand "
                 "over the trophy.", "podium presentation", "stock"),
            Beat("India would not take it from him.", "empty stadium seats", "stock"),
            Beat("Reports say India were prepared to receive it from a different official, "
                 "Khalid Al Zarooni, the vice chairman of the Emirates Cricket Board.",
                 "men in suits meeting", "stock"),
            Beat("Naqvi insisted on presenting it himself.", "press conference microphones", "stock"),
            Beat("The ceremony was delayed for more than an hour.", "clock ticking", "stock"),
            Beat("In the end, officials took the trophy away.", "trophy on stage", "stock"),
            Beat("And India celebrated with nothing. Suryakumar lifted an invisible "
                 "trophy, and the team cheered as if it were real.", "team celebration", "stock"),
            Beat("A championship celebration, without the one thing every final is played "
                 "for.", "reading news on phone", "stock"),
        ]),

        Chapter("Act 4 - The fallout", [
            Beat("The BCCI's secretary, Devajit Saikia, condemned what happened, and said "
                 "India would lodge a formal protest at the ICC's conference in November.",
                 "business meeting table", "stock"),
            Beat("Naqvi's answer was simple. India were welcome to collect the trophy from "
                 "him, at the Asian Cricket Council's office.", "press conference microphones", "stock"),
            Beat("India did not go.", "empty room window light", "stock"),
            Beat("Haris Rauf picked up more demerit points in the final, which added up "
                 "to a two match ban.", "cricket bowler bowling", "stock"),
            Beat("It ruled him out of Pakistan's one day internationals against South "
                 "Africa that November.", "newspaper headlines", "stock"),
            Beat("And the trophy itself stayed where it was.", "gold trophy close up", "stock"),
            Beat("Think about how unusual that is.", "clock ticking", "stock"),
            Beat("A team wins a continental title on the field, beats its biggest rival "
                 "three times in a fortnight, and never actually holds the cup.",
                 "empty stadium seats", "stock"),
            Beat("It could have stayed a one off. A single, heated night in Dubai.",
                 "dubai skyline night", "stock"),
            Beat("It was not.", "silhouette sunset", "stock"),
        ]),

        Chapter("Act 5 - The women's final", [
            Beat("The thirteenth of September, twenty twenty six. Same city, same stadium.",
                 "dubai city aerial", "stock"),
            Beat("The Women's Asia Cup final. India against Sri Lanka.",
                 "women cricket match", "stock"),
            Beat("Shafali Verma and Smriti Mandhana walked out to open, and put on one "
                 "hundred and twenty nine together.", "female cricketer batting", "stock"),
            Beat("The highest partnership for any wicket in the history of the Women's T20 "
                 "Asia Cup.", "women cricket match", "stock"),
            Beat("Shafali made sixty eight off thirty nine balls, then took a wicket as "
                 "well. Player of the match.", "female cricketer batting", "stock"),
            Beat("India made one hundred and eighty three. Sri Lanka were bowled out for "
                 "one hundred and eleven.", "cricket wicket stumps", "stock"),
            Beat("India won by seventy two runs. Their eighth Asia Cup title.",
                 "women team celebration", "stock"),
            Beat("And the man due to present the trophy was, once again, Mohsin Naqvi.",
                 "podium presentation", "stock"),
            Beat("The presentation was delayed. The Indian players did not come out to the "
                 "stage.", "award ceremony stage", "stock"),
            Beat("Naqvi stood with the Asian Cricket Council officials, waiting.",
                 "men in suits meeting", "stock"),
            Beat("Sri Lanka's captain, Chamari Athapaththu, went up and collected the "
                 "runners up cheque on her own.", "stage lights ceremony", "stock"),
            Beat("And the ceremony was brought to a quick close.", "empty stadium seats", "stock"),
            Beat("It was the second year in a row that an Indian team had skipped the Asia "
                 "Cup trophy presentation.", "television news screen", "stock"),
            Beat("India's head coach, Amol Muzumdar, kept it short. The stand, he said, "
                 "has been taken by the BCCI, and we stand by it.", "press conference microphones", "stock"),
            Beat("Rajeev Shukla later said Naqvi did not object.",
                 "reading news on phone", "stock"),
        ]),

        Chapter("Close - The cup nobody lifted", [
            Beat("One trophy, two refusals, and a year of stalemate.", "clock ticking", "stock"),
            Beat("So where does that leave the trophy?", "gold trophy close up", "stock"),
            Beat("According to reports, the men's Asia Cup from twenty twenty five has still "
                 "not been handed over to India.", "trophy on stage", "stock"),
            Beat("The BCCI has confirmed an informal meeting with Naqvi about it.",
                 "business meeting table", "stock"),
            Beat("But for now, one of cricket's major titles has a winner, and no one "
                 "holding the cup.", "empty room window light", "stock"),
            Beat("Depending on who you ask, this is a principled stand.",
                 "cricket fans stadium crowd", "stock"),
            Beat("Or it is cricket being pulled into politics it cannot fix.",
                 "television news screen", "stock"),
            Beat("Two different teams, a year apart, made exactly the same choice.",
                 "silhouette sunset", "stock"),
            Beat("What is not in dispute is the scoreboard.", "cricket match action", "stock"),
            Beat("India's men beat Pakistan three times. India's women won by seventy two "
                 "runs.", "team celebration", "stock"),
            Beat("They earned those titles on the field. The only thing missing is the "
                 "silverware.", "gold trophy close up", "stock"),
            Beat("So tell me in the comments. Was India right to refuse the trophy?",
                 "fans cheering", "stock"),
            Beat("And if you want the full story behind the headlines, subscribe. We do "
                 "this every week.", "cricket stadium floodlights night", "stock"),
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

    pool_file = os.path.join(config.OUTPUT_DIR, "asiacup_bucket_pool.json")
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

    vo_file = os.path.join(config.OUTPUT_DIR, "asiacup_vo_path.txt")
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

    out = os.path.join(config.VIDEOS_DIR, "doc_asiacup.mp4")
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
