"""R032 bounded capture metadata; no physical IO or absolute clock claims."""
import math
from fractions import Fraction

MODEL='FIRST_SAMPLE_CAPTURE_TIMESTAMP_V1'
FIELDS={'model','reference_rate_assumption','capture_clock_id','delivery_clock_id','timestamp_kind',
        'clock_mode','pdm_clock_hz','decimation_ratio','sample_rate_hz','frame_samples',
        'sample_width_bits','slot_width_bits','expected_channel_ids','observed_slot_order',
        'timestamp_resolution_ns','allowed_rate_error_ppm','allowed_alignment_skew_samples',
        'maximum_delivery_latency_ms','maximum_nominal_rate_timing_residual_ns','channels'}


def validate(p):
    if not isinstance(p,dict) or set(p)!=FIELDS:raise ValueError('exact capture metadata contract required')
    for key,value in {'model':MODEL,'reference_rate_assumption':'UNVERIFIED_REFERENCE_TIMESCALE',
                      'timestamp_kind':'FIRST_SAMPLE_ACQUISITION','clock_mode':'PDM_INTEGER_DECIMATION'}.items():
        if p[key]!=value:raise ValueError('unsupported clock/timestamp assumption')
    def identifier(v):return isinstance(v,str) and 0<len(v)<=80 and v.strip()==v
    if not identifier(p['capture_clock_id']) or p['capture_clock_id']!=p['delivery_clock_id']:
        raise ValueError('same explicit acquisition/delivery reference clock required')
    def integer(v,low,high):
        if type(v) is not int or not low<=v<=high:raise ValueError('bounded integer required')
    for key,low,high in (('sample_rate_hz',8000,192000),('pdm_clock_hz',1,100000000),
                         ('decimation_ratio',1,4096),('frame_samples',1,8192),('timestamp_resolution_ns',1,1000000000)):
        integer(p[key],low,high)
    for key in ('sample_width_bits','slot_width_bits'):
        if type(p[key]) is not int or p[key] not in (16,24,32):raise ValueError('supported PCM width required')
    for key in ('allowed_rate_error_ppm','allowed_alignment_skew_samples','maximum_delivery_latency_ms',
                'maximum_nominal_rate_timing_residual_ns'):
        v=p[key]
        if type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1e9:raise ValueError('finite nonnegative policy required')
    for key in ('expected_channel_ids','observed_slot_order'):
        v=p[key]
        if not isinstance(v,list) or not 2<=len(v)<=16 or any(not identifier(x) for x in v) or len(set(v))!=len(v):
            raise ValueError('unique ordered channel IDs required')
    channels=p['channels']
    if not isinstance(channels,list) or len(channels)!=len(p['expected_channel_ids']):raise ValueError('complete channel streams required')
    ids=[];counts=[]
    for c in channels:
        if not isinstance(c,dict) or set(c)!={'channel_id','frames'} or not identifier(c['channel_id']):raise ValueError('channel contract')
        ids.append(c['channel_id']);frames=c['frames']
        if not isinstance(frames,list) or not 2<=len(frames)<=128:raise ValueError('2..128 frames required')
        counts.append(len(frames))
        for i,f in enumerate(frames):
            if not isinstance(f,dict) or set(f)!={'frame_seq','first_sample_index','sample_count','capture_timestamp_ns','delivery_timestamp_ns'}:
                raise ValueError('exact frame metadata required')
            for key,v in f.items():integer(v,1 if key=='sample_count' else 0,8192 if key=='sample_count' else 2**53-1)
            if f['delivery_timestamp_ns']<f['capture_timestamp_ns']:raise ValueError('delivery before capture')
            if i and f['capture_timestamp_ns']<=frames[i-1]['capture_timestamp_ns']:raise ValueError('capture timestamps must increase')
        if frames[-1]['first_sample_index']<=frames[0]['first_sample_index']:raise ValueError('unwrapped positive sample advance required')
    if len(set(ids))!=len(ids) or set(ids)!=set(p['expected_channel_ids']) or len(set(counts))!=1:
        raise ValueError('unique complete equal-length aligned channel records required')


