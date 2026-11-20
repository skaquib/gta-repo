"""
doc_athletes_broke.py — first long-form documentary.
"The Most Repeated Lie in Sports"

THE PIVOT THAT MADE THIS WORTH MAKING:
The obvious video is "78% of NFL players go broke." Verification killed it
2026-09-08 -- that statistic is disputed and effectively wrong. Which is a
far better documentary, because every other channel just repeats it.

VERIFIED CHAIN:
- Sports Illustrated, March 2009, writer Pablo S. Torre: 78% of NFL players
  are "bankrupt or under financial stress" within two years of retirement.
  Torre later acknowledged he did not conduct the study himself and that the
  figure was vetted via NFL / NFLPA sources.
- Carlson, Kim, Lusardi & Camerer, "Bankruptcy Rates among NFL Players with
  Short-Lived Income Spikes" (NBER w21085; American Economic Review, May
  2015). Sample: every player drafted by an NFL team 1996-2003.
    * ~1.9% had filed for bankruptcy within 2 years of retirement
    * ~16% -- close to 1 in 6 -- had filed by year 12
    * bankruptcy begins soon after retirement and continues at a substantial
      rate through at least 12 years
    * total career earnings and career length had surprisingly little effect
      on bankruptcy risk  <-- the emotional core
- ESPN 30 for 30 "Broke" (2012) documented mechanisms: bad investments,
  freeloading entourages, medical costs, divorce, and lifestyle pressure.

The honest through-line: the famous number is false, the real number is
smaller but slower and stranger, and earning more money did not protect
players. That is the story nobody else tells.

Per standing process: builds/writes only. Nothing uploads from this file.
"""
import config
from longform_creator import DocScript, Chapter, Beat, build_narration_file

