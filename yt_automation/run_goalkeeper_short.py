"""
One-shot: generate 1 video using the new goalkeeper 9-save script entry
(added to SCRIPT_LIBRARY to replicate the winning "8-Minute Hat-Trick" format),
bypassing the dynamic Gemini path so this exact script is used, then upload.
"""
import visual_shorts_creator as vsc

GOALKEEPER_SCRIPT = vsc.SCRIPT_LIBRARY[-1]
GOALKEEPER_IDX = len(vsc.SCRIPT_LIBRARY) - 1


def _forced_pick_script(state):
    used = set(state.get("used", []))
    used.add(GOALKEEPER_IDX)
    state["used"] = list(used)
    state["script_idx"] = GOALKEEPER_IDX
    return GOALKEEPER_SCRIPT.copy()


vsc.pick_script = _forced_pick_script

vsc.run_one_job()
