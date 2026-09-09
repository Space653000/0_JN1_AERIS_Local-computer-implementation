"""R031 independent clock/counter arithmetic; does not call capture executor."""
from fractions import Fraction as F
from decimal import Decimal,localcontext,ROUND_CEILING,ROUND_FLOOR
import math
from .capture_clock import validate


def review(p,candidate):
    validate(p)  # Shared schema only; no execution result or decision predicate.
    sample_rate=p['sample_rate_hz'];q=p['timestamp_resolution_ns']
    names=('CONTINUITY','RELATIVE_RATE','NOMINAL_RATE_TIMING_RESIDUAL','CHANNEL_ALIGNMENT',
           'DELIVERY_LATENCY','CHANNEL_MAPPING','PCM_PACKING','PDM_RATE_RELATION')
    outcomes={key:[] for key in names};streams=[]
    def show(v):return round(float(v),9)
    def endpoint(v,upper):
        # Independent Decimal rounding, not the executor's integer grid routine.
        v=F(v)
        with localcontext() as ctx:
            ctx.prec=80
            decimal=Decimal(v.numerator)/Decimal(v.denominator)
            grid=decimal.quantize(Decimal('0.000000001'),rounding=ROUND_CEILING if upper else ROUND_FLOOR)
            result=float(grid)
        if (upper and F(result)<v) or (not upper and F(result)>v):
            result=math.nextafter(result,math.inf if upper else -math.inf)
        return result
    def verdict(left,right,minimum,maximum):
        if right<minimum or left>maximum:return 'FAIL'
        if left<minimum or right>maximum:return 'INCONCLUSIVE'
        return 'PASS'
    for channel in p['channels']:
        frames=channel['frames'];starts=[f['first_sample_index'] for f in frames]
        ticks=[f['capture_timestamp_ns'] for f in frames]
        issues=[];timing=[];delivery=[]
        for position,frame in enumerate(frames):
            size_error=frame['sample_count']-p['frame_samples']
            if size_error:issues.append(dict(frame_position=position,kind='FRAME_SIZE',delta=size_error))
            # Quantization bounds are attached to both endpoints before subtraction.
            lower=max(F(0),F(2*frame['delivery_timestamp_ns']-q,2)-F(2*frame['capture_timestamp_ns']+q,2))/1000000
            upper=(F(2*frame['delivery_timestamp_ns']+q,2)-F(2*frame['capture_timestamp_ns']-q,2))/1000000
            delivery.append([endpoint(lower,False),endpoint(upper,True)])
            outcomes['DELIVERY_LATENCY'].append(verdict(lower,upper,F(0),F(str(p['maximum_delivery_latency_ms']))))
            if not position:continue
            previous=frames[position-1]
            for kind,delta in (('FRAME_SEQUENCE',frame['frame_seq']-previous['frame_seq']-1),
                               ('SAMPLE_GAP_OR_OVERLAP',starts[position]-starts[position-1]-previous['sample_count'])):
                if delta:issues.append(dict(frame_position=position,kind=kind,delta=delta))
            expected_ns=F((starts[position]-starts[position-1])*1000000000,sample_rate)
            error=F(ticks[position]-ticks[position-1])-expected_ns
            error_min,error_max=error-q,error+q
            lower=F(0) if error_min<=0<=error_max else min(abs(error_min),abs(error_max))
            upper=max(abs(error_min),abs(error_max))
            timing.append([endpoint(lower,False),endpoint(upper,True)])
            outcomes['NOMINAL_RATE_TIMING_RESIDUAL'].append(verdict(lower,upper,F(0),F(str(p['maximum_nominal_rate_timing_residual_ns']))))
        outcomes['CONTINUITY'].append('FAIL' if issues else 'PASS')
        n=starts[-1]-starts[0];dt=ticks[-1]-ticks[0]
        # Compare observed sample advance to nominal advance; no received-frame count.
        ppm=F((n*10**9-sample_rate*dt)*10**6,sample_rate*dt)
        rate=F(n,dt)*10**9
        bounds=None
        if dt<=q:outcomes['RELATIVE_RATE'].append('INCONCLUSIVE')
        else:
            low=F((n*10**9-sample_rate*(dt+q))*10**6,sample_rate*(dt+q))
            high=F((n*10**9-sample_rate*(dt-q))*10**6,sample_rate*(dt-q))
            bounds=[endpoint(low,False),endpoint(high,True)];allow=F(str(p['allowed_rate_error_ppm']))
            outcomes['RELATIVE_RATE'].append(verdict(low,high,-allow,allow))
        streams.append({'channel_id':channel['channel_id'],'observed_reference_rate_hz':show(rate),
            'relative_rate_error_ppm':show(ppm),'relative_rate_interval_ppm':bounds,
            'continuity_issues':issues,'absolute_timing_residual_intervals_ns':timing,
            'delivery_latency_intervals_ms':delivery})
    alignment=[]
    for frame_tuple in zip(*(c['frames'] for c in p['channels'])):
        reference=frame_tuple[0]['first_sample_index']
        if any(f['first_sample_index']!=reference for f in frame_tuple):
            alignment.append(None);outcomes['CHANNEL_ALIGNMENT'].append('FAIL');continue
        times=sorted(f['capture_timestamp_ns'] for f in frame_tuple)
        minimum=max(F(0),F(times[-1]-times[0]-q)*sample_rate/10**9)
        maximum=F(times[-1]-times[0]+q)*sample_rate/10**9
        alignment.append([endpoint(minimum,False),endpoint(maximum,True)])
        outcomes['CHANNEL_ALIGNMENT'].append(verdict(minimum,maximum,F(0),F(str(p['allowed_alignment_skew_samples']))))
    outcomes['CHANNEL_MAPPING']=['PASS' if tuple(p['expected_channel_ids'])==tuple(p['observed_slot_order']) else 'FAIL']
    outcomes['PCM_PACKING']=['FAIL' if p['sample_width_bits']>p['slot_width_bits'] else 'PASS']
    outcomes['PDM_RATE_RELATION']=['PASS' if F(p['pdm_clock_hz'],p['decimation_ratio'])==sample_rate else 'FAIL']
    actions=('Repair frame counters and sample continuity without padding away losses',
        'Establish a sufficient observation interval and relative clock-rate budget',
        'Resolve nominal-rate timing residual and timestamp quantization',
        'Align equal sample indices on the shared capture reference',
        'Repair delivery scheduling separately from acquisition alignment',
        'Correct explicit slot-to-channel ordering and verify physical wiring separately',
        'Provide a slot wide enough for the declared sample word',
        'Reconcile PDM clock and integer decimation with PCM rate')
    checks=[]
    for name,action in zip(names,actions):
        state=max(outcomes[name],key=lambda s:{'PASS':0,'INCONCLUSIVE':1,'FAIL':2}[s])
        checks.append(dict(id=name,state=state,passed=state=='PASS',actual=outcomes[name],
                           limit='ALL_BOUNDED_INTERVALS_PASS',on_failure=action))
    unresolved=[c['id'] for c in checks if not c['passed']]
    expected={'model':'FIRST_SAMPLE_CAPTURE_TIMESTAMP_V1','reference_rate_assumption':'UNVERIFIED_REFERENCE_TIMESCALE',
        'capture_clock_id':p['capture_clock_id'],'channels':streams,'alignment_intervals_samples':alignment,
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
    if not isinstance(candidate,dict) or set(candidate)!=set(expected):raise ValueError('complete scoped capture report required')
    def same(a,b):
        if isinstance(b,dict):return isinstance(a,dict) and set(a)==set(b) and all(same(a[k],v) for k,v in b.items())
        if isinstance(b,list):return isinstance(a,list) and len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
        if type(b) is int:return type(a) is int and a==b
        if type(b) is float:return type(a) in (int,float) and a==b
        return type(a) is type(b) and a==b
    differences=[{'field':k,'asserted':candidate[k],'expected':v} for k,v in expected.items() if not same(candidate[k],v)]
    return {'domain':'microphone-capture-clock','decision':'CHANGES_REQUIRED' if differences else 'BOUNDED_REVIEW_ACCEPT',
            'disagreements':differences,'human_approval':False,'role_l3_awarded':False,
            'scope':'capture counter and relative reference-clock metadata only; no ADC/PDM noise or physical acceptance'}
