-- =========================================================================
-- BO1 — Churn predictions sink
--
-- Idempotent DDL. Created automatically by the batch scorer if absent.
-- =========================================================================
CREATE TABLE IF NOT EXISTS churn_predictions (
    prediction_id      BIGSERIAL PRIMARY KEY,
    scored_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    as_of_date         DATE      NOT NULL,
    model_name         VARCHAR(64) NOT NULL,
    model_version      VARCHAR(64) NOT NULL,
    loyalty_number     INT       NOT NULL,
    churn_probability  NUMERIC(6,5) NOT NULL,
    churn_risk_tier    VARCHAR(16) NOT NULL,
    decision_threshold NUMERIC(6,5) NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_churn_predictions_loyalty
    ON churn_predictions (loyalty_number);
CREATE INDEX IF NOT EXISTS ix_churn_predictions_as_of
    ON churn_predictions (as_of_date);
