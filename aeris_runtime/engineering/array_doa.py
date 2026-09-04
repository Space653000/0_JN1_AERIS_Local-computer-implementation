"""Bounded GCC-PHAT observations with explicit peak and geometry ambiguity."""
import math
import numpy as np
from .numerical_policy import ratio_at_least

SCALARS={
    'sample_rate_hz':(4000,192000),'band_low_hz':(1,90000),'band_high_hz':(2,95000),
    'spacing_m':(0.001,2),'spacing_lower_m':(0.001,2),'spacing_upper_m':(0.001,2),
    'sound_speed_m_s':(250,450),'sound_speed_lower_m_s':(250,450),'sound_speed_upper_m_s':(250,450),
    'timing_bound_samples':(0.5,64),'estimator_error_bound_samples':(0,64),
    'minimum_active_bins':(4,2048),'minimum_peak_ratio':(1.01,100),
    'support_fraction':(0.5,0.99),'peak_exclusion_samples':(1,64),'maximum_support_width_samples':(1,129),
}
INTEGERS={'minimum_active_bins','peak_exclusion_samples','maximum_support_width_samples'}
MODELS={'array_model':'SYNCHRONIZED_LINEAR_PAIR_FAR_FIELD','channel_polarity':'SAME_POLARITY'}
SPECTRAL_RELATIVE_FLOOR=1e-10
PEAK_TIE_RESOLUTION=1e-10


def validate(p):
    if not isinstance(p,dict) or set(p) != set(SCALARS)|set(MODELS)|{'channel_1','channel_2'}:
        raise ValueError('exact synchronized pair contract required')
    for key,(low,high) in SCALARS.items():
        v=p[key]
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not low <= v <= high:
            raise ValueError('invalid declared-unit value: '+key)
        if key in INTEGERS and not isinstance(v,int): raise ValueError('integer peak/bin count required')
    if any(p[key] != value for key,value in MODELS.items()):
        raise ValueError('unsupported geometry, synchronization or polarity assumption')
    if not p['band_low_hz'] < p['band_high_hz'] < p['sample_rate_hz']/2:
        raise ValueError('analysis band must be strictly inside Nyquist')
    if not p['spacing_lower_m'] <= p['spacing_m'] <= p['spacing_upper_m'] or not p['sound_speed_lower_m_s'] <= p['sound_speed_m_s'] <= p['sound_speed_upper_m_s']:
        raise ValueError('geometry bounds must contain nominal values')
    for key in ('channel_1','channel_2'):
        values=p[key]
        if not isinstance(values,list) or not 64 <= len(values) <= 4096:
            raise ValueError('64..4096 real samples required per channel')
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or abs(v)>1000 for v in values):
            raise ValueError('finite bounded real samples required')
    if len(p['channel_1']) != len(p['channel_2']): raise ValueError('channel length mismatch')


