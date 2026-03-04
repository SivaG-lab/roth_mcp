# Tax computation sub-package — public API
from tax.calculator import compute_tax_components, compute_bracket_boundaries
from tax.rmd import compute_rmd
from tax.irmaa import compute_irmaa_surcharge
from tax.ss import compute_ss_taxation

__all__ = [
    "compute_tax_components",
    "compute_bracket_boundaries",
    "compute_rmd",
    "compute_irmaa_surcharge",
    "compute_ss_taxation",
]
