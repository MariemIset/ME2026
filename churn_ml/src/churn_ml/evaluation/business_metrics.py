"""Business-aligned evaluation.

We translate raw ML metrics into outcomes the retention team can act on:

* **Revenue at risk (RaR)**         — sum of CLV across customers the model
  flags. Critical for sizing the retention budget.
* **Targeted intervention precision** — share of contacted customers who
  would actually have churned. Drives ROI vs blind outreach.
* **Retention uplift (assumed)**     — expected churners saved given an
  assumed save-rate per contacted customer. Conservative defaults are used.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd


@dataclass
class BusinessReport:
    n_contacted: int
    contact_rate: float
    contacted_precision: float
    expected_saved_churners: float
    revenue_at_risk: float
    revenue_at_risk_in_contacted: float
    save_rate_assumption: float
    contact_cost_per_customer: float
    expected_program_roi: float

    def to_dict(self) -> dict:
        return asdict(self)


def evaluate_business_value(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    clv: pd.Series,
    threshold: float,
    save_rate: float = 0.30,
    contact_cost_per_customer: float = 25.0,
) -> BusinessReport:
    """Compute the business value of contacting every customer above
    ``threshold``.

    Assumptions
    -----------
    * ``save_rate`` (default 30 %) — the fraction of contacted churners we
      successfully retain. Calibrate from A/B test data once available.
    * ``contact_cost_per_customer`` — average marginal cost of a contact
      (e-mail + offer + ops overhead).
    """
    y_true = np.asarray(y_true)
    contacted = y_proba >= threshold
    n_contacted = int(contacted.sum())

    if n_contacted == 0:
        return BusinessReport(
            n_contacted=0, contact_rate=0.0, contacted_precision=0.0,
            expected_saved_churners=0.0, revenue_at_risk=float(clv[y_true == 1].sum()),
            revenue_at_risk_in_contacted=0.0,
            save_rate_assumption=save_rate,
            contact_cost_per_customer=contact_cost_per_customer,
            expected_program_roi=0.0,
        )

    contacted_true_churners = int((contacted & (y_true == 1)).sum())
    contacted_precision = contacted_true_churners / n_contacted
    expected_saved = contacted_true_churners * save_rate

    clv_arr = clv.to_numpy(dtype=float)
    rar_total = float(np.nansum(clv_arr[y_true == 1]))
    rar_contacted_actual = float(np.nansum(clv_arr[contacted & (y_true == 1)]))

    saved_revenue = save_rate * rar_contacted_actual
    program_cost = n_contacted * contact_cost_per_customer
    roi = (saved_revenue - program_cost) / program_cost if program_cost > 0 else 0.0

    return BusinessReport(
        n_contacted=n_contacted,
        contact_rate=n_contacted / len(y_true),
        contacted_precision=contacted_precision,
        expected_saved_churners=expected_saved,
        revenue_at_risk=rar_total,
        revenue_at_risk_in_contacted=rar_contacted_actual,
        save_rate_assumption=save_rate,
        contact_cost_per_customer=contact_cost_per_customer,
        expected_program_roi=roi,
    )
