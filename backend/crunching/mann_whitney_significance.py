"""Mann-Whitney U significance, Bonferroni-corrected across POPULATIONS.

Mann-Whitney U (Wilcoxon rank-sum) tests whether two independent samples'
distributions differ -- the natural counterpart to a median/quartile-based
analysis, and unlike a t-test, doesn't assume normality. It requires
independent observations, so callers must pass one value per subject (see
crunching.response_frequencies.get_response_subject_frequencies), not one
value per sample -- a subject contributing multiple samples would otherwise
violate that assumption (pseudoreplication), biasing p-values toward
appearing more significant than they really are.
"""

from scipy.stats import mannwhitneyu

from backend.crunching.cell_frequencies import POPULATIONS
from backend.crunching.significance import SignificanceMethod, SignificanceResult

ALPHA = 0.05
# Testing all 5 populations at once with an uncorrected alpha=0.05 each gives
# ~23% overall false-positive risk (1 - 0.95**5), not 5%. Bonferroni divides
# alpha by the number of simultaneous tests to keep the overall risk near 5%.
BONFERRONI_ALPHA = ALPHA / len(POPULATIONS)


def _test(responder_values: list[float], non_responder_values: list[float]) -> SignificanceResult:
    _, p_value = mannwhitneyu(responder_values, non_responder_values, alternative="two-sided")
    # scipy returns numpy scalars (numpy.float64, and numpy.bool_ from the
    # comparison below) -- cast to native Python types so SignificanceResult
    # actually holds what its annotations (float, bool) declare, not just
    # something that happens to behave similarly (e.g. `numpy.bool_() is
    # False` is False, unlike a real Python bool).
    return SignificanceResult(
        statistic=float(p_value), significant=bool(p_value < BONFERRONI_ALPHA)
    )


MANN_WHITNEY_U = SignificanceMethod(
    name="Mann-Whitney U test",
    description=(
        "Significance is determined by a Mann-Whitney U test comparing "
        "responders to non-responders, using one value per subject (the "
        "median across that subject's own samples) rather than one value "
        "per sample, since the test assumes independent observations. A "
        f"population is flagged significant at p < {BONFERRONI_ALPHA:.3g} "
        f"-- a Bonferroni-corrected threshold ({ALPHA} divided by "
        f"{len(POPULATIONS)}, the number of populations tested at once) "
        "rather than the usual 0.05, to control the chance of a false "
        "positive across all populations tested together."
    ),
    test=_test,
)
