import sys

from .hooker import Hooker
from .util import Empty
from .profiling import format_timedelta


os = Empty()
os.path = Empty()
os.path.basename = lambda s: s

enum = Empty()
enum.Enum = Empty

sys.modules['os'] = os
sys.modules['re'] = Empty()
sys.modules['enum'] = enum

import _functools
sys.modules['functools'] = _functools

import pstats
pstats.f8 = format_timedelta

import cProfile
p = cProfile.Profile()

@Hooker.OnInit.attach
def start_profiling():
    p.enable()

def print_stats(cumtime=False):
    p.print_stats((cumtime and 2) or 1)

def clear():
    p.clear()
