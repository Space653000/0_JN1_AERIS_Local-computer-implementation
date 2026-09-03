"""Bounded SI-unit engineering methods, independent of LLM output."""
from __future__ import annotations

import itertools
import math
from typing import Any

import numpy as np
from scipy import signal, stats


def scalar(p: dict, key: str, low: float | None = None, high: float | None = None) -> float:
    value = p[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{key}: finite numeric value required")
    if low is not None and value <= low or high is not None and value > high:
        raise ValueError(f"{key}: outside method applicability")
    return float(value)


def vector(p: dict, key: str, minimum: int = 2, maximum: int = 262144) -> np.ndarray:
    raw = p[key]
    if not isinstance(raw, list) or not minimum <= len(raw) <= maximum:
        raise ValueError(f"{key}: requires {minimum}..{maximum} values")
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) for x in raw):
        raise ValueError(f"{key}: numeric vector required")
    arr = np.asarray(raw, dtype=float)
    if not np.isfinite(arr).all():
        raise ValueError(f"{key}: nonfinite values")
    return arr


def paired(p: dict, x: str, y: str, minimum: int = 2) -> tuple[np.ndarray, np.ndarray]:
    a, b = vector(p, x, minimum), vector(p, y, minimum)
    if a.shape != b.shape:
        raise ValueError("paired data lengths differ")
    return a, b


def rms(a: np.ndarray) -> float:
    return float(np.sqrt(np.mean(a*a)))


def db_ratio(a: float, b: float, multiplier: int = 20) -> float | None:
    return float(multiplier * np.log10(a / b)) if a > 0 and b > 0 else None


def spectral(p: dict) -> dict:
    x = vector(p, "samples", 8)
    fs = scalar(p, "sample_rate_hz", 0)
    window = p.get("window", "rectangular")
    if window not in {"rectangular", "hann", "hamming"}:
        raise ValueError("unsupported window")
    w = np.ones(len(x)) if window == "rectangular" else signal.get_window(window, len(x), fftbins=True)
    z = np.fft.rfft(x*w)
    amp = abs(z) / sum(w)
    amp[1:-1 if len(x) % 2 == 0 else None] *= 2
    return {"frequency_hz": np.fft.rfftfreq(len(x), 1/fs), "amplitude": amp,
            "phase_rad": np.angle(z), "fft_real": z.real, "fft_imag": z.imag,
            "ifft_reconstructed_windowed_samples": np.fft.irfft(z, n=len(x)),
            "window_coherent_gain": float(np.mean(w)), "rms": rms(x)}


def response(p: dict) -> dict:
    f, mag = paired(p, "frequency_hz", "magnitude_db", 3)
    phase = vector(p, "phase_rad", 3)
    if len(phase) != len(f) or np.any(np.diff(f) <= 0) or np.any(f <= 0):
        raise ValueError("positive increasing frequencies and matching phase required")
    phase = np.unwrap(phase)
    octave = float(p.get("smoothing_octaves", 0))
    if not 0 <= octave <= 1:
        raise ValueError("smoothing_octaves outside [0,1]")
    smooth = np.array([np.mean(mag[abs(np.log2(f/center)) <= octave/2 + 1e-12]) for center in f])
    return {"frequency_hz": f, "smoothed_db": smooth, "unwrapped_phase_rad": phase,
            "group_delay_s": -np.gradient(phase, 2*np.pi*f), "ripple_db": float(np.ptp(mag))}


