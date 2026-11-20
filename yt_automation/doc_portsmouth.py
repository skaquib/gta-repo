"""
doc_portsmouth.py — documentary #2. "From Wembley to the Bottom"

WHY THIS TOPIC (data-driven, 2026-09-11):
Doc #1 was myth-busting a statistic. The Shorts data says that register is
our weakest: the stat-debunk Short got 8 views while absurd MOMENT/drama
Shorts got 843 and 385. So doc #2 is pure narrative drama, not analysis.

It also stays in the SPORTS MONEY niche, which is the high-CPM bridge --
sports alone is low-CPM entertainment; sports finance sits in the business
category advertisers pay for. And it needs no rights-managed footage: the
story is carried by archive photos, stadiums, documents and empty terraces.

VERIFIED (2026-09-11: Wikipedia 2008 FA Cup final, 2009-10 and 2010-11
Portsmouth F.C. season pages, 2010 FA Cup final, Portsmouth FC official
history, Boardroom Ball):
- 17 May 2008: Portsmouth beat Cardiff City 1-0 at Wembley to win the FA
  Cup and qualify for Europe. Squad included David James, Sol Campbell,
  Glen Johnson, Sylvain Distin, Lassana Diarra, Sulley Muntari, Pedro
  Mendes and Niko Kranjcar.
- 2009 into early 2010: ownership changed hands repeatedly -- Alexandre
  Gaydamak sold to Sulaiman Al-Fahim, and that regime gave way again.
- 26 February 2010: Portsmouth entered administration -- the FIRST Premier
  League club ever to do so -- and were docked nine points.
- 2010: reached the FA Cup final again, lost 1-0 to Chelsea, and were
  relegated to the Championship in the same season.
- 2012: relegated to League One, out of the top two divisions for the
  first time since 1983.
- 2013: fell to League Two, the bottom tier.

DELIBERATELY OMITTED: specific debt figures. Reported totals vary between
sources and none could be confirmed to a primary source, so the script
states none -- the same discipline that removed the transfer fee from the
Gabriel Jesus Short when Sky, ESPN and Barca Blaugranes disagreed.
"""
import config
from longform_creator import DocScript, Chapter, Beat, build_narration_file