SCRIPT = DocScript(
    title="The Most Repeated Lie in Sports",
    hook_card="78% IS A LIE",
    description=(
        "Everyone repeats the same statistic: 78% of NFL players go broke within "
        "two years of retiring. It isn't true. The peer-reviewed number is about "
        "1.9%. But the real research found something stranger -- and worse. "
        "Sources: Sports Illustrated (2009); Carlson, Kim, Lusardi & Camerer, "
        "'Bankruptcy Rates among NFL Players with Short-Lived Income Spikes,' "
        "NBER w21085 / American Economic Review (2015); ESPN 30 for 30 'Broke' (2012)."
    ),
    tags=["nfl", "sports business", "athlete finances", "documentary",
          "sports money", "bankruptcy", "personal finance", "sports facts"],
    sources=[
        "Pablo S. Torre, 'How (and Why) Athletes Go Broke,' Sports Illustrated, March 2009",
        "Carlson, Kim, Lusardi & Camerer, 'Bankruptcy Rates among NFL Players with Short-Lived Income Spikes,' NBER Working Paper 21085 / American Economic Review 105(5), May 2015",
        "ESPN Films, 30 for 30: 'Broke,' 2012",
        "FiveThirtyEight, 'There's A Difference Between Broke And Bankrupt For Ex-NFL Players'",
    ],
    chapters=[
        Chapter("Cold Open", [
            Beat("Seventy-eight percent.",
                 "american football stadium empty night", "stock"),
            Beat("That is the number everyone repeats. Seventy-eight percent of NFL "
                 "players go broke within two years of retiring.",
                 "american football players field", "stock"),
            Beat("You have heard it in documentaries. In podcasts. In financial "
                 "advice columns and locker room speeches.",
                 "podcast microphone studio", "stock"),
            Beat("There is only one problem with it. It isn't true.",
                 "newspaper print close up", "stock"),
            Beat("And the real number, the one almost nobody quotes, tells a much "
                 "stranger story.",
                 "american football helmet close up", "stock"),
        ]),

        Chapter("Act 1 — The Number That Ate Sports Media", [
            Beat("In March 2009, Sports Illustrated published an article by a writer "
                 "named Pablo Torre.",
                 "magazine pages flipping", "stock"),
            Beat("The headline finding was brutal. Within two years of retirement, "
                 "seventy-eight percent of former NFL players were bankrupt, or under "
                 "financial stress.",
                 "empty american football field goal posts", "stock"),
            Beat("Think about what that claim actually says. Take any ten men who "
                 "walked off an NFL field for the last time.",
                 "american football players walking off field", "stock"),
            Beat("Within twenty-four months, almost eight of them are financially "
                 "underwater.",
                 "money cash counting", "stock"),
            Beat("It was the perfect statistic. Shocking, simple, and it confirmed "
                 "something people already believed about young men and sudden money.",
                 "young man counting money", "stock"),
            Beat("So it spread. Everywhere.",
                 "television screens broadcast", "stock"),
            Beat("It became the opening line of financial literacy programs. It was "
                 "quoted by agents, by advisors, by players themselves.",
                 "business meeting documents desk", "stock"),
            Beat("It appeared in books, in college lectures, in rookie orientation "
                 "sessions designed to frighten twenty-two year olds into saving.",
                 "lecture hall seats", "stock"),
            Beat("And it kept working, because it felt true. Everyone can name an "
                 "athlete who lost everything.",
                 "stadium floodlights night", "stock"),
            Beat("That is what makes a statistic dangerous. Not that it is false, but "
                 "that it agrees with you.",
                 "library archive shelves", "stock"),
            Beat("For years, almost nobody checked it at all.",
                 "dusty archive documents", "stock"),
        ]),

        Chapter("Act 2 — What the Researchers Actually Found", [
            Beat("Then, in 2015, four researchers decided to count properly.",
                 "university research library", "stock"),
            Beat("Kyle Carlson, Joshua Kim, Annamaria Lusardi and Colin Camerer "
                 "published their work through the National Bureau of Economic "
                 "Research, and in the American Economic Review.",
                 "academic paper documents", "stock"),
            Beat("They did not survey opinions. They pulled the records of every "
                 "single player drafted by an NFL team between 1996 and 2003, and "
                 "checked who had actually filed for bankruptcy.",
                 "filing cabinet records", "stock"),
            Beat("Two years after retirement, the share of players who had filed for "
                 "bankruptcy was not seventy-eight percent.",
                 "american football stadium seats empty", "stock"),
            Beat("It was about one point nine percent.",
                 "calculator numbers close up", "stock"),
            Beat("Not seventy-eight. Under two.",
                 "chart graph declining", "stock"),
            Beat("The most repeated financial statistic in sports was off by a factor "
                 "of roughly forty.",
                 "newspaper headlines archive", "stock"),
            Beat("Torre, to his credit, has been open about the limits of his number.",
                 "journalist writing notebook", "stock"),
            Beat("He has said he did not conduct the study himself, and that the "
                 "figure came vetted through league and players' association sources.",
                 "office interview desk", "stock"),
            Beat("So how do you get from under two percent to seventy-eight?",
                 "question mark chalkboard", "stock"),
            Beat("The gap comes down to a single word.",
                 "dictionary page close up", "stock"),
            Beat("Bankrupt is a legal filing. It is a court record with a date on it. "
                 "You can count it.",
                 "courthouse building exterior", "stock"),
            Beat("Financial stress is not. It has no definition, no filing, no "
                 "threshold.",
                 "man worried paperwork", "stock"),
            Beat("A player who lost money in a bad restaurant deal is under financial "
                 "stress. So is a player going through a divorce. So is a player who "
                 "simply worries about money.",
                 "restaurant closed sign", "stock"),
            Beat("Those are real problems. They are not bankruptcies. And once you "
                 "blend them together, the number can be almost anything you want it "
                 "to be.",
                 "blurred crowd people", "stock"),
        ]),

        Chapter("Act 3 — The Truth Is Slower, and Worse", [
            Beat("Here is where most corrections would stop. Myth busted, athletes "
                 "are fine, move on.",
                 "american football game action", "stock"),
            Beat("But that is not what the researchers found.",
                 "research data screen", "stock"),
            Beat("Because bankruptcies did not stop after those first two years. They "
                 "kept coming.",
                 "clock time passing", "stock"),
            Beat("Steadily. Year after year. Through at least twelve years of "
                 "retirement.",
                 "calendar pages", "stock"),
            Beat("By year twelve, nearly sixteen percent of those players had filed "
                 "for bankruptcy. Close to one in six.",
                 "american football stadium crowd", "stock"),
            Beat("The crisis was real. It was just slower than anyone said.",
                 "empty locker room", "stock"),
            Beat("And then the finding that should genuinely disturb you.",
                 "dark stadium tunnel", "stock"),
            Beat("The researchers checked whether earning more money protected "
                 "players. Whether a longer career protected them.",
                 "money stacks close up", "stock"),
            Beat("It barely did.",
                 "chart flat line graph", "stock"),
            Beat("Total career earnings and career length had surprisingly little "
                 "effect on whether a player went bankrupt.",
                 "american football player silhouette", "stock"),
            Beat("The men who made the most were not meaningfully safer than the men "
                 "who made the least.",
                 "luxury car keys", "stock"),
            Beat("Read that again, because it breaks the entire common sense "
                 "explanation.",
                 "american football stadium empty seats", "stock"),
            Beat("If going broke were simply about reckless spending, then the players "
                 "with the biggest contracts and the longest careers should have the "
                 "deepest cushion.",
                 "bank vault door", "stock"),
            Beat("More money, more margin for error. That is how it is supposed to "
                 "work.",
                 "stack of coins rising", "stock"),
            Beat("It did not work that way. Which means the problem is not really "
                 "about the size of the paycheck at all.",
                 "empty american football field", "stock"),
        ]),

        Chapter("Act 4 — Why More Money Doesn't Save You", [
            Beat("Standard economics says this should not happen.",
                 "economics textbook", "stock"),
            Beat("The life cycle theory says people save during high income years to "
                 "cover the low income years that follow. Earn a lot young, spread it "
                 "out, be fine.",
                 "piggy bank savings", "stock"),
            Beat("NFL careers are the cleanest test of that theory that exists. A "
                 "massive income spike, lasting a few years, followed by decades of "
                 "nothing like it.",
                 "graph spike chart", "stock"),
            Beat("And the theory failed.",
                 "broken glass", "stock"),
            Beat("ESPN's documentary Broke, released in 2012, spent ninety minutes on "
                 "the mechanisms.",
                 "film documentary camera", "stock"),
            Beat("Bad investments sold by people who knew exactly how little financial "
                 "training these men had.",
                 "business handshake contract", "stock"),
            Beat("Entourages. Friends, relatives, and hangers-on whose income was the "
                 "player's income.",
                 "group of people crowd", "stock"),
            Beat("Divorce. Medical costs from a body that was used as equipment for a "
                 "decade.",
                 "hospital corridor", "stock"),
            Beat("And lifestyle. Not yachts, usually. Just a standard of living built "
                 "for a salary that stops arriving in your early thirties.",
                 "large house exterior", "stock"),
            Beat("A house sized for the contract. A family supported at that level. "
                 "Commitments that were reasonable at twenty-six and impossible at "
                 "thirty-four.",
                 "suburban house driveway", "stock"),
            Beat("None of that is fixed by a bigger contract.",
                 "contract signing pen", "stock"),
            Beat("A bigger contract often makes every single one of those pressures "
                 "larger.",
                 "money falling", "stock"),
            Beat("More money attracts more advisors, more relatives, more "
                 "opportunities that are really just someone else's risk wearing a "
                 "suit.",
                 "businessman suit briefcase", "stock"),
            Beat("And it raises the floor of the life you now have to keep paying for, "
                 "long after the income has stopped.",
                 "empty luxury living room", "stock"),
            Beat("That is why earnings did not protect them. The money scaled. The "
                 "problems scaled with it.",
                 "balance scales", "stock"),
        ]),

        Chapter("Close", [
            Beat("So the famous number is wrong. Seventy-eight percent was never real.",
                 "newspaper crumpled", "stock"),
            Beat("But the story underneath it survived the fact check, and it is more "
                 "uncomfortable than the myth.",
                 "american football field sunset", "stock"),
            Beat("Roughly one in six. Spread across twelve years. Largely indifferent "
                 "to how much they earned.",
                 "empty stadium wide", "stock"),
            Beat("The myth said athletes are reckless, and that it happens fast.",
                 "sports car night city", "stock"),
            Beat("The research says something quieter, and much harder to fix.",
                 "quiet empty hallway", "stock"),
            Beat("That a short career and a long life is a genuinely difficult "
                 "financial problem. That the danger arrives slowly, years after "
                 "anyone is still paying attention.",
                 "man walking away stadium", "stock"),
            Beat("And that money, by itself, does not solve it.",
                 "empty wallet", "stock"),
            Beat("Which is a harder lesson than the lie. It is also the true one.",
                 "american football on grass", "stock"),
            Beat("The next time someone tells you seventy-eight percent, you will know "
                 "where it came from. And what it replaced.",
                 "stadium lights turning off", "stock"),
        ]),
    ],
)


