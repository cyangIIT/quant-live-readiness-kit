"""quant-live-readiness-kit (qlrk).

Operational infrastructure for taking a systematic trading strategy from
research to auditable paper and live readiness.

This package is deliberately alpha-free: it provides primitives (freeze
manifests, contamination detection, reconciliation, monitoring, kill
switches, promotion gates, alerting, reporting) that sit *around* your
strategy. Bring your own signal.
"""

__version__ = "0.1.0"

__all__ = [
    "__version__",
]