def analyze(p):
    validate(p)
    x=np.asarray(p['channel_1'],dtype=float); y=np.asarray(p['channel_2'],dtype=float)
    x=x-x.mean(); y=y-y.mean()
    if np.linalg.norm(x)<=1e-12 or np.linalg.norm(y)<=1e-12:
        raise ValueError('silent or constant channels have no delay observation')
    size=len(x); fft_size=1 << (2*size-2).bit_length()
    sx=np.fft.rfft(x,fft_size); sy=np.fft.rfft(y,fft_size)
    cross=sy*np.conj(sx); magnitude=abs(cross)
    frequencies=np.fft.rfftfreq(fft_size,1/p['sample_rate_hz'])
    mask=(frequencies>=p['band_low_hz']) & (frequencies<=p['band_high_hz'])
    supported=mask & (magnitude>max(float(magnitude.max())*SPECTRAL_RELATIVE_FLOOR,1e-24))
    active=int(supported.sum())
    if active<p['minimum_active_bins']: raise ValueError('insufficient excited cross-spectrum bins in declared band')
    phat=np.zeros_like(cross); phat[supported]=cross[supported]/magnitude[supported]
    circular=np.fft.irfft(phat,fft_size)
    correlation=np.concatenate((circular[-(size-1):],circular[:size]))
    lags=np.arange(-(size-1),size); scores=abs(correlation)
    peak=float(scores.max())
    tied=np.flatnonzero(scores>=peak*(1-PEAK_TIE_RESOLUTION))
    index=int(tied[0]); delay=int(lags[index])
    left=right=index
    while left>0 and ratio_at_least(float(scores[left-1])/peak,p['support_fraction']): left-=1
    while right<len(scores)-1 and ratio_at_least(float(scores[right+1])/peak,p['support_fraction']): right+=1
    competitors=(np.abs(lags-delay)>p['peak_exclusion_samples']) & ((np.arange(len(lags))<left)|(np.arange(len(lags))>right))
    competing=float(scores[competitors].max()) if competitors.any() else 0.0
    ratio=peak/competing if competing>1e-15 else None
    width=right-left+1
    qualified=bool(len(tied)==1 and width<=p['maximum_support_width_samples'] and (ratio is None or ratio_at_least(ratio,p['minimum_peak_ratio'])))
    polarity=bool(correlation[index]>0)
    error=p['timing_bound_samples']+p['estimator_error_bound_samples']
    support=[float(lags[left])-error,float(lags[right])+error]
    seconds=[bound/p['sample_rate_hz'] for bound in support]
    cosine_bounds=[t*c/d for t in seconds for c in (p['sound_speed_lower_m_s'],p['sound_speed_upper_m_s'])
                   for d in (p['spacing_lower_m'],p['spacing_upper_m'])]
    interval=[min(cosine_bounds),max(cosine_bounds)]
    physical=interval[0]>=-1 and interval[1]<=1
    alias=2*p['band_high_hz']*p['spacing_upper_m']<=p['sound_speed_lower_m_s']
    angle=[math.degrees(math.asin(v)) for v in interval] if physical and qualified and polarity and alias else None
    checks=[{'id':'POLARITY_CONSISTENCY','passed':polarity,'on_failure':'CHECK_CHANNEL_WIRING_AND_POLARITY'},
            {'id':'PEAK_IDENTIFIABILITY','passed':qualified,'on_failure':'ISOLATE_ARRIVAL_OR_IMPROVE_BAND_EXCITATION'},
            {'id':'ALIAS_FREE_DECLARED_BAND','passed':bool(alias),'on_failure':'REVISE_APERTURE_OR_ANALYSIS_BAND'},
            {'id':'DIRECTION_INTERVAL_VALIDITY','passed':bool(physical),'on_failure':'CHECK_GEOMETRY_CLOCK_AND_REFLECTION_PATH'}]
    return {'delay_samples':delay,'tdoa_s':delay/p['sample_rate_hz'],
            'direction_cosine':delay/p['sample_rate_hz']*p['sound_speed_m_s']/p['spacing_m'],
            'direction_cosine_interval':interval,'planar_angle_interval_deg':angle,
            'front_back_complement_interval_deg':[180-angle[1],180-angle[0]] if angle is not None else None,
            'peak_score':peak,'competing_peak_score':competing,'peak_ratio':ratio,'peak_tie_count':len(tied),
            'peak_support_lags':[int(lags[left]),int(lags[right])],'delay_interval_samples':support,
            'active_bins':active,'fft_size':fft_size,'peak_qualified':qualified,'polarity_consistent':polarity,
            'checks':checks,'disposition':'BOUNDED_BASELINE_ACCEPT' if all(c['passed'] for c in checks) else 'DESIGN_REVISION_REQUIRED',
            'required_revisions':[c['on_failure'] for c in checks if not c['passed']],
            'next_discriminating_experiment':next((c['on_failure'] for c in checks if not c['passed']),'SWAP_CHANNELS_AND_REPEAT_WITH_KNOWN_SOURCE_GEOMETRY'),
            'counter_hypotheses':['channel order or timing bias rather than source motion','reflection rather than direct arrival',
                                  'spatial aliasing or weak excitation rather than a unique source direction'],
            'model_assumptions':[MODELS['array_model'],MODELS['channel_polarity'],
                                'timing plus supplied estimator-error bound and selected lobe support are not confidence intervals'],
            'unique_3d_direction_verified':False,'calibration_verified':False,
            'scope':'Two-sensor direction-cosine/planar ambiguity under supplied model bounds; not a complete beamformer',
            'unresolved':['front/back and 3D cone ambiguity','actual synchronized acquisition and array calibration',
                          'unverified estimator error bound and multipath applicability']}
