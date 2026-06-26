"""Submission agent (cabt: Pokemon TCG AI Battle).

The grader calls the LAST def in this file: agent(observation) -> action.
At deck selection (obs.select is None) the agent returns the 60-card deck list;
otherwise it returns option indices. Self-contained: needs only the vendored
modules (search_teacher/heuristic_agent/cards/deck_io) + cg/. No torch/numpy,
no file reads. Deck = mega_starmie_ex_2; piloted by SearchTeacher (2-ply).

TIMING (cabt): actTimeout=0 + ~12 s remainingOverageTime pool => ~12 s of TOTAL
thinking PER GAME. Measured ~2-3 s/game (4x margin). time_budget=1.0 is a
per-move outlier cap. If timeouts appear vs long games, set plies=1.
"""
from search_teacher import SearchTeacher

DECK = [
    860, 860, 860, 860, 861, 861, 861, 1030, 1030, 1030, 1030, 1031,
    1031, 1031, 1189, 1189, 1189, 1189, 1227, 1227, 1227, 1227, 1229, 1229,
    1229, 1182, 1182, 1225, 1225, 1211, 1119, 1119, 1119, 1119, 1086, 1086,
    1086, 1086, 1122, 1122, 1122, 1145, 1145, 1123, 1123, 1097, 1252, 1252,
    3, 3, 3, 3, 3, 3, 3, 3, 3, 11, 17, 12,
]

_AGENT = SearchTeacher(deck=DECK, plies=2, samples=1,
                       dynamic_attack=True, time_budget=1.0,
                       rollout_policy="improved_dev")


def agent(observation):
    return _AGENT(observation)