def distortion(p: dict) -> dict:
    x = vector(p, "samples", 32)
    fs, f0 = scalar(p, "sample_rate_hz", 0), scalar(p, "fundamental_hz", 0)
    harmonics = int(p.get("harmonics", 5))
    if not 1 <= harmonics <= 20 or f0*harmonics >= fs/2 or len(x)*f0/fs < 3:
        raise ValueError("at least 3 periods and harmonics strictly below Nyquist required")
    t = np.arange(len(x))/fs
    columns = [np.ones(len(x))]
    for h in range(1, harmonics+1):
        columns += [np.sin(2*np.pi*h*f0*t), np.cos(2*np.pi*h*f0*t)]
    design = np.column_stack(columns)
    coeff, _, rank, _ = np.linalg.lstsq(design, x, rcond=None)
    if rank != design.shape[1]:
        raise ValueError("harmonic fit is rank deficient")
    amplitudes = np.hypot(coeff[1::2], coeff[2::2])
    if amplitudes[0] <= 1e-12:
        raise ValueError("fundamental absent")
    fundamental = design[:, 1:3] @ coeff[1:3]
    residual = x - design @ coeff
    dn = x - coeff[0] - fundamental
    return {"harmonic_peak_amplitudes": amplitudes, "thd_ratio": float(np.linalg.norm(amplitudes[1:])/amplitudes[0]),
            "thdn_ratio": rms(dn)/rms(fundamental), "noise_rms": rms(residual),
            "snr_db": db_ratio(rms(fundamental), rms(residual)), "dc": float(coeff[0])}


def time_frequency(p: dict) -> dict:
    x = vector(p, "samples", 32)
    fs = scalar(p, "sample_rate_hz", 0)
    n = int(p.get("segment_samples", min(256, len(x))))
    if not 16 <= n <= len(x):
        raise ValueError("invalid segment_samples")
    f, psd = signal.welch(x, fs, nperseg=n, detrend=False)
    _, t, stft = signal.stft(x, fs, nperseg=n, boundary=None, padded=False)
    return {"frequency_hz": f, "psd_unit2_per_hz": psd, "time_s": t,
            "stft_real": stft.real, "stft_imag": stft.imag, "spectrogram_power": abs(stft)**2,
            "integrated_power": float(np.sum(psd)*(fs/n))}