def _number(v):return round(float(v),9)


def _bound(v,upper):
    """Outward decimal grid, then outward binary-float conversion if needed."""
    v=Fraction(v);scaled=v*10**9
    units=-((-scaled.numerator)//scaled.denominator) if upper else scaled.numerator//scaled.denominator
    result=float(Fraction(units,10**9))
    if (upper and Fraction(result)<v) or (not upper and Fraction(result)>v):
        result=math.nextafter(result,math.inf if upper else -math.inf)
    return result


def analyze(p):
    validate(p)
    fs=p['sample_rate_hz'];resolution=p['timestamp_resolution_ns']
    def limit(key):return Fraction(str(p[key]))
    def interval_state(lo,hi,maximum,minimum=Fraction(0)):
        if lo is None:return 'INCONCLUSIVE'
        if lo>=minimum and hi<=maximum:return 'PASS'
        if hi<minimum or lo>maximum:return 'FAIL'
        return 'INCONCLUSIVE'
    def combine(states):return 'FAIL' if 'FAIL' in states else 'INCONCLUSIVE' if 'INCONCLUSIVE' in states else 'PASS'
    states={key:[] for key in ('CONTINUITY','RELATIVE_RATE','NOMINAL_RATE_TIMING_RESIDUAL','CHANNEL_ALIGNMENT','DELIVERY_LATENCY')}
    states['CHANNEL_MAPPING']=['PASS' if p['expected_channel_ids']==p['observed_slot_order'] else 'FAIL']
    states['PCM_PACKING']=['PASS' if p['sample_width_bits']<=p['slot_width_bits'] else 'FAIL']
    states['PDM_RATE_RELATION']=['PASS' if p['pdm_clock_hz']==fs*p['decimation_ratio'] else 'FAIL']
    result=[]
    for c in p['channels']:
        frames=c['frames'];issues=[];residuals=[];latencies=[]
        for i,f in enumerate(frames):
            if f['sample_count']!=p['frame_samples']:issues.append({'frame_position':i,'kind':'FRAME_SIZE','delta':f['sample_count']-p['frame_samples']})
            latency=f['delivery_timestamp_ns']-f['capture_timestamp_ns']
            lo=Fraction(max(0,latency-resolution),1000000);hi=Fraction(latency+resolution,1000000)
            latencies.append([_bound(lo,False),_bound(hi,True)])
            states['DELIVERY_LATENCY'].append(interval_state(lo,hi,limit('maximum_delivery_latency_ms')))
            if i:
                prev=frames[i-1];seq=f['frame_seq']-prev['frame_seq']-1
                gap=f['first_sample_index']-prev['first_sample_index']-prev['sample_count']
                if seq:issues.append({'frame_position':i,'kind':'FRAME_SEQUENCE','delta':seq})
                if gap:issues.append({'frame_position':i,'kind':'SAMPLE_GAP_OR_OVERLAP','delta':gap})
                residual=Fraction(f['capture_timestamp_ns']-prev['capture_timestamp_ns'])-Fraction((f['first_sample_index']-prev['first_sample_index'])*10**9,fs)
                lo=max(Fraction(0),abs(residual)-resolution);hi=abs(residual)+resolution
                residuals.append([_bound(lo,False),_bound(hi,True)])
                states['NOMINAL_RATE_TIMING_RESIDUAL'].append(interval_state(lo,hi,limit('maximum_nominal_rate_timing_residual_ns')))
        states['CONTINUITY'].append('FAIL' if issues else 'PASS')
        advance=frames[-1]['first_sample_index']-frames[0]['first_sample_index']
        elapsed=frames[-1]['capture_timestamp_ns']-frames[0]['capture_timestamp_ns']
        rate=Fraction(advance*10**9,elapsed);ppm=(rate/fs-1)*10**6
        bounds=None
        if elapsed>resolution:
            lower=(Fraction(advance*10**9,elapsed+resolution)/fs-1)*10**6
            upper=(Fraction(advance*10**9,elapsed-resolution)/fs-1)*10**6
            bounds=[_bound(lower,False),_bound(upper,True)]
            rate_state=interval_state(lower,upper,limit('allowed_rate_error_ppm'),-limit('allowed_rate_error_ppm'))
        else:rate_state='INCONCLUSIVE'
        states['RELATIVE_RATE'].append(rate_state)
        result.append({'channel_id':c['channel_id'],'observed_reference_rate_hz':_number(rate),
            'relative_rate_error_ppm':_number(ppm),'relative_rate_interval_ppm':bounds,
            'continuity_issues':issues,'absolute_timing_residual_intervals_ns':residuals,
            'delivery_latency_intervals_ms':latencies})
    alignment=[]
    for i in range(len(p['channels'][0]['frames'])):
        frames=[c['frames'][i] for c in p['channels']]
        if len({f['first_sample_index'] for f in frames})!=1:
            alignment.append(None);states['CHANNEL_ALIGNMENT'].append('FAIL');continue
        times=[f['capture_timestamp_ns'] for f in frames];spread=max(times)-min(times)
        lo=Fraction(max(0,spread-resolution)*fs,10**9);hi=Fraction((spread+resolution)*fs,10**9)
        alignment.append([_bound(lo,False),_bound(hi,True)])
        states['CHANNEL_ALIGNMENT'].append(interval_state(lo,hi,limit('allowed_alignment_skew_samples')))
    actions={'CONTINUITY':'Repair frame counters and sample continuity without padding away losses',
        'RELATIVE_RATE':'Establish a sufficient observation interval and relative clock-rate budget',
        'NOMINAL_RATE_TIMING_RESIDUAL':'Resolve nominal-rate timing residual and timestamp quantization',
        'CHANNEL_ALIGNMENT':'Align equal sample indices on the shared capture reference',
        'DELIVERY_LATENCY':'Repair delivery scheduling separately from acquisition alignment',
        'CHANNEL_MAPPING':'Correct explicit slot-to-channel ordering and verify physical wiring separately',
        'PCM_PACKING':'Provide a slot wide enough for the declared sample word',
        'PDM_RATE_RELATION':'Reconcile PDM clock and integer decimation with PCM rate'}
    checks=[{'id':key,'state':combine(values),'passed':combine(values)=='PASS','actual':values,
             'limit':'ALL_BOUNDED_INTERVALS_PASS','on_failure':actions[key]} for key,values in states.items()]
    unresolved=[c['id'] for c in checks if not c['passed']]
    return {'model':MODEL,'reference_rate_assumption':p['reference_rate_assumption'],
        'capture_clock_id':p['capture_clock_id'],'channels':result,'alignment_intervals_samples':alignment,
        'checks':checks,'unresolved':unresolved,'required_revisions':[c['on_failure'] for c in checks if not c['passed']],
        'disposition':'DESIGN_REVISION_REQUIRED' if unresolved else 'BOUNDED_BASELINE_ACCEPT',
        'physical_measurement_verified':False,'physical_capture_verified':False,'bitstream_filter_verified':False,'clock_phase_noise_verified':False,
        'absolute_oscillator_accuracy_verified':False,'role_l3_accepted':False,
        'counter_hypotheses':['Missing transport frames rather than sample oscillator drift',
            'Callback scheduling delay rather than acquisition skew','Slot labels or packing rather than acoustic DOA instability',
            'Reference timescale frequency error rather than absolute sample clock error'],
        'next_discriminating_experiment':'Capture independent frame/sample counters and first-sample timestamps on one documented reference; compare scheduling timestamps separately.',
        'limitations':['Unverified shared reference timescale; no absolute frequency accuracy',
            'Metadata channel labels do not prove wiring or analog group delay',
            'Integer decimation rate does not verify PDM filtering or ADC noise',
            'Nominal-rate timing residual includes steady rate offset; it is not aperture jitter']}
