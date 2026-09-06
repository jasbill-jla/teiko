"""Pluggable statistical-significance testing for two independent samples.

A `SignificanceMethod` is a swappable unit: callers pass one in rather than
hardcoding a specific test, and should surface its `description` to explain
to an end user how significance was determined -- not write that explanation
themselves, since it would go stale the moment a different method is used.
"""

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class SignificanceResult:
    # The single number this method's significance call is based on (e.g. a
    # p-value) -- comparable across populations, unlike a raw test statistic
    # such as Mann-Whitney U's U value, whose scale depends on sample sizes.
    statistic: float
    significant: bool


@dataclass(frozen=True)
class SignificanceMethod:
    name: str
    # Explains, in plain language, what was computed and how "significant"
    # was decided -- meant to be shown to an end user as-is.
    description: str
    test: Callable[[list[float], list[float]], SignificanceResult]