def build():
    """Full documentary build. Renders only -- never uploads."""
    import os
    import longform_creator as lf
    import pro_shorts_creator as psc
    from logger import log

    issues = SCRIPT.validate()
    if issues:
        raise RuntimeError(f"Script validation failed: {issues}")
    log(SCRIPT.report())

    log("Sourcing themed visual pool (vision-gated)...")
    pool = lf.source_pool(SCRIPT, per_theme=3)
    beat_clips = lf.assign_visuals(SCRIPT, pool)
    log(f"Assigned visuals to {len(beat_clips)} beats "
        f"from {len({p for p in beat_clips})} distinct clips")

    log("Generating narration...")
    vo_path = lf.generate_long_voiceover(SCRIPT)

    from moviepy import AudioFileClip
    vo_dur = AudioFileClip(vo_path).duration
    log(f"Narration runtime: {vo_dur/60:.1f} min")

    music_path = None
    try:
        music_path = psc.get_music(duration=min(vo_dur, 600),
                                   script={"hook": SCRIPT.title,
                                           "body": SCRIPT.description,
                                           "cta": ""})
    except Exception as e:
        log(f"Music skipped ({e})")

    out_path = os.path.join(config.VIDEOS_DIR, "doc_athletes_broke.mp4")
    lf.render(SCRIPT, beat_clips, vo_path, music_path, out_path)
    print("VO_PATH=" + vo_path)
    return out_path, vo_path


if __name__ == "__main__":
    import sys
    if "--build" in sys.argv:
        build()
    else:
        print(SCRIPT.report())
        issues = SCRIPT.validate()
        print("\nValidation:", "PASSED" if not issues else "")
        for i in issues:
            print("  -", i)
        build_narration_file(SCRIPT)
        SCRIPT.save("output/scripts/athletes_broke.json")
