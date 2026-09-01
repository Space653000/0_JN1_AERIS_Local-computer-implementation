# Measurement Import / Validation

Purpose: deterministically validate local frequency-response CSV before downstream acoustic analysis.

Required columns: one frequency column (`frequency_hz`, `frequency`, `freq_hz`, `freq`) and one level column (`level_db`, `spl_db`, `magnitude_db`, `db`).

Checks: numeric/finite values, frequency > 0, at least two points, duplicate frequencies, strictly increasing order.

Inputs are local-only and must reside under `data/` or `.aeris/imports/`. No cloud call is permitted.

A PASS means the file passed this import/schema/order validation only; it does not prove fixture, calibration, environmental condition, channel mapping, or measurement correctness.
