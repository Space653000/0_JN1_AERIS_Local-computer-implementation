"""R040 independent full-complex FFT and interval/ambiguity review."""
import math
from scipy import fft
from .array_doa import validate
from .numerical_policy import ratio_at_least


def review(parameters, candidate):
    p=parameters
    validate(p)
    n=len(p['channel_1']); size=2**math.ceil(math.log2(2*n-1))
    x=[v-sum(p['channel_1'])/n for v in p['channel_1']]
    y=[v-sum(p['channel_2'])/n for v in p['channel_2']]
    if math.sqrt(sum(v*v for v in x))<=1e-12 or math.sqrt(sum(v*v for v in y))<=1e-12:
        raise ValueError('no nonconstant excitation')
    sx=fft.fft(x,size); sy=fft.fft(y,size)
    cross=[b*a.conjugate() for a,b in zip(sx,sy)]
    floor=max(max(abs(v) for v in cross)*1e-10,1e-24)
    frequencies=fft.fftfreq(size,1/p['sample_rate_hz'])
    supported=[p['band_low_hz']<=abs(f)<=p['band_high_hz'] and abs(v)>floor for f,v in zip(frequencies,cross)]
    active=sum(ok and f>0 for f,ok in zip(frequencies,supported))
    if active<p['minimum_active_bins']: raise ValueError('declared band insufficiently excited')
    normalized=[v/abs(v) if ok else 0j for v,ok in zip(cross,supported)]
    circular=fft.ifft(normalized).real
    by_lag={lag:float(circular[lag % size]) for lag in range(1-n,n)}
    peak=max(abs(v) for v in by_lag.values())
    tied=[lag for lag,v in by_lag.items() if abs(v)>=peak*(1-1e-10)]
    delay=min(tied)
    start=stop=delay
    while start-1 in by_lag and ratio_at_least(abs(by_lag[start-1])/peak,p['support_fraction']): start-=1
    while stop+1 in by_lag and ratio_at_least(abs(by_lag[stop+1])/peak,p['support_fraction']): stop+=1
    other=[abs(v) for lag,v in by_lag.items() if abs(lag-delay)>p['peak_exclusion_samples'] and not start<=lag<=stop]
    competitor=max(other,default=0.0)
    ratio=peak/competitor if competitor>1e-15 else None
    qualified=len(tied)==1 and stop-start+1<=p['maximum_support_width_samples'] and (ratio is None or ratio_at_least(ratio,p['minimum_peak_ratio']))
    polarity=by_lag[delay]>0
    extent=p['timing_bound_samples']+p['estimator_error_bound_samples']
    samples=[start-extent,stop+extent]
    speed_spacing=[c/d for c in (p['sound_speed_lower_m_s'],p['sound_speed_upper_m_s'])
                   for d in (p['spacing_lower_m'],p['spacing_upper_m'])]
    directions=[bound/p['sample_rate_hz']*factor for bound in samples for factor in speed_spacing]
    interval=[min(directions),max(directions)]
    physical=all(-1<=value<=1 for value in interval)
    alias=p['spacing_upper_m']<=p['sound_speed_lower_m_s']/(2*p['band_high_hz'])
    angle=[math.asin(value)*180/math.pi for value in interval] if physical and alias and polarity and qualified else None
    checks=[{'id':'POLARITY_CONSISTENCY','passed':polarity,'on_failure':'CHECK_CHANNEL_WIRING_AND_POLARITY'},
            {'id':'PEAK_IDENTIFIABILITY','passed':qualified,'on_failure':'ISOLATE_ARRIVAL_OR_IMPROVE_BAND_EXCITATION'},
            {'id':'ALIAS_FREE_DECLARED_BAND','passed':alias,'on_failure':'REVISE_APERTURE_OR_ANALYSIS_BAND'},
            {'id':'DIRECTION_INTERVAL_VALIDITY','passed':physical,'on_failure':'CHECK_GEOMETRY_CLOCK_AND_REFLECTION_PATH'}]
    revisions=[check['on_failure'] for check in checks if not check['passed']]
    expected={'delay_samples':delay,'tdoa_s':delay/p['sample_rate_hz'],
              'direction_cosine':delay*p['sound_speed_m_s']/(p['sample_rate_hz']*p['spacing_m']),
              'direction_cosine_interval':interval,'planar_angle_interval_deg':angle,
              'front_back_complement_interval_deg':None if angle is None else [180-angle[1],180-angle[0]],
              'peak_score':peak,'competing_peak_score':competitor,'peak_ratio':ratio,'peak_tie_count':len(tied),
              'peak_support_lags':[start,stop],'delay_interval_samples':samples,'active_bins':int(active),'fft_size':size,
              'peak_qualified':qualified,'polarity_consistent':polarity,'checks':checks,
              'disposition':'DESIGN_REVISION_REQUIRED' if revisions else 'BOUNDED_BASELINE_ACCEPT',
              'required_revisions':revisions,'next_discriminating_experiment':revisions[0] if revisions else 'SWAP_CHANNELS_AND_REPEAT_WITH_KNOWN_SOURCE_GEOMETRY',
              'counter_hypotheses':['channel order or timing bias rather than source motion','reflection rather than direct arrival',
                                    'spatial aliasing or weak excitation rather than a unique source direction'],
              'model_assumptions':['SYNCHRONIZED_LINEAR_PAIR_FAR_FIELD','SAME_POLARITY',
                                  'timing plus supplied estimator-error bound and selected lobe support are not confidence intervals'],
              'unique_3d_direction_verified':False,'calibration_verified':False,'physical_measurement_verified':False,
              'scope':'Two-sensor direction-cosine/planar ambiguity under supplied model bounds; not a complete beamformer',
              'unresolved':['front/back and 3D cone ambiguity','actual synchronized acquisition and array calibration',
                            'unverified estimator error bound and multipath applicability']}
    if not isinstance(candidate,dict) or set(candidate)!=set(expected): raise ValueError('complete array-domain assertions required')
    from .domain_review import _same_assertion
    disagreements=[{'field':key,'asserted':candidate[key],'expected':value} for key,value in expected.items()
                   if not _same_assertion(candidate[key],value)]
    return {'domain':'microphone-array-geometry','decision':'CHANGES_REQUIRED' if disagreements else 'BOUNDED_REVIEW_ACCEPT',
            'disagreements':disagreements,'observations':{'independent_path':'full-complex scipy FFT and extrema over speed/spacing ratios',
             'unresolved':'supplied estimator bound is not measured coverage; planar and cone ambiguities remain'},
            'human_approval':False,'role_l3_awarded':False,'scope':'bounded signal/geometry report consistency only'}
