"""SCIPRA manuscript table arithmetic generator.

This script reproduces PCI/RPCI arithmetic from the scenario domain scores
reported in the manuscript. It does NOT independently derive those domain
scores from the raw documentary corpus. Empirical end-to-end reproduction
requires the complete documented corpus and upstream derivation pipeline.

Usage:
    python code/generate_tables.py
"""

from pci_computation import DomainScores, pci, pci_nonlinear, rpci, rpci_raw, weighted_sigma

# Published/calibrated scenario-domain inputs from manuscript Table 5.
# Keeping them here makes the downstream PCI/RPCI arithmetic transparent, but
# they must not be described as independently reconstructed from raw data.
SCENARIOS = {
    "A: Pre-Intervention (2010-2012)":  DomainScores(0.82, 0.48, 0.12),
    "B: Post-Charter III (2018-2021)":  DomainScores(0.70, 0.75, 0.55),
    "C: SCIPRA-Optimised (projected)":  DomainScores(0.75, 0.80, 0.79),
}
WEIGHTS = (0.30, 0.35, 0.35)
LAMBDA = 0.10
BETA = 0.50


def table_5():
    print("\n" + "=" * 80)
    print("TABLE 5 ARITHMETIC CHECK: Published Domain Scores -> PCI")
    print("=" * 80)
    header = f"{'Scenario':<38} {'I':>6} {'R':>6} {'S':>6} {'PCI':>8} {'PCI-NL':>10}"
    print(header)
    print("-" * 80)
    for name, sc in SCENARIOS.items():
        print(
            f"{name:<38}"
            f" {sc.investment:>6.3f}"
            f" {sc.regulatory:>6.3f}"
            f" {sc.stakeholder:>6.3f}"
            f" {pci(sc, WEIGHTS):>8.3f}"
            f" {pci_nonlinear(sc, WEIGHTS, BETA):>10.3f}"
        )
    print("\nNote: I/R/S are published scenario inputs, not values reconstructed here from raw evidence.")


def table_7():
    print("\n" + "=" * 80)
    print("RPCI ARITHMETIC CHECK — Normalized Form (SI Eq. A.10)")
    print("=" * 80)
    header = (
        f"{'Scenario':<38} {'PCI':>8} {'sigma':>8}"
        f" {'RPCI_raw':>10} {'RPCI_norm':>12}"
    )
    print(header)
    print("-" * 80)
    for name, sc in SCENARIOS.items():
        p0 = pci(sc, WEIGHTS)
        sig = weighted_sigma(sc, WEIGHTS)
        r_raw = rpci_raw(sc, WEIGHTS, LAMBDA)
        r_nrm = rpci(sc, WEIGHTS, LAMBDA)
        print(
            f"{name:<38}"
            f" {p0:>8.3f}"
            f" {sig:>8.4f}"
            f" {r_raw:>10.3f}"
            f" {r_nrm:>12.3f}"
        )
    print("\nNotes:")
    print("  sigma = weighted standard deviation of domain scores")
    print("  RPCI_raw  = max(0, PCI - lambda*sigma)")
    print("  RPCI_norm = RPCI_raw / (1 + lambda/2)")
    print(f"  lambda = {LAMBDA}")


def parameter_summary():
    print("\n" + "=" * 80)
    print("DOCUMENTED PARAMETER SUMMARY")
    print("=" * 80)
    params = [
        ("PCI domain weights (w1, w2, w3)", "0.30, 0.35, 0.35"),
        ("SIC coefficients (alpha, beta, gamma)", "0.30, 0.40, 0.30"),
        ("Dispersion sensitivity (lambda)", "0.10"),
        ("Harmonic-Linear blend (beta)", "0.50"),
        ("VADER urgency ceiling", "0.10"),
        ("SVM random_state", "42"),
        ("CV protocol", "Stratified 5-fold on full corpus"),
        ("TF-IDF max_features", "500"),
        ("TF-IDF min_df / max_df", "2 / 0.90"),
        ("Manuscript-reported corpus size", "87 documents"),
        ("Current repository manifest", "13 documents — empirical reproduction incomplete"),
    ]
    for label, value in params:
        print(f"  {label:<45} {value}")


if __name__ == "__main__":
    print("\nSCIPRA MANUSCRIPT ARITHMETIC CHECK")
    print("This script checks downstream table calculations from published domain inputs.")
    table_5()
    table_7()
    parameter_summary()