SCRIPT = DocScript(
    title="From Wembley to the Bottom: How Portsmouth Fell",
    hook_card="FA CUP TO FOURTH TIER",
    description=(
        "In May 2008 Portsmouth won the FA Cup at Wembley. Less than two years "
        "later they became the first Premier League club ever to enter "
        "administration. Five years after lifting the trophy they were in the "
        "fourth tier. This is how a club wins the oldest cup competition in "
        "football and then falls further than anyone thought possible."
    ),
    tags=["portsmouth", "football", "fa cup", "sports business", "premier league",
          "football finance", "administration", "sports money", "documentary"],
    sources=[
        "2008 FA Cup final -- Wikipedia",
        "2009-10 Portsmouth F.C. season -- Wikipedia",
        "2010 FA Cup final -- Wikipedia",
        "2010-11 Portsmouth F.C. season -- Wikipedia",
        "Honours and History -- Portsmouth FC official site",
        "Portsmouth's Premier League Crash -- Boardroom Ball",
    ],
    chapters=[
        Chapter("Cold Open", [
            Beat("On the seventeenth of May, 2008, Portsmouth Football Club walked "
                 "out at Wembley.", "empty stadium wide shot", "stock"),
            Beat("Ninety minutes later they were FA Cup winners.",
                 "football trophy silver", "stock"),
            Beat("They had beaten Cardiff City one-nil. They had qualified for "
                 "Europe. They were a Premier League club with a trophy and a squad "
                 "full of internationals.", "football stadium crowd celebrating", "stock"),
            Beat("Five years later, they were playing in the fourth tier of English "
                 "football.", "empty terraces stadium", "stock"),
            Beat("Not relegated once. Relegated three times, in consecutive seasons.",
                 "empty stadium steps", "stock"),
            Beat("And along the way they became the first Premier League club in "
                 "history to go into administration.",
                 "courthouse steps building", "stock"),
            Beat("Clubs decline all the time. Very few fall from a trophy at Wembley "
                 "to the bottom division of the league in the time it takes to finish "
                 "a degree.", "empty football ground small", "stock"),
            Beat("This is not a story about bad luck. It is a story about money that "
                 "was never really there.", "empty football stadium night", "stock"),
        ]),

        Chapter("Act 1 - The Team That Won It", [
            Beat("Look at the side that lifted that cup.",
                 "football players lining up", "stock"),
            Beat("David James in goal. Sol Campbell and Sylvain Distin in defence. "
                 "Glen Johnson at right back.", "goalkeeper gloves football", "stock"),
            Beat("Lassana Diarra and Sulley Muntari in midfield. Pedro Mendes. Niko "
                 "Kranjcar.", "football match action midfield", "stock"),
            Beat("That is not a mid-table squad. That is a team of established "
                 "internationals, at a club whose stadium held barely twenty thousand "
                 "people.", "small football stadium stands", "stock"),
            Beat("Think about what that means in practice.",
                 "empty stadium seats rows", "stock"),
            Beat("A football club's income is broadly fixed by its size. Tickets, "
                 "merchandise, its share of the television money.",
                 "ticket turnstile stadium", "stock"),
            Beat("Portsmouth's stadium capacity put a hard ceiling on the first two. "
                 "And television money in the Premier League is shared, not earned by "
                 "trophies.", "television broadcast cameras", "stock"),
            Beat("So the revenue of a small club. And the wage bill of a big one.",
                 "financial documents calculator", "stock"),
            Beat("And that gap, between the size of the squad and the size of the "
                 "club, is the entire story.",
                 "football stadium aerial small", "stock"),
            Beat("Portsmouth were not winning the FA Cup because they had grown. They "
                 "were winning it because they were spending like a club that had.",
                 "money cash counting", "stock"),
            Beat("For one season, that worked perfectly. That is the dangerous part.",
                 "football trophy silver close", "stock"),
        ]),

        Chapter("Act 2 - The Owners Start Leaving", [
            Beat("Wages at that level have to be paid every month, for years, whether "
                 "or not you qualify for Europe again.",
                 "payroll documents desk", "stock"),
            Beat("Portsmouth did not qualify again.",
                 "empty football pitch rain", "stock"),
            Beat("And then something happened that should worry any supporter. The "
                 "owners began handing the club on.",
                 "business handshake office", "stock"),
            Beat("Alexandre Gaydamak sold to Sulaiman Al-Fahim. That regime gave way "
                 "again. Control of the football club changed hands repeatedly across "
                 "2009 and into 2010.", "signing contract documents", "stock"),
            Beat("Each new owner inherited the same wage bill, and the same problem.",
                 "calculator financial documents", "stock"),
            Beat("Football clubs do not usually change owners three times in a year "
                 "when things are going well.",
                 "empty boardroom chairs", "stock"),
            Beat("When a club changes hands that quickly, it is rarely because "
                 "everyone wants to own it. It is usually because nobody can afford "
                 "to keep it.", "office empty desk night", "stock"),
            Beat("Supporters could see something was wrong. What they could not see "
                 "was how far it had already gone.",
                 "football fans stadium", "stock"),
            Beat("Because a football club in trouble still plays every weekend. The "
                 "stadium still opens. The team still runs out.",
                 "football players entering pitch", "stock"),
            Beat("The collapse happens in offices, months before it happens on the "
                 "pitch.", "empty office corridor", "stock"),
        ]),

        Chapter("Act 3 - The First One", [
            Beat("On the twenty-sixth of February, 2010, Portsmouth entered "
                 "administration.", "courthouse building exterior", "stock"),
            Beat("They were the first Premier League club in history to do it.",
                 "premier league football stadium", "stock"),
            Beat("Not the first small club. Not the first club in the lower "
                 "divisions. The first club in the richest league in world football.",
                 "football stadium floodlights night", "stock"),
            Beat("Administration means the club can no longer pay what it owes, and "
                 "control passes to insolvency practitioners whose job is to protect "
                 "the creditors.", "legal documents signing", "stock"),
            Beat("Not the manager. Not the supporters. The people owed money.",
                 "invoice paperwork desk", "stock"),
            Beat("The punishment was a nine point deduction.",
                 "football scoreboard", "stock"),
            Beat("For a team already near the bottom, that made relegation close to "
                 "unavoidable.", "empty stadium seats", "stock"),
            Beat("The deduction exists so clubs cannot spend recklessly, collapse, and "
                 "keep the sporting advantage they bought.",
                 "football pitch line markings", "stock"),
            Beat("Which is fair. It is also brutal, because it lands on the players "
                 "and the supporters, not the owners who left.",
                 "empty stadium terrace", "stock"),
            Beat("And here is the detail that makes this story genuinely strange.",
                 "football pitch centre circle", "stock"),
            Beat("In the same season they went into administration, Portsmouth "
                 "reached the FA Cup final again.",
                 "wembley stadium arch", "stock"),
            Beat("They lost one-nil to Chelsea. A club in administration, ninety "
                 "minutes from a second trophy in three years.",
                 "football trophy presentation", "stock"),
            Beat("They were relegated that same season.",
                 "dejected football player", "stock"),
        ]),

        Chapter("Act 4 - The Fall Keeps Going", [
            Beat("Relegation is usually where these stories end. A club drops a "
                 "division, sells its best players, and stabilises.",
                 "football players training", "stock"),
            Beat("Portsmouth kept falling.",
                 "stairs descending", "stock"),
            Beat("In 2012 they were relegated again, to League One.",
                 "lower league football ground", "stock"),
            Beat("That took them out of the top two divisions of English football for "
                 "the first time since 1983.",
                 "old football programme archive", "stock"),
            Beat("The following year they fell again, into League Two. The bottom "
                 "tier.", "empty non league stadium", "stock"),
            Beat("Every drop costs a club more than pride. Each division down means "
                 "less television money, smaller crowds, cheaper players.",
                 "lower league football match", "stock"),
            Beat("Which makes climbing back harder than falling was. That is why "
                 "these collapses so rarely reverse quickly.",
                 "stairs climbing", "stock"),
            Beat("From an FA Cup final at Wembley to the fourth division, in five "
                 "years.", "empty stadium wide", "stock"),
            Beat("The same club. Many of the same supporters. A completely different "
                 "football club.", "football fans scarves", "stock"),
        ]),

        Chapter("Close", [
            Beat("It is tempting to call this bad management, and leave it there.",
                 "business meeting documents", "stock"),
            Beat("But look at what actually happened.",
                 "financial charts screen", "stock"),
            Beat("Portsmouth did not fail because they lost. They failed at the exact "
                 "moment they were winning.",
                 "football trophy close up", "stock"),
            Beat("The FA Cup, the European qualification, the internationals in the "
                 "squad. Those were not the reward for the spending. They were the "
                 "spending.", "money stacks close up", "stock"),
            Beat("A trophy does not generate the money it takes to win one. Not at a "
                 "club that size.", "empty trophy cabinet", "stock"),
            Beat("An FA Cup brings prize money, a run in Europe, and a good year of "
                 "shirt sales. It does not bring years of Premier League wages.",
                 "football shirts merchandise", "stock"),
            Beat("The maths only works if you keep qualifying. Keep winning. Keep the "
                 "run going, permanently.",
                 "football pitch floodlights", "stock"),
            Beat("And no club that size keeps that going forever. It only has to stop "
                 "once.", "empty stadium single seat", "stock"),
            Beat("Portsmouth bought a season that their income could never repay, and "
                 "then spent five years paying for it.",
                 "empty football stadium sunset", "stock"),
            Beat("They remain the clearest warning in English football of what "
                 "winning can cost.",
                 "football stadium empty night", "stock"),
            Beat("And every club that overspends to chase one good season is making "
                 "the same bet they did.",
                 "football pitch aerial", "stock"),
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
    out = os.path.join(config.VIDEOS_DIR, "doc_portsmouth.mp4")
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
