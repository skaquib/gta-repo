"""
doc_dixon.py — documentary #2. "He Drew Golf Courses in Prison for 27 Years"

WHY THIS STORY (brief set by the channel owner 2026-09-11):
The ask was untold stories, shocking real-life detail, hidden talent, and
something an audience would be curious enough to open. Two earlier drafts
were rejected and both rejections were correct:
  - Portsmouth FC collapse -> business analysis, not a human story.
  - MS Dhoni ticket collector -> not untold at all. It has a 2016 Bollywood
    film ("MS Dhoni: The Untold Story"). Reaching for the most famous
    rags-to-riches example is the opposite of the brief.

This one is genuinely obscure to almost everyone, and it is all four things
at once: untold, shocking, a hidden talent, and a payoff nobody expects.

VERIFIED (2026-09-11: Golf Digest; CNN; CBS News; Innocence Project;
WBUR "Only A Game"; Fox News; Gulf News):
- 1991: Torriano Jackson, 17, is fatally shot on a Buffalo street corner.
- 1992: Valentino Dixon is convicted of the murder, sentenced 39 years to life.
- Early 2000s: a warden at Attica Correctional Facility asks Dixon to draw
  Augusta National's 12th hole from a picture in Golf Digest. Dixon was not
  a golfer and was reluctant at first. The images fired his imagination.
- 2012: Dixon sends artwork and case details to Golf Digest editorial
  director Max Adler, who publishes a piece on the drawings that also lays
  out possible mistakes in the arrest, trial and conviction.
- January 2018: three Georgetown University undergraduates and their
  professors research the case -- gathering evidence, locating witnesses,
  and visiting Dixon in prison.
- 19 September 2018: the 1992 conviction is vacated by the Erie County
  court in Buffalo after 27 years, and a judge accepts a guilty plea from
  another man who confessed to the killing.
- April 2019: Dixon is invited to the Masters at Augusta to sketch for
  Golf Digest.

AUDIENCE NOTE: the channel is 64% India, where golf is niche. That is fine
here -- the hook is human, not sporting. No knowledge of golf is required
to follow a man drawing his way out of a life sentence.

NOT CLAIMED: no invented dialogue, no speculation about guilt beyond the
court record, no embellished prison detail.
"""
import config
from longform_creator import DocScript, Chapter, Beat, build_narration_file