def transfer(p: dict) -> dict:
    x, y = paired(p, "reference", "response", 64)
    fs = scalar(p, "sample_rate_hz", 0)
    if rms(x) <= 1e-12:
        raise ValueError("reference has no excitation")
    n = min(256, len(x)//2)
    f, pxx = signal.welch(x, fs, nperseg=n, detrend=False)
    _, pyy = signal.welch(y, fs, nperseg=n, detrend=False)
    _, pxy = signal.csd(x, y, fs, nperseg=n, detrend=False)
    valid = pxx > np.max(pxx)*1e-10
    h = pxy[valid]/pxx[valid]
    coherence = abs(pxy[valid])**2/np.maximum(pxx[valid]*pyy[valid], 1e-300)
    return {"frequency_hz": f[valid], "transfer_real": h.real, "transfer_imag": h.imag,
            "coherence": np.clip(coherence, 0, 1), "unexcited_bins_excluded": int(sum(~valid))}


def octave_bands(p: dict) -> dict:
    x = vector(p, "samples", 64)
    fs = scalar(p, "sample_rate_hz", 0)
    fraction = int(p.get("fraction", 3))
    if fraction not in {1, 3, 6, 12}:
        raise ValueError("supported fractions: 1,3,6,12")
    f, psd = signal.periodogram(x, fs, detrend=False)
    centers, power = [], []
    for k in range(-12*fraction, 6*fraction+1):
        center = 1000*2**(k/fraction)
        lo, hi = center/2**(1/(2*fraction)), center*2**(1/(2*fraction))
        mask = (f >= lo) & (f < hi)
        if hi <= fs/2 and sum(mask) >= 1:
            centers.append(center)
            power.append(float(sum(psd[mask])*fs/len(x)))
    return {"centers_hz": centers, "band_power_unit2": power, "fraction": fraction,
            "method_note": "FFT-bin integration; not a certified IEC filterbank"}


def weighting(p: dict) -> dict:
    x = vector(p, "samples", 16)
    fs = scalar(p, "sample_rate_hz", 2000)
    mode = p.get("weighting", "A")
    if mode not in {"A", "C", "Z"}:
        raise ValueError("weighting must be A, C or Z")
    if mode == "Z":
        y = x
    else:
        poles = -2*np.pi*np.array([20.598997,20.598997,12194.217,12194.217] + ([107.65265,737.86223] if mode == "A" else []))
        z, poles, gain = signal.bilinear_zpk(np.zeros(4 if mode == "A" else 2), poles, 1, fs)
        sos = signal.zpk2sos(z,poles,gain)
        _, h = signal.sosfreqz(sos, worN=[1000], fs=fs)
        sos[0,:3] /= abs(h[0])
        y = signal.sosfilt(sos,x)
    return {"weighted_samples": y, "rms": rms(y), "weighting": mode,
            "transient_policy": "causal zero-state; caller must exclude startup settling for level acceptance"}


def sensitivity(p: dict) -> dict:
    sensitivity_mv = scalar(p, "sensitivity_mv_per_pa", 0)
    noise_v = scalar(p, "noise_rms_v", 0)
    signal_v = scalar(p, "signal_rms_v", 0)
    vpa = sensitivity_mv/1000
    return {"sensitivity_dbv_per_pa": 20*np.log10(vpa), "equivalent_noise_spl_db": 20*np.log10(noise_v/vpa/20e-6),
            "signal_spl_db": 20*np.log10(signal_v/vpa/20e-6), "snr_db": 20*np.log10(signal_v/noise_v),
            "calibration_status": "USER_SUPPLIED_MODEL_NOT_CALIBRATED"}


def uncertainty(p: dict) -> dict:
    s, u = paired(p, "sensitivity_coefficients", "standard_uncertainties", 1)
    if len(s)>64: raise ValueError("uncertainty model is limited to 64 contributors")
    if np.any(u < 0):
        raise ValueError("uncertainties must be nonnegative")
    corr = np.asarray(p.get("correlation_matrix", np.eye(len(s))), dtype=float)
    if corr.shape != (len(s),len(s)) or not np.isfinite(corr).all() or not np.allclose(corr,corr.T) or not np.allclose(np.diag(corr),1) or np.min(np.linalg.eigvalsh(corr)) < -1e-10:
        raise ValueError("correlation matrix must be symmetric positive semidefinite with unit diagonal")
    combined = math.sqrt(max(0,float((s*u) @ corr @ (s*u))))
    k = scalar(p, "coverage_factor", 0)
    return {"combined_standard_uncertainty": combined, "expanded_uncertainty": k*combined,
            "coverage_factor": k, "coverage_probability": "not inferred without distribution and degrees of freedom"}


def repeatability(p: dict) -> dict:
    groups = [vector({"x": g}, "x", 2) for g in p["groups"]]
    if not 2 <= len(groups) <= 100 or len({len(g) for g in groups}) != 1:
        raise ValueError("balanced replicated groups required")
    a = np.array(groups); n=a.shape[1]
    within=float(np.mean(np.var(a,axis=1,ddof=1)))
    between=max(0,float(np.var(np.mean(a,axis=1),ddof=1)-within/n))
    return {"mean": float(a.mean()), "repeatability_sd": math.sqrt(within),
            "between_group_sd": math.sqrt(between), "reproducibility_sd": math.sqrt(within+between),
            "group_count": len(groups), "replicates_per_group": n}


def doe(p: dict) -> dict:
    factors=p["factors"]
    if not isinstance(factors,dict) or not 1 <= len(factors) <= 8:
        raise ValueError("1..8 named factors required")
    for bounds in factors.values():
        if not isinstance(bounds,list) or len(bounds)!=2 or not all(isinstance(v,(float,int)) and math.isfinite(v) for v in bounds) or bounds[0]>=bounds[1]:
            raise ValueError("each factor needs ascending numeric bounds")
    coded=np.array(list(itertools.product([-1,1],repeat=len(factors))))
    runs=[dict(zip(factors,[factors[k][int(v>0)] for k,v in zip(factors,row)])) for row in coded]
    effects={}
    if "responses" in p:
        y=vector(p,"responses")
        if len(y)!=len(runs): raise ValueError("response count does not match factorial design")
        effects={k:float(y[coded[:,i]>0].mean()-y[coded[:,i]<0].mean()) for i,k in enumerate(factors)}
    return {"runs":runs,"main_effects":effects,"run_order":"lexicographic; randomize actual experiments independently"}


def monte_carlo(p: dict) -> dict:
    means, stds=paired(p,"means","standard_deviations",1)
    if len(means)>64: raise ValueError("Monte Carlo is limited to 64 independent inputs")
    coefficients=vector(p,"coefficients",1)
    count=int(p.get("trials",10000)); seed=int(p.get("seed",0))
    if len(coefficients)!=len(means) or np.any(stds<0) or not 1000<=count<=100000:
        raise ValueError("invalid independent-normal Monte Carlo specification")
    y=np.random.default_rng(seed).normal(means,stds,size=(count,len(means))) @ coefficients
    return {"mean":float(y.mean()),"standard_deviation":float(y.std(ddof=1)),
            "interval_95":np.quantile(y,[.025,.975]),"seed":seed,"trials":count,
            "analytic_mean":float(means@coefficients),"analytic_sd":float(np.linalg.norm(stds*coefficients))}


def association(p: dict) -> dict:
    x,y=paired(p,"x","y",3)
    if np.ptp(x)==0 or np.ptp(y)==0: raise ValueError("nonconstant pairs required")
    slope,intercept,r,pvalue,stderr=stats.linregress(x,y)
    med=np.median(y); mad=np.median(abs(y-med))
    outliers=np.flatnonzero(abs(y-med)> (3.5*mad/.67448975 if mad>0 else 0)).tolist()
    return {"slope":slope,"intercept":intercept,"pearson_r":r,"p_value":pvalue,
            "slope_standard_error":stderr,"outlier_indices":outliers,"deletion_performed":False,
            "causality_claimed":False}


def speaker_model(p: dict) -> dict:
    m=scalar(p,"moving_mass_kg",0); c=scalar(p,"compliance_m_per_n",0)
    r=scalar(p,"mechanical_resistance_ns_per_m",0); bl=scalar(p,"force_factor_n_per_a",0)
    re=scalar(p,"dc_resistance_ohm",0); sd=scalar(p,"diaphragm_area_m2",0)
    f=vector(p,"frequency_hz",3)
    if np.any(f<=0) or np.any(np.diff(f)<=0): raise ValueError("frequencies must increase above zero")
    w=2*np.pi*f; fs=1/(2*np.pi*np.sqrt(m*c)); w0=2*np.pi*fs
    zm=r+1j*(w*m-1/(w*c)); z=re+bl*bl/zm
    qms=w0*m/r; qes=w0*m*re/bl**2
    vas=1.204*343**2*sd**2*c
    vb=scalar(p,"box_volume_m3",0); voltage=scalar(p,"voltage_rms_v",0); xmax=scalar(p,"xmax_m",0)
    current=voltage/z; excursion=abs(bl*current/zm/w)*np.sqrt(2)
    return {"fs_hz":float(fs),"qms":float(qms),"qes":float(qes),"qts":float(1/(1/qms+1/qes)),
            "vas_m3":float(vas),"sealed_fc_hz":float(fs*np.sqrt(1+vas/vb)),
            "impedance_real_ohm":z.real,"impedance_imag_ohm":z.imag,
            "free_air_excursion_peak_m":excursion,"free_air_excursion_within_limit":bool(max(excursion)<=xmax),
            "voicecoil_power_w":abs(current)**2*re,"limitations":"linear small-signal free-air model; no inductance, thermal compression or nonlinear validation"}


def port_model(p: dict) -> dict:
    area=scalar(p,"area_m2",0); length=scalar(p,"effective_length_m",0); volume=scalar(p,"volume_m3",0)
    c=scalar(p,"sound_speed_m_s",0)
    return {"helmholtz_hz":c/(2*np.pi)*np.sqrt(area/(length*volume)),"end_correction":"effective length supplied by caller"}


def array_pattern(p: dict) -> dict:
    positions=vector(p,"positions_m",2,64)
    if np.any(np.diff(positions)<=0): raise ValueError("ordered unique linear array positions required")
    freq=scalar(p,"frequency_hz",0); c=scalar(p,"sound_speed_m_s",0)
    steer=scalar(p,"steering_deg",-90.00001,90)
    angles=np.linspace(-90,90,361); directions=np.sin(np.deg2rad(angles))
    phase=2*np.pi*freq/c*np.outer(directions-np.sin(np.deg2rad(steer)),positions)
    power=abs(np.mean(np.exp(1j*phase),axis=1))**2
    u=np.linspace(-1,1,2001)
    sphere_power=abs(np.mean(np.exp(2j*np.pi*freq/c*np.outer(u-np.sin(np.deg2rad(steer)),positions)),axis=1))**2
    return {"angles_deg":angles,"normalized_power":power,"directivity_index_db":-10*np.log10(np.trapezoid(sphere_power,u)/2),
            "alias_free_spacing":bool(max(np.diff(positions))<=c/(2*freq)),"aperture_m":float(np.ptp(positions)),
            "model":"far-field point sensors, linear array, omnidirectional elements"}


def tdoa(p: dict) -> dict:
    x,y=paired(p,"reference","delayed",32)
    fs=scalar(p,"sample_rate_hz",0); d=scalar(p,"spacing_m",0); c=scalar(p,"sound_speed_m_s",0)
    if rms(x)==0 or rms(y)==0: raise ValueError("silent channels")
    n=2**int(np.ceil(np.log2(2*len(x)-1)))
    spectrum=np.fft.rfft(y,n)*np.conj(np.fft.rfft(x,n))
    corr=np.fft.fftshift(np.fft.irfft(spectrum/np.maximum(abs(spectrum),1e-20),n))
    lags=np.arange(-n//2,n//2); maxlag=int(np.floor(d/c*fs))
    if maxlag<1: raise ValueError("spacing below one-sample TDOA resolution")
    mask=abs(lags)<=maxlag; lag=int(lags[mask][np.argmax(corr[mask])]); tau=lag/fs
    return {"delay_samples":lag,"tdoa_s":tau,"doa_deg":float(np.rad2deg(np.arcsin(np.clip(tau*c/d,-1,1)))),
            "time_resolution_s":1/fs,"ambiguity":"front/back unresolved with a linear two-sensor array"}


def beamform(p: dict) -> dict:
    positions=vector(p,"positions_m",2,64)
    channels=np.array([vector({"x":v},"x",32) for v in p["channels"]])
    if len(channels)!=len(positions) or np.any(np.diff(positions)<=0): raise ValueError("channel/ordered position mismatch")
    fs=scalar(p,"sample_rate_hz",0); c=scalar(p,"sound_speed_m_s",0); angle=scalar(p,"steering_deg",-90.0001,90)
    delays=(positions-positions[0])*np.sin(np.deg2rad(angle))/c*fs
    indices=np.arange(channels.shape[1]); valid=(indices+min(delays)>=0)&(indices+max(delays)<=len(indices)-1)
    if valid.sum()<16: raise ValueError("insufficient overlapping samples after steering")
    y=np.mean([np.interp(indices[valid]+delay,indices,ch) for delay,ch in zip(delays,channels)],axis=0)
    return {"samples":y,"steering_delays_samples":delays,"valid_start_sample":int(np.flatnonzero(valid)[0]),"rms":rms(y)}


def enhancement(p: dict) -> dict:
    clean,processed=paired(p,"clean","processed",16)
    if rms(clean)<=1e-12: raise ValueError("clean reference is silent")
    centered=clean-clean.mean(); estimate=processed-processed.mean()
    if np.dot(centered,centered)<=1e-20: raise ValueError("constant clean reference")
    target=np.dot(estimate,centered)/np.dot(centered,centered)*centered
    residual=estimate-target
    result={"si_sdr_db":db_ratio(rms(target),rms(residual)),"rmse":rms(processed-clean),"mos_claimed":False}
    if "echo_before" in p:
        before,after=paired(p,"echo_before","echo_after",16)
        if p.get("far_end_only") is not True: raise ValueError("ERLE requires declared far-end-only interval")
        result["erle_db"]=db_ratio(rms(before),rms(after))
    return result


def room_ir(p: dict) -> dict:
    ir=vector(p,"impulse_response",64); fs=scalar(p,"sample_rate_hz",0)
    energy=ir*ir
    if sum(energy)<=1e-20: raise ValueError("silent IR")
    peak=int(np.argmax(abs(ir))); energy=energy[peak:]
    decay=np.cumsum(energy[::-1])[::-1]; level=10*np.log10(np.maximum(decay/decay[0],1e-300)); t=np.arange(len(energy))/fs
    noise_floor=scalar(p,"usable_decay_db",0,120)
    result={"direct_arrival_sample":peak,"method":"Schroeder backward integration; usable decay supplied, no noise compensation"}
    for name,low,high in (("edt_s",0,10),("t20_s",5,25),("t30_s",5,35)):
        mask=(level<=-low)&(level>=-high)
        if noise_floor<high+10 or mask.sum()<10:
            result[name]=None
            continue
        fit=stats.linregress(t[mask],level[mask])
        result[name]=float(-60/fit.slope) if fit.slope<0 and fit.rvalue**2>=.95 else None
    for ms in (50,80):
        split=int(ms/1000*fs); result[f"c{ms}_db"]=db_ratio(float(sum(energy[:split])),float(sum(energy[split:])),10)
    return result


def psychoacoustic(p: dict) -> dict:
    f, power=paired(p,"frequency_hz","power",2)
    if np.any(f<0) or np.any(power<0) or sum(power)<=0: raise ValueError("positive spectrum required")
    bark=13*np.arctan(.00076*f)+3.5*np.arctan((f/7500)**2)
    return {"bark_positions":bark,"spectral_centroid_hz":float(f@power/sum(power)),
            "bark_centroid":float(bark@power/sum(power)),"subjective_loudness_or_mos_verified":False}


def nvh(p: dict) -> dict:
    a=vector(p,"acceleration_m_s2",16); fs=scalar(p,"sample_rate_hz",0)
    f=np.fft.rfftfreq(len(a),1/fs); z=np.fft.rfft(a-a.mean()); v=np.zeros_like(z); displacement=np.zeros_like(z)
    v[1:]=z[1:]/(2j*np.pi*f[1:]); displacement[1:]=v[1:]/(2j*np.pi*f[1:])
    return {"velocity_rms_m_s":rms(np.fft.irfft(v,n=len(a))),"displacement_rms_m":rms(np.fft.irfft(displacement,n=len(a))),
            "acceleration_rms_m_s2":rms(a-a.mean()),"dc_removed":True,"assumption":"periodic record; no drift reconstruction"}


def porous(p: dict) -> dict:
    f=vector(p,"frequency_hz",2); sigma=scalar(p,"flow_resistivity_pa_s_m2",0); thickness=scalar(p,"thickness_m",0)
    x=1.204*f/sigma
    if np.any((x<.01)|(x>1)): raise ValueError("Delany-Bazley applicability requires 0.01 <= rho*f/sigma <= 1")
    zc=1.204*343*(1+.0571*x**-.754-1j*.087*x**-.732)
    kc=2*np.pi*f/343*(1+.0978*x**-.700-1j*.189*x**-.595)
    zin=-1j*zc/np.tan(kc*thickness); reflection=(zin-1.204*343)/(zin+1.204*343)
    return {"absorption_normal_incidence":1-abs(reflection)**2,"model":"Delany-Bazley homogeneous fibrous layer, rigid backing; not measured material data"}


def thermal(p: dict) -> dict:
    power=scalar(p,"power_w",0); resistance=scalar(p,"thermal_resistance_k_w",0); capacity=scalar(p,"thermal_capacity_j_k",0)
    ambient=scalar(p,"ambient_c",-273.15); limit=scalar(p,"limit_c",-273.15); t=vector(p,"time_s",2)
    if np.any(t<0): raise ValueError("time cannot be negative")
    temp=ambient+power*resistance*(1-np.exp(-t/(resistance*capacity)))
    return {"temperature_c":temp,"steady_temperature_c":ambient+power*resistance,
            "within_limit":bool(max(temp)<=limit),"time_constant_s":resistance*capacity,"model":"single thermal RC, constant input power"}


def leakage(p: dict) -> dict:
    radius=scalar(p,"radius_m",0); length=scalar(p,"length_m",0); viscosity=scalar(p,"viscosity_pa_s",0)
    ur=scalar(p,"radius_standard_uncertainty_m",-1e-30)
    if ur>=radius/4: raise ValueError("linearized radius uncertainty too large")
    r=8*viscosity*length/(np.pi*radius**4)
    return {"flow_resistance_pa_s_m3":r,"standard_uncertainty_pa_s_m3":4*r*ur/radius,
            "assumption":"laminar incompressible low-frequency circular leak; inertance and turbulent flow excluded"}


def latency(p: dict) -> dict:
    fs=scalar(p,"sample_rate_hz",0); buffers=vector(p,"buffer_samples",1)
    stages=vector(p,"other_stage_ms",1); ppm=scalar(p,"clock_difference_ppm",-1e-30)
    if np.any(buffers<0) or np.any(stages<0): raise ValueError("latency stages cannot be negative")
    return {"serial_latency_ms":float(sum(buffers)/fs*1000+sum(stages)),"uncompensated_drift_ms_per_hour":ppm*3.6,
            "measured_latency":False,"assumption":"serial nonoverlapping stages; wireless scheduling supplied by caller"}


def local_ml(p: dict) -> dict:
    x=np.asarray(p["train_features"],dtype=float); v=np.asarray(p["validation_features"],dtype=float)
    y=vector(p,"train_targets",3); target=vector(p,"validation_targets",2)
    if x.ndim!=2 or v.ndim!=2 or x.shape[1]!=v.shape[1] or len(x)!=len(y) or len(v)!=len(target) or x.shape[1]>64 or not np.isfinite(x).all() or not np.isfinite(v).all(): raise ValueError("invalid train/validation arrays")
    if set(p["train_ids"]) & set(p["validation_ids"]) or len(p["train_ids"])!=len(x) or len(p["validation_ids"])!=len(v): raise ValueError("train/validation identity leakage")
    ridge=scalar(p,"ridge",0); mean=x.mean(axis=0); scale=x.std(axis=0); scale[scale==0]=1
    a=np.column_stack([np.ones(len(x)),(x-mean)/scale]); av=np.column_stack([np.ones(len(v)),(v-mean)/scale])
    penalty=np.eye(a.shape[1])*ridge; penalty[0,0]=0
    weights=np.linalg.solve(a.T@a+penalty,a.T@y); predicted=av@weights
    return {"predictions":predicted,"validation_rmse":rms(predicted-target),"training_only_scaler_mean":mean,
            "method":"ridge regression on supplied acoustic features; no general perceptual or clinical validity"}


def filtering(p: dict) -> dict:
    x=vector(p,"samples",32); fs=scalar(p,"sample_rate_hz",0)
    cutoff=vector(p,"cutoff_hz",1,2); order=int(p.get("order",4)); kind=p.get("kind","lowpass")
    if kind not in {"lowpass","highpass","bandpass","bandstop"} or not 1<=order<=8 or np.any(cutoff<=0) or np.any(cutoff>=fs/2):
        raise ValueError("invalid Butterworth filter contract")
    if len(cutoff)!=(2 if kind.startswith("band") else 1) or len(cutoff)==2 and cutoff[0]>=cutoff[1]: raise ValueError("cutoff count/order mismatch")
    sos=signal.butter(order,cutoff if len(cutoff)==2 else cutoff[0],btype=kind,fs=fs,output="sos")
    y=signal.sosfilt(sos,x)
    return {"filtered_samples":y,"sos":sos,"output_rms":rms(y),"startup_state":"zero; causal phase and settling retained"}


def level_statistics(p: dict) -> dict:
    levels=vector(p,"levels_db",2); durations=vector(p,"durations_s",2)
    if len(levels)!=len(durations) or np.any(durations<=0): raise ValueError("matching positive durations required")
    order=np.argsort(levels); cumulative=np.cumsum(durations[order])/sum(durations)
    def exceedance(percent): return float(levels[order][np.searchsorted(cumulative,1-percent/100)])
    maximum=float(max(levels))
    leq=maximum+10*np.log10(np.average(10**((levels-maximum)/10),weights=durations))
    return {"leq_db":float(leq),"l10_db":exceedance(10),"l50_db":exceedance(50),"l90_db":exceedance(90),"duration_s":float(sum(durations))}


def resonance(p: dict) -> dict:
    f,a=paired(p,"frequency_hz","amplitude",5)
    if np.any(np.diff(f)<=0) or np.any(f<=0) or np.any(a<0): raise ValueError("ordered positive frequencies and nonnegative amplitudes required")
    peak=int(np.argmax(a)); threshold=a[peak]/np.sqrt(2)
    left=np.flatnonzero(a[:peak]<=threshold); right=np.flatnonzero(a[peak+1:]<=threshold)+peak+1
    if not len(left) or not len(right) or a[peak]<=0: raise ValueError("resonance peak must have both half-power crossings in measured band")
    li=int(left[-1]); ri=int(right[0]); f1=float(np.interp(threshold,a[li:li+2],f[li:li+2])); f2=float(np.interp(threshold,a[ri-1:ri+1][::-1],f[ri-1:ri+1][::-1]))
    return {"peak_frequency_hz":float(f[peak]),"half_power_bandwidth_hz":f2-f1,"q_estimate":float(f[peak]/(f2-f1)),
            "frequency_grid_resolution_hz":float(max(np.diff(f))),"method":"isolated amplitude resonance, linear interpolation; not nonlinear T/S identification"}


def circuit_noise(p: dict) -> dict:
    resistance=scalar(p,"resistance_ohm",0); temp=scalar(p,"temperature_k",0); bw=scalar(p,"bandwidth_hz",0)
    density=scalar(p,"amplifier_noise_v_per_sqrt_hz",-1e-30); fullscale=scalar(p,"adc_fullscale_v",0)
    bits=int(scalar(p,"adc_bits",0,32)); f=scalar(p,"signal_frequency_hz",0); jitter=scalar(p,"jitter_rms_s",0)
    thermal=math.sqrt(4*1.380649e-23*temp*resistance*bw); quant=fullscale/(2**bits*math.sqrt(12))
    return {"johnson_noise_rms_v":thermal,"quantization_rms_v":quant,
            "input_noise_rss_v":math.sqrt(thermal**2+density**2*bw+quant**2),"jitter_snr_limit_db":-20*math.log10(2*math.pi*f*jitter),
            "assumption":"white uncorrelated noise, full-scale peak-to-peak ADC range, ideal quantizer"}


HANDLERS = {
    "butterworth-filter":filtering,"level-statistics":level_statistics,"resonance-characterization":resonance,"circuit-noise-budget":circuit_noise,
    "spectral-analysis":spectral,"response-phase-delay":response,"harmonic-noise-analysis":distortion,
    "time-frequency-analysis":time_frequency,"transfer-coherence":transfer,"fractional-octave":octave_bands,
    "frequency-weighting":weighting,"microphone-sensitivity":sensitivity,"uncertainty-propagation":uncertainty,
    "repeatability-reproducibility":repeatability,"factorial-doe":doe,"monte-carlo":monte_carlo,
    "correlation-outliers":association,"lumped-speaker":speaker_model,"helmholtz-port":port_model,
    "linear-array-pattern":array_pattern,"gcc-phat-tdoa":tdoa,"delay-sum-beamforming":beamform,
    "enhancement-aec-metrics":enhancement,"room-ir-decay":room_ir,"psychoacoustic-descriptors":psychoacoustic,
    "nvh-integration":nvh,"porous-absorption":porous,"thermal-rc":thermal,"leakage-tolerance":leakage,
    "latency-budget":latency,"local-audio-regression":local_ml,
}
