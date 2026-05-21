-- =========================================================================
-- BO2 — Loyalty recommendations sink (created on-demand by the engine)
-- =========================================================================
CREATE TABLE IF NOT EXISTS loyalty_recommendations (
    recommendation_id   BIGSERIAL PRIMARY KEY,
    scored_at           TIMESTAMP NOT NULL DEFAULT NOW(),
    as_of_date          DATE      NOT NULL,
    loyalty_number      INT       NOT NULL,
    segment_id          INT       NOT NULL,
    segment_label       VARCHAR(64) NOT NULL,
    redemption_proba    NUMERIC(6,5) NOT NULL,
    uplift_score        NUMERIC(7,6) NOT NULL,
    recommended_reward  VARCHAR(64) NOT NULL,
    expected_value      NUMERIC(10,4) NOT NULL,
    reward_rank         INT       NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_loyalty_reco_loyalty
    ON loyalty_recommendations (loyalty_number);
CREATE INDEX IF NOT EXISTS ix_loyalty_reco_as_of
    ON loyalty_recommendations (as_of_date);