SCRIPT = DocScript(
    title="He Drew Golf Courses in Prison for 27 Years. He'd Never Played.",
    hook_card="HE'D NEVER PLAYED GOLF",
    description=(
        "Valentino Dixon spent 27 years in prison for a murder he did not commit. "
        "A warden handed him a golf magazine and asked him to draw a hole at Augusta. "
        "He had never played golf in his life. He drew courses for years, sent them "
        "to Golf Digest, and those drawings started the chain of events that ended "
        "with his conviction being vacated."
    ),
    tags=["valentino dixon", "golf", "true story", "wrongful conviction",
          "untold story", "art", "documentary", "augusta", "inspiration"],
    sources=[
        "Valentino Dixon, whose golf illustrations sustained him while in prison, has his murder conviction vacated after 27 years -- Golf Digest",
        "How art and golf freed innocent man from life sentence -- CNN",
        "New York inmate Valentino Dixon cleared of 1991 murder, thanks partly to his golf drawings -- CBS News",
        "Golf Digest Helps Wrongly Convicted Man Regain his Freedom -- Innocence Project",
        "Golf Artist Valentino Dixon Draws Himself Out Of Prison -- WBUR, Only A Game",
    ],
    chapters=[
        Chapter("Cold Open", [
            Beat("A man spent twenty-seven years in prison drawing golf courses.",
                 "golf course green aerial", "stock"),
            Beat("Hole after hole. Fairways, bunkers, water, trees. Thousands of hours "
                 "of them.", "golf course fairway trees", "stock"),
            Beat("He had never played golf. Not once.",
                 "golf ball on tee", "stock"),
            Beat("He had never even seen a golf course in person.",
                 "golf course wide landscape", "stock"),
            Beat("And those drawings are part of the reason he is not in prison today.",
                 "prison fence barbed wire", "stock"),
            Beat("Not a lawyer. Not new forensic evidence. Drawings of fairways, made "
                 "in coloured pencil by a man serving thirty-nine years to life.",
                 "coloured pencils drawing", "stock"),
            Beat("If you want a subscribe-worthy story, this is it. So subscribe, "
                 "because this one is genuinely difficult to believe.",
                 "golf course morning light", "stock"),
            Beat("This is the story of Valentino Dixon.",
                 "pencil drawing paper", "stock"),
        ]),

        Chapter("Act 1 - Buffalo, 1991", [
            Beat("In 1991, a seventeen year old named Torriano Jackson was shot and "
                 "killed on a street corner in Buffalo, New York.",
                 "city street night", "stock"),
            Beat("In 1992, Valentino Dixon was convicted of that murder.",
                 "courthouse exterior", "stock"),
            Beat("He was sentenced to thirty-nine years to life.",
                 "prison corridor", "stock"),
            Beat("Thirty-nine years to life means you do not get to plan anything. "
                 "There is no date to count down to.",
                 "prison cell bars", "stock"),
            Beat("Dixon said he had not done it.",
                 "empty interrogation room", "stock"),
            Beat("So does almost everyone in prison. That is the problem with saying "
                 "it. It is the most common sentence in the building.",
                 "prison hallway", "stock"),
            Beat("He went to Attica Correctional Facility, and the years started.",
                 "prison building exterior", "stock"),
            Beat("Understand what twenty-seven years actually is.",
                 "clock face time", "stock"),
            Beat("He went in during 1992. Mobile phones were rare. There was no public "
                 "internet to speak of.", "old telephone vintage", "stock"),
            Beat("Children who had not been born when he was convicted were finishing "
                 "university while he was still inside.",
                 "university graduation", "stock"),
            Beat("And for almost all of that time, nobody outside was working on his "
                 "case.", "empty office night", "stock"),
        ]),

        Chapter("Act 2 - The Warden's Request", [
            Beat("In the early 2000s, something small and completely random happened.",
                 "magazine pages", "stock"),
            Beat("A warden at Attica asked Dixon to draw something for him.",
                 "pencil sketch hands", "stock"),
            Beat("Specifically, the twelfth hole at Augusta National, from a picture "
                 "in a copy of Golf Digest.", "golf hole green flag", "stock"),
            Beat("Dixon was not interested. He was not a golfer. He had no connection "
                 "to the sport at all.", "golf magazine", "stock"),
            Beat("He was reluctant. But he drew it anyway.",
                 "drawing with coloured pencils", "stock"),
            Beat("And then something unexpected happened to him.",
                 "artist sketching detail", "stock"),
            Beat("The image caught hold of him.",
                 "golf course sunrise", "stock"),
            Beat("Think about what a golf course actually looks like to someone "
                 "living inside a maximum security prison.",
                 "prison yard wall", "stock"),
            Beat("Open space. Distance. Grass. Somewhere you can see all the way to "
                 "the horizon.", "golf course open fairway", "stock"),
            Beat("Everything a cell is not.",
                 "small window light", "stock"),
        ]),

        Chapter("Act 3 - Drawing a Game He Had Never Played", [
            Beat("So he kept drawing them.",
                 "coloured pencils close up", "stock"),
            Beat("Not occasionally. Constantly, for years.",
                 "stack of drawings paper", "stock"),
            Beat("Courses he had never visited. A sport he had never played. Places "
                 "he had only ever seen in photographs.",
                 "golf course photograph", "stock"),
            Beat("He worked from magazine pictures, and from imagination.",
                 "hands drawing detailed art", "stock"),
            Beat("People who have seen the work describe it the same way. It does not "
                 "look like the output of someone passing time.",
                 "detailed artwork close up", "stock"),
            Beat("It looks like obsession. Precise, patient, enormously detailed.",
                 "art studio drawing", "stock"),
            Beat("He was doing it with coloured pencils, inside a prison, for a game "
                 "he had no relationship to whatsoever.",
                 "coloured pencil drawing", "stock"),
            Beat("And that is the detail that makes this story work.",
                 "golf course green grass", "stock"),
            Beat("If he had drawn his neighbourhood, or his family, nobody outside "
                 "would ever have seen it.",
                 "empty prison visiting room", "stock"),
            Beat("He drew golf. Which meant there was a magazine that cared.",
                 "magazine stack", "stock"),
            Beat("That is the accident at the centre of this whole story.",
                 "golf ball grass close", "stock"),
            Beat("His talent was not golf. His talent was drawing. The golf was "
                 "someone else's idea, handed to him by chance.",
                 "artist hands pencil", "stock"),
            Beat("And it happened to be the one subject that came with an audience "
                 "outside the prison walls.",
                 "golf course clubhouse", "stock"),
        ]),

        Chapter("Act 4 - The Letter", [
            Beat("In 2012, Dixon sent some of his artwork to Golf Digest.",
                 "envelope letter mail", "stock"),
            Beat("It went to the magazine's editorial director, Max Adler. And Dixon "
                 "included details of his case.",
                 "editor desk office", "stock"),
            Beat("Adler could have run a short, pleasant piece about unusual art and "
                 "left it there.", "printing press magazine", "stock"),
            Beat("He did not.",
                 "newspaper printing", "stock"),
            Beat("Golf Digest published a piece that showed the drawings, and also set "
                 "out the possible mistakes made during Dixon's arrest, his trial, and "
                 "his conviction.", "magazine article pages", "stock"),
            Beat("A golf magazine. Publishing an investigation into a murder case.",
                 "golf course flag hole", "stock"),
            Beat("That is not what golf magazines do. It happened because of the "
                 "drawings.", "artwork on wall", "stock"),
            Beat("And it put the case in front of people who had never heard of it.",
                 "reading magazine", "stock"),
        ]),

        Chapter("Act 5 - Three Students", [
            Beat("In January 2018, three undergraduate students at Georgetown "
                 "University took on Dixon's case as part of their studies.",
                 "university campus students", "stock"),
            Beat("Undergraduates. Working with their professors.",
                 "students studying documents", "stock"),
            Beat("They gathered evidence. They located witnesses. They went to the "
                 "prison and sat with him.",
                 "legal documents research", "stock"),
            Beat("Consider what that means about the original case.",
                 "case files folders", "stock"),
            Beat("Work that university students could do, in a matter of months, had "
                 "not been done for twenty-six years.",
                 "empty law library", "stock"),
            Beat("Not because it was impossible. Because nobody had looked.",
                 "dusty archive boxes", "stock"),
            Beat("On the nineteenth of September, 2018, Valentino Dixon's conviction "
                 "was vacated.", "courthouse courtroom", "stock"),
            Beat("A judge accepted a guilty plea from another man, who confessed to "
                 "the killing.", "gavel courtroom", "stock"),
            Beat("Dixon walked out after twenty-seven years.",
                 "open gate daylight", "stock"),
            Beat("He had entered prison in 1992. He left in 2018.",
                 "calendar pages turning", "stock"),
            Beat("Almost everything about the outside world had changed while he was "
                 "drawing fairways he had never walked on.",
                 "city street modern", "stock"),
        ]),

        Chapter("Close", [
            Beat("In April 2019, Dixon was invited to the Masters at Augusta, to "
                 "sketch for Golf Digest.", "golf tournament crowd", "stock"),
            Beat("The twelfth hole. The one the warden had asked him to draw from a "
                 "photograph, years earlier, inside Attica.",
                 "golf hole water bridge", "stock"),
            Beat("He finally stood on the course he had spent decades drawing from "
                 "memory of somebody else's picture.",
                 "golf course beautiful landscape", "stock"),
            Beat("It is tempting to tell this as a story about art saving a life, and "
                 "leave it there. It is nicer that way.",
                 "artwork paintbrush", "stock"),
            Beat("But look at what actually had to happen.",
                 "documents on desk", "stock"),
            Beat("A warden had to make a random request. Dixon had to say yes to "
                 "something he did not care about.",
                 "pencil on paper", "stock"),
            Beat("An editor had to read an unsolicited letter and decide to "
                 "investigate a murder conviction. Students had to pick that case out "
                 "of many.", "letters envelopes pile", "stock"),
            Beat("Remove any one of those and he is still inside.",
                 "prison fence", "stock"),
            Beat("Twenty-seven years, undone by a chain of coincidences that started "
                 "with a drawing of a golf hole by a man who had never played golf.",
                 "golf course empty green", "stock"),
            Beat("Which should make you wonder how many people are still waiting for "
                 "their coincidence.", "prison window light", "stock"),
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
    out = os.path.join(config.VIDEOS_DIR, "doc_dixon.mp4")
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
