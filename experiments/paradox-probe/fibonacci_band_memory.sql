-- =========================================
-- Fibonacci Band Memory System (PostgreSQL)
-- Single-file implementation
--
-- Author: Jaie Parker (via ChatGPT experiment)
-- Date: 2026-04-01
--
-- PURPOSE:
-- Memories are assigned to Fibonacci-spaced bands (1,2,3,5,8,13,21)
-- based on a composite score. Retrieval samples ACROSS bands —
-- sharp focus (band 1) + broad context (band 21) simultaneously.
--
-- OMDR CONNECTION:
-- - Fibonacci spacing IS the dissipation cascade (memory file:
--   claude_thought_fibonacci_dissipation.md)
-- - Band 1 = high-frequency, recent, sharp (surface reactions)
-- - Band 21 = low-frequency, persistent, broad (core identity)
-- - Cross-band retrieval = multi-scale observation (Eq. 3 across timescales)
-- - The score formula (relevance*0.5 + recency*0.3 + log(frequency)*0.2)
--   IS a coupling constant: relevance = resonance, recency = time decay,
--   frequency = standing wave strength (retrieved more = more persistent)
-- - resonance_count tracks how often a memory is retrieved —
--   this IS the recall log idea from consonance memory
--
-- CONNECTION TO CONSONANCE MEMORY LAYERS:
-- This could be the retrieval strategy for Layer 2 (Graph):
--   Instead of flat "return top N", sample across Fibonacci bands
--   to get both precise matches AND broad context simultaneously.
-- The assign_fib_band() function maps continuous score to discrete
--   Fibonacci levels — this IS rationalization (Stern-Brocot style).
--
-- CONNECTION TO ADAPTIVE BAND MEMORY (adaptive_band_memory.py):
-- The Python version makes the weights dynamic (context-dependent).
-- This SQL version makes the BANDS dynamic (score-dependent).
-- Together: dynamic weights feeding into dynamic bands = full system.
--
-- NOTE: Original from ChatGPT had markdown code-block artifacts.
-- This is the cleaned, runnable version.
-- =========================================

-- Optional: enable extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;
-- CREATE EXTENSION IF NOT EXISTS vector; -- uncomment if using pgvector

-- =========================================
-- TABLE
-- =========================================
CREATE TABLE memory_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    content TEXT NOT NULL,

    -- Optional embedding (requires pgvector)
    -- embedding VECTOR(1536),

    relevance FLOAT DEFAULT 0,
    recency FLOAT DEFAULT 0,
    frequency INT DEFAULT 1,

    score FLOAT GENERATED ALWAYS AS (
        (relevance * 0.5) +
        (recency * 0.3) +
        (LOG(frequency + 1) * 0.2)
    ) STORED,

    band INT,
    resonance_count INT DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW()
);

-- =========================================
-- FIBONACCI BAND FUNCTION
-- =========================================
-- Maps continuous score to Fibonacci-spaced discrete bands.
-- This IS rationalization: continuous → nearest Fibonacci level.
-- The Fibonacci numbers ARE the Farey hierarchy's backbone.
CREATE OR REPLACE FUNCTION assign_fib_band(score FLOAT)
RETURNS INT AS $$
BEGIN
    IF score < 1 THEN RETURN 1;
    ELSIF score < 2 THEN RETURN 2;
    ELSIF score < 3 THEN RETURN 3;
    ELSIF score < 5 THEN RETURN 5;
    ELSIF score < 8 THEN RETURN 8;
    ELSIF score < 13 THEN RETURN 13;
    ELSE RETURN 21;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =========================================
-- TRIGGER TO AUTO-ASSIGN BAND
-- =========================================
CREATE OR REPLACE FUNCTION set_band()
RETURNS TRIGGER AS $$
BEGIN
    NEW.band := assign_fib_band(NEW.score);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_set_band
BEFORE INSERT OR UPDATE ON memory_items
FOR EACH ROW
EXECUTE FUNCTION set_band();

-- =========================================
-- INSERT EXAMPLE
-- =========================================
-- INSERT INTO memory_items (content, relevance, recency, frequency)
-- VALUES ('example thought', 0.9, 0.8, 3);

-- =========================================
-- FIBONACCI BAND RETRIEVAL
-- =========================================
-- Multi-scale memory pull (sharp → broad)
-- THIS IS THE KEY IDEA: sample across bands simultaneously.
-- Band 1 = precise, recent. Band 21 = persistent, core.
-- You get both the surface and the depth in one query.
(
    SELECT * FROM memory_items
    WHERE band = 1
    ORDER BY score DESC
    LIMIT 3
)
UNION ALL
(
    SELECT * FROM memory_items
    WHERE band = 3
    ORDER BY score DESC
    LIMIT 3
)
UNION ALL
(
    SELECT * FROM memory_items
    WHERE band = 8
    ORDER BY score DESC
    LIMIT 2
)
UNION ALL
(
    SELECT * FROM memory_items
    WHERE band = 21
    ORDER BY score DESC
    LIMIT 2
);

-- =========================================
-- OPTIONAL: RESONANCE UPDATE
-- =========================================
-- Track retrieval frequency — memories that resonate more
-- get retrieved more → frequency increases → score increases
-- → band shifts → self-reinforcing standing wave
--
-- UPDATE memory_items
-- SET resonance_count = resonance_count + 1
-- WHERE id IN (<ids returned from query>);

-- =========================================
-- NOTES
-- =========================================
-- score = importance signal (composite coupling constant)
-- band = scale layer (Fibonacci spaced — dissipation cascade)
-- retrieval = cross-band sampling (multi-scale observation)
-- resonance_count = standing wave strength (retrieved more = more persistent)
-- =========================================
