"""Dependency-free deterministic acoustic analysis baseline.

This is a local engineering baseline, not a substitute for calibrated licensed
professional instruments. Results retain that truth label in every response.
"""
from __future__ import annotations

import cmath
import math
from typing import Any

MAX_SAMPLES = 8192


def _samples(value: Any, name: str = "samples") -> list[float]:
    if not isinstance(value, list) or len(value) < 8 or len(value) > MAX_SAMPLES:
        raise ValueError(f"{name} must contain 8..{MAX_SAMPLES} numeric samples")
    result = [float(x) for x in value]
    if any(not math.isfinite(x) for x in result):
        raise ValueError(f"{name} contains non-finite values")
    return result


def _sample_rate(value: Any) -> float:
    rate = float(value)
    if not math.isfinite(rate) or rate <= 0:
        raise ValueError("sample_rate_hz must be positive")
    return rate


def _fft(values: list[complex]) -> list[complex]:
    n = len(values)
    if n == 1:
        return values
    if n % 2:
        return [sum(x * cmath.exp(-2j * math.pi * k * i / n) for i, x in enumerate(values)) for k in range(n)]
    even, odd = _fft(values[0::2]), _fft(values[1::2])
    factors = [cmath.exp(-2j * math.pi * k / n) * odd[k] for k in range(n // 2)]
    return [even[k] + factors[k] for k in range(n // 2)] + [even[k] - factors[k] for k in range(n // 2)]


def _spectrum(samples: list[float], rate: float) -> tuple[list[float], list[complex]]:
    n = len(samples)
    window = [0.5 - 0.5 * math.cos(2 * math.pi * i / (n - 1)) for i in range(n)]
    scale = sum(window) or 1.0
    bins = _fft([complex(x * w, 0) for x, w in zip(samples, window)])[: n // 2 + 1]
    bins = [x / scale * 2 for x in bins]
    return [i * rate / n for i in range(len(bins))], bins


def _rms(values: list[float]) -> float:
    return math.sqrt(sum(x * x for x in values) / len(values))


def _svg(freqs: list[float], levels: list[float]) -> str:
    if not levels:
        return "<svg xmlns='http://www.w3.org/2000/svg' width='640' height='240'/>"
    lo, hi = min(levels), max(levels)
    span = hi - lo or 1.0
    points = " ".join(f"{20+i*600/max(1,len(levels)-1):.2f},{210-(v-lo)*180/span:.2f}" for i, v in enumerate(levels))
    return f"<svg xmlns='http://www.w3.org/2000/svg' width='640' height='240' viewBox='0 0 640 240'><rect width='640' height='240' fill='#111314'/><polyline fill='none' stroke='#72d0c5' stroke-width='2' points='{points}'/><text x='20' y='230' fill='#b6bcc1' font-size='11'>FREE_BASELINE spectrum {freqs[0]:.1f}..{freqs[-1]:.1f} Hz</text></svg>"


def analyze(params: dict[str, Any]) -> dict[str, Any]:
    samples = _samples(params.get("samples"))
    rate = _sample_rate(params.get("sample_rate_hz"))
    freqs, bins = _spectrum(samples, rate)
    mags = [abs(x) for x in bins]
    levels = [20 * math.log10(max(x, 1e-15)) for x in mags]
    fundamental_hz = float(params.get("fundamental_hz") or freqs[max(range(1, len(mags)), key=lambda i: mags[i])])
    if fundamental_hz <= 0 or fundamental_hz >= rate / 2:
        raise ValueError("fundamental_hz must be within (0, Nyquist)")
    fundamental_bin = min(range(1, len(freqs)), key=lambda i: abs(freqs[i] - fundamental_hz))
    harmonic_bins = [min(range(1, len(freqs)), key=lambda i, h=h: abs(freqs[i] - fundamental_hz * h)) for h in range(2, 6) if fundamental_hz * h < rate / 2]
    thd = math.sqrt(sum(mags[i] ** 2 for i in harmonic_bins)) / max(mags[fundamental_bin], 1e-15)
    excluded = {0, fundamental_bin, *harmonic_bins}
    noise_rms = math.sqrt(sum(mags[i] ** 2 for i in range(len(mags)) if i not in excluded) / max(1, len(mags) - len(excluded)))
    snr = 20 * math.log10(max(mags[fundamental_bin], 1e-15) / max(noise_rms, 1e-15))
    reference_pa = float(params.get("reference_pa", 20e-6))
    calibration_pa_per_unit = float(params.get("calibration_pa_per_unit", 1.0))
    if reference_pa <= 0 or calibration_pa_per_unit <= 0:
        raise ValueError("SPL calibration values must be positive")
    spl = 20 * math.log10(max(_rms(samples) * calibration_pa_per_unit, 1e-15) / reference_pa)

    # IEC-style nominal fractional-octave centers; deterministic aggregation baseline.
    fraction = int(params.get("octave_fraction", 3))
    if fraction not in {1, 3}:
        raise ValueError("octave_fraction must be 1 or 3")
    centers, center = [], 31.5
    ratio = 2 ** (1 / fraction)
    while center <= rate / 2:
        low, high = center / math.sqrt(ratio), center * math.sqrt(ratio)
        energy = [m * m for f, m in zip(freqs, mags) if low <= f < high]
        if energy:
            centers.append({"center_hz": round(center, 3), "level_db": round(10 * math.log10(max(sum(energy), 1e-30)), 6)})
        center *= ratio

    frame = min(256, 2 ** int(math.floor(math.log2(max(8, len(samples) // 2)))))
    hop = max(1, frame // 2)
    stft = []
    for start in range(0, len(samples) - frame + 1, hop):
        sf, sb = _spectrum(samples[start:start + frame], rate)
        peak = max(range(1, len(sb)), key=lambda i: abs(sb[i]))
        stft.append({"time_sec": round(start / rate, 8), "peak_hz": round(sf[peak], 6), "peak_db": round(20 * math.log10(max(abs(sb[peak]), 1e-15)), 6)})

    output: dict[str, Any] = {
        "skill_id": "free-local-acoustic-baseline", "result": "PASS", "evidence_class": "DETERMINISTIC_FREE_LOCAL_BASELINE", "capability_maturity": "FREE_BASELINE",
        "professional_verification": "NOT_CLAIMED", "sample_count": len(samples), "sample_rate_hz": rate,
        "fft": {"bin_hz": rate / len(samples), "peak_hz": freqs[fundamental_bin], "levels_db": [round(x, 6) for x in levels]},
        "frequency_response": [{"frequency_hz": round(f, 6), "level_db": round(v, 6)} for f, v in zip(freqs, levels)],
        "thd_percent": round(thd * 100, 6), "snr_db": round(snr, 6), "spl_db_re_20upa": round(spl, 6),
        "time_domain_samples": samples, "octave_fraction": fraction, "octave_bands": centers, "stft": stft,
        "deterministic_plot_svg": _svg(freqs, levels),
        "report": {"speaker_microphone_basic_analysis": "computed", "calibration_model": "linear_pa_per_input_unit", "limitations": ["No traceable microphone/calibrator certificate is implied", "No licensed professional tool correlation is implied"]},
    }
    input_kind = str(params.get("input_kind", "signal"))
    if input_kind not in {"signal", "impulse_response"}:
        raise ValueError("input_kind must be signal or impulse_response")
    if input_kind == "impulse_response":
        output["impulse_response"] = samples
        output["impulse_response_method"] = "caller-declared measured_or_simulated_ir_input; no deconvolution claimed"
    reference = params.get("reference_samples")
    if reference is not None:
        ref = _samples(reference, "reference_samples")
        if len(ref) != len(samples):
            raise ValueError("reference_samples length must match samples")
        _, rb = _spectrum(ref, rate)
        transfer = [b / r if abs(r) > 1e-15 else 0j for b, r in zip(bins, rb)]
        output["transfer_function"] = [{"frequency_hz": round(f, 6), "magnitude_db": round(20 * math.log10(max(abs(v), 1e-15)), 6), "phase_deg": round(math.degrees(cmath.phase(v)), 6)} for f, v in zip(freqs, transfer)]
        # Deterministic magnitude-squared coherence baseline across overlapping frames.
        cross=[0j]*(frame//2+1); auto_x=[0.0]*len(cross); auto_y=[0.0]*len(cross); segments=0
        for start in range(0, len(samples)-frame+1, hop):
            _, xb=_spectrum(ref[start:start+frame],rate); _, yb=_spectrum(samples[start:start+frame],rate); segments+=1
            for i,(x,y) in enumerate(zip(xb,yb)):
                cross[i]+=x.conjugate()*y;auto_x[i]+=abs(x)**2;auto_y[i]+=abs(y)**2
        output["coherence"]=[{"frequency_hz":round(i*rate/frame,6),"value":round(min(1.0,abs(cross[i])**2/max(auto_x[i]*auto_y[i],1e-30)),6)} for i in range(len(cross))]
        output["coherence_segments"]=segments
    cutoff = params.get("filter_cutoff_hz")
    if cutoff is not None:
        cutoff=float(cutoff)
        if not 0 < cutoff < rate/2: raise ValueError("filter_cutoff_hz must be below Nyquist")
        alpha=1-math.exp(-2*math.pi*cutoff/rate); low=[];state=samples[0]
        for value in samples: state+=alpha*(value-state);low.append(state)
        kind=str(params.get("filter_type","lowpass"))
        if kind not in {"lowpass","highpass"}: raise ValueError("filter_type must be lowpass or highpass")
        output["filtered_samples"]=[round(x,9) for x in (low if kind=="lowpass" else [a-b for a,b in zip(samples,low)])]
        output["filter"]={"type":kind,"cutoff_hz":cutoff,"model":"one-pole deterministic baseline"}
    return output
