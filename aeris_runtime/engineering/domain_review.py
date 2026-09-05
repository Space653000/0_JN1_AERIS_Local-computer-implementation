"""Bounded software review policy; never Human approval or role-wide L3."""
from __future__ import annotations

import ast
import copy
import hashlib
import inspect
import json
import math
import textwrap
from pathlib import Path

from ..config import ROOT
from .numerical_policy import db_at_least,db_at_most,MIN_IDENTIFIABLE_VARIANCE_FRACTION

REQUIRED_DOMAINS={
    'microphone-capture-continuity-baseline':['microphone-capture-clock'],
    'microphone-array-taper-baseline':['microphone-array-pattern'],
    'speaker-sealed-alignment-baseline':['speaker-sealed-lumped'],
    'speaker-ported-alignment-baseline':['speaker-port-lumped'],
    'standards-metadata-applicability-baseline':['standards-metadata'],
    'requirement-association-baseline':['requirement-association'],
    'failure-hypothesis-experiment-baseline':['failure-hypothesis'],
    'microphone-array-tdoa-baseline':['microphone-array-geometry'],
    'speaker-fr-reference-baseline':['speaker-fr-uncertainty'],
    'speaker-power-distortion-baseline':['speaker-nonlinear','speaker-thermal'],
    'tws-fit-anc-call-baseline':['tws-anc','tws-fit-capture'],
    'microphone-reference-noise-headroom-baseline':['microphone-reference','microphone-noise-headroom'],
}
DOMAIN_SKILLS={domain:skill for skill,domains in REQUIRED_DOMAINS.items() for domain in domains}


def applicable(domain,context):
    if domain in {'failure-hypothesis','requirement-association','standards-metadata'}:
        return (context.get('risk') in {'R0','R1'} and context.get('lifecycle') in {'Concept','Architecture','Prototype','EVT'}
                and context.get('source_kind') in {'SYNTHETIC','USER_SUPPLIED_UNVERIFIED'}
                and context.get('transducer') in {'Speaker','Microphone','Both'}
                and isinstance(context.get('product'),str) and bool(context['product'].strip()))
    speaker=domain.startswith('speaker-')
    microphone=domain.startswith('microphone-')
    return (domain in DOMAIN_SKILLS and context.get('risk') in {'R0','R1'}
            and context.get('lifecycle') in {'Concept','Architecture','Prototype','EVT'}
            and context.get('source_kind') in {'SYNTHETIC','USER_SUPPLIED_UNVERIFIED'}
            and context.get('transducer') in ({'Speaker','Both'} if speaker else {'Microphone','Both'} if microphone else {'Both'})
            and isinstance(context.get('product'),str)
            and (speaker or microphone or context['product'] in {'R048','TWS Earbuds'}))


def select_reviewers(request,executor_ids):
    """A matrix label is not qualification; replay the seat's sealed suite."""
    from . import factory,role_acceptance
    from .professional_profiles import ROLE_DOMAIN_CONTRACTS
    skills=request.get('needed_skills',[])
    needed=sorted({d for skill in skills for d in REQUIRED_DOMAINS.get(skill,[])})
    unknown=[skill for skill in skills if skill not in REQUIRED_DOMAINS]
    context={key:request.get(key) for key in ('product','transducer','lifecycle','risk')}
    context['source_kind']=request.get('source_kind','USER_SUPPLIED_UNVERIFIED')
    conflicts=request.get('conflicted_role_ids',[])
    if not isinstance(conflicts,list) or any(not isinstance(role,str) for role in conflicts):
        raise ValueError('explicit conflicted role IDs required')
    excluded=set(executor_ids)|set(conflicts)
    evidence_types=request.get('required_evidence',[])
    evidence_supported=(isinstance(evidence_types,list) and bool(evidence_types)
                        and all(item in {'sealed numerical run','independent counterreview'} for item in evidence_types))
    found=[]; missing=[]; runner=role_acceptance.RoleAcceptanceFactory()
    for domain in needed:
        selected=None
        if evidence_supported and applicable(domain,context):
            for role,contracts in sorted(ROLE_DOMAIN_CONTRACTS.items()):
                if role in excluded: continue
                for contract in contracts:
                    manifest=factory.read(ROOT/f"skills/{contract['skill_id']}/manifest.json")
                    if manifest.get('review_domain')!=domain: continue
                    status=runner.status_for_skill(role,contract['skill_id'])
                    if not status['execution_passed']: continue
                    selected={'role_id':role,'domain':domain,'skill_id':contract['skill_id'],
                              'qualification_run_id':status['run_id'],'qualification_evidence_ref':status['evidence_ref'],
                              'reason':'current sealed exact-Skill domain review suite replayed; context in bounded scope; executor/conflict excluded'}
                    break
                if selected: break
        if selected: found.append(selected)
        else: missing.append(domain)
    return {'reviewers':found,'uncovered_review_domains':missing,'unsupported_review_skills':unknown,
            'complete':bool(needed) and not missing and not unknown,
            'human_approval':False,'context':context,'evidence_requirements_supported':evidence_supported}


def _validate(value,schema):
    """Strict declared-unit input validation, without invoking an executor."""
    kind=schema.get('type')
    if kind=='object':
        if not isinstance(value,dict) or set(schema.get('required',[]))-set(value):
            raise ValueError('required review input fields missing')
        if schema.get('additionalProperties') is False and set(value)-set(schema.get('properties',{})):
            raise ValueError('unknown review input field or unit')
        for key,item in value.items(): _validate(item,schema.get('properties',{}).get(key,{}))
    elif kind=='array':
        if not isinstance(value,list) or not schema.get('minItems',0)<=len(value)<=schema.get('maxItems',1000):
            raise ValueError('bounded review vector required')
        for item in value: _validate(item,schema.get('items',{}))
    elif kind=='number':
        if (isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value)
                or value<schema.get('minimum',-math.inf) or value>schema.get('maximum',math.inf)
                or value<=schema.get('exclusiveMinimum',-math.inf)):
            raise ValueError('finite declared-unit review input required')


def _review_envelope(domain,request):
    if domain not in DOMAIN_SKILLS: raise ValueError('unknown review domain')
    if not isinstance(request,dict) or set(request)!={'parameters','candidate','context'}:
        raise ValueError('exact review envelope required')
    p=request['parameters']; candidate=request['candidate']; context=request['context']
    schema=json.loads((ROOT/f'skills/{DOMAIN_SKILLS[domain]}/input.schema.json').read_text())
    _validate(p,schema)
    if not isinstance(candidate,dict) or not isinstance(context,dict): raise ValueError('review objects required')
    if set(context)!={'product','transducer','lifecycle','risk','source_kind'}:
        raise ValueError('exact applicability context required')
    speaker=domain.startswith('speaker-')
    microphone=domain.startswith('microphone-')
    if not applicable(domain,context):
        raise ValueError('outside evidenced bounded review applicability')
    return p,candidate,speaker,microphone


def _validate_inline_family(p,speaker,microphone):
    if speaker:
        if p['drive_voltage_rms_v']<p['reference_voltage_rms_v'] or p['max_coil_temperature_c']<p['ambient_temperature_c']:
            raise ValueError('inconsistent power review bounds')
    if microphone:
        if (p['minimum_sensitivity_dbv_per_pa']>p['maximum_sensitivity_dbv_per_pa']
                or p['calibrator_output_rms_v']*math.sqrt(2)>=p['adc_peak_v']
                or p['total_noise_rms_v']*(1+p['noise_relative_bound'])>=p['adc_peak_v']
                or p['frontend_noise_rms_v']>p['total_noise_rms_v']):
            raise ValueError('invalid common-frame microphone reference or bounds')


def review(domain,request):
    """Challenge a scoped candidate; acceptance means report consistency only.

    Candidate fields are assertions to check, not inputs to recomputation. These
    independent equations never call domain_methods or use its decision output.
    """
    p,candidate,speaker,microphone=_review_envelope(domain,request)
    if domain=='speaker-fr-uncertainty':
        from .speaker_fr_review import review as review_fr
        return review_fr(p,candidate)
    if domain=='speaker-sealed-lumped':
        from .sealed_alignment_review import review as review_sealed
        return review_sealed(p,candidate)
    if domain=='speaker-port-lumped':
        from .ported_alignment_review import review as review_port
        return review_port(p,candidate)
    if domain=='microphone-array-pattern':
        from .array_beam_review import review as review_pattern
        return review_pattern(p,candidate)
    if domain=='microphone-capture-clock':
        from .capture_clock_review import review as review_clock
        return review_clock(p,candidate)
    if domain=='microphone-array-geometry':
        from .array_doa_review import review as review_array
        return review_array(p,candidate)
    if domain=='failure-hypothesis':
        from .faca_review import review as review_failure
        return review_failure(p,candidate)
    if domain=='requirement-association':
        from .requirement_trace_review import review as review_trace
        return review_trace(p,candidate)
    if domain=='standards-metadata':
        from .standard_metadata_review import review as review_metadata
        return review_metadata(p,candidate)
    expected={}; observations={}
    _validate_inline_family(p,speaker,microphone)
    if domain=='speaker-thermal':
        temperature=p['ambient_temperature_c']+p['input_power_w']*p['thermal_resistance_k_per_w']*(1-math.exp(-p['duration_s']/p['thermal_resistance_k_per_w']/p['thermal_capacity_j_per_k']))
        compression=20*math.log10(p['drive_voltage_rms_v']*p['reference_fundamental_rms_pa']/(p['reference_voltage_rms_v']*p['fundamental_rms_pa']))
        hot=temperature>p['max_coil_temperature_c']; compressed=compression>p['max_compression_db']
        experiment='COOLING_RESISTANCE_SWEEP' if hot and compressed else 'COLD_AMPLIFIER_LIMITER_CAPTURE' if compressed else 'HARMONIC_HEADROOM_SWEEP'
        expected={'predicted_coil_temperature_c':temperature,'compression_db':compression,
                  'thermal_passed':not hot,'next_experiment':experiment}
        observations={'temperature_margin_c':p['max_coil_temperature_c']-temperature,
                      'counter_hypothesis':'limiter gain or amplifier headroom can mimic thermal compression',
                      'limitation':'single RC, constant real power, initial ambient; no lifetime inference'}
    elif domain=='speaker-nonlinear':
        thd=100*math.sqrt(sum(h*h for h in p['harmonic_rms_pa']))/p['fundamental_rms_pa']
        compression=20*math.log10(p['drive_voltage_rms_v']*p['reference_fundamental_rms_pa']/(p['reference_voltage_rms_v']*p['fundamental_rms_pa']))
        expected={'thd_percent':thd,'compression_db':compression,
                  'thd_passed':thd<=p['max_thd_percent'],'compression_passed':compression<=p['max_compression_db'],
                  'transducer_cause_verified':False}
        observations={'counter_hypothesis':'amplifier clipping, limiter gain or fixture rattling rather than proven transducer cause',
                      'next_experiment':'matched level and fixture sweep with amplifier voltage/headroom recorded',
                      'limitation':'RMS harmonics exclude fundamental; no Bl/Kms/Le identification from scalar THD'}
    elif domain=='tws-anc':
        margin=180-(p['plant_phase_lag_deg']+0.36*p['feedback_crossover_hz']*p['feedback_delay_ms'])
        feedback=margin>=p['min_phase_margin_deg']; feedforward=p['ff_wind_rms_pa']<=p['max_ff_wind_rms_pa']
        topology={(True,True):'HYBRID',(True,False):'FB_ONLY',(False,True):'FF_ONLY',(False,False):'PASSIVE'}[(feedback,feedforward)]
        expected={'phase_margin_deg':margin,'feedback_passed':feedback,'feedforward_passed':feedforward,
                  'anc_topology_candidate':topology,'full_loop_stability_verified':False}
        observations={'counter_hypothesis':'feedback latency versus wind-exposed feedforward path',
                      'next_experiment':'measure inward/outward loop transfer across all crossovers and fit states',
                      'limitation':'one crossover and supplied plant phase cannot establish full-loop stability'}
    elif domain=='tws-fit-capture':
        loss=10*math.log10((p['bass_reference_hz']**2+p['leak_pole_hz']**2)/p['bass_reference_hz']**2)
        snr=10*math.log10(p['call_speech_rms_pa']**2/(p['call_ambient_rms_pa']**2+p['ff_wind_rms_pa']**2))
        experiment=('RESEAL_BEFORE_EQ' if loss>p['max_leak_loss_db'] else
                    'WIND_SHIELD_AND_PORT_ORIENTATION' if p['ff_wind_rms_pa']>p['max_ff_wind_rms_pa'] else
                    'STATIONARY_NOISE_AND_CAPTURE_PATH' if snr<p['min_call_snr_db'] else 'FIT_DISTRIBUTION_AND_PORT_TRANSFER')
        expected={'leak_loss_db':loss,'call_snr_db':snr,'seal_passed':loss<=p['max_leak_loss_db'],
                  'capture_passed':snr>=p['min_call_snr_db'],'next_experiment':experiment,
                  'excursion_passed':p['driver_peak_excursion_mm']<=p['safe_peak_excursion_mm'],
                  'occlusion_passed':p['occlusion_boost_db']<=p['max_occlusion_boost_db'],
                  'excursion_measured':False,'occlusion_measured':False}
        observations={'counter_hypothesis':'port wind or seal leakage rather than capsule sensitivity or insufficient EQ',
                      'limitation':'supplied excursion and occlusion estimates are not acquired measurements'}
    elif domain=='microphone-reference':
        sensitivity_db=20*(math.log10(p['calibrator_output_rms_v'])-math.log10(p['calibration_gain_linear'])-math.log10(p['calibrator_pressure_rms_pa']))
        interval=[sensitivity_db-20*math.log10((1+p['pressure_relative_bound'])*(1+p['gain_relative_bound'])),
                  sensitivity_db-20*math.log10((1-p['pressure_relative_bound'])*(1-p['gain_relative_bound']))]
        expected={'sensitivity_dbv_per_pa':sensitivity_db,'sensitivity_interval_dbv_per_pa':interval,
                  'sensitivity_passed':db_at_least(interval[0],p['minimum_sensitivity_dbv_per_pa']) and db_at_most(interval[1],p['maximum_sensitivity_dbv_per_pa']),
                  'capsule_overload_verified':False}
        observations={'counter_hypothesis':'calibration gain or pressure coupling rather than changed capsule sensitivity',
                      'next_experiment':'repeat an unclipped common reference and independently establish calibration gain',
                      'limitation':'supplied sensitivity cannot establish capsule acoustic overload'}
    elif domain=='microphone-noise-headroom':
        # Work in input-equivalent pressure, separately from the executor's
        # voltage-chain implementation. The noise subtraction is identifiable
        # only when its conservative lower residual remains positive.
        ratio=p['calibrator_pressure_rms_pa']*p['calibration_gain_linear']/p['calibrator_output_rms_v']/p['analysis_gain_linear']
        pu=p['pressure_relative_bound']; gu=p['gain_relative_bound']; nu=p['noise_relative_bound']
        ratio_low=ratio*(1-pu)*(1-gu)/(1+gu)
        ratio_high=ratio*(1+pu)*(1+gu)/(1-gu)
        total=p['total_noise_rms_v']; frontend=p['frontend_noise_rms_v']; ambient=p['ambient_noise_rms_pa']
        residual=(total*ratio)**2-(frontend*ratio)**2-ambient**2
        low=((total*(1-nu))**2-(frontend*(1+nu))**2)*ratio_low**2-(ambient*(1+nu))**2
        high=((total*(1+nu))**2-(frontend*(1-nu))**2)*ratio_high**2-(ambient*(1-nu))**2
        resolved=residual>max(1e-30,(total*ratio)**2*MIN_IDENTIFIABLE_VARIANCE_FRACTION) and low>0
        noise=math.sqrt(residual) if resolved else None
        noise_db=20*math.log10(noise/20e-6) if resolved else None
        upper_pa=math.sqrt(high) if resolved else total*(1+nu)*ratio_high
        upper=20*math.log10(upper_pa/20e-6)
        headroom=20*math.log10(p['adc_peak_v']*ratio/20e-6/p['signal_crest_factor'])-p['required_spl_db']
        headroom_low=20*math.log10(p['adc_peak_v']*ratio_low/20e-6/p['signal_crest_factor'])-p['required_spl_db']
        experiment=('QUIETER_ROOM_OR_CALIBRATOR_COUPLING' if ambient>=frontend*ratio else 'LOWER_NOISE_FRONTEND_AT_MATCHED_GAIN') if not resolved else 'LEVEL_SWEEP_WITH_DISTORTION_BEFORE_ANY_CAPSULE_OVERLOAD_CLAIM'
        expected={'noise_resolved':resolved,'self_noise_rms_pa':noise,'self_noise_spl_db':noise_db,
                  'self_noise_upper_spl_db':upper,'electrical_headroom_db':headroom,'electrical_headroom_lower_db':headroom_low,
                  'noise_upper_scope':'INTRINSIC_RESIDUAL_BOUND' if resolved else 'TOTAL_INPUT_EQUIVALENT_BOUND',
                  'noise_passed':resolved and db_at_most(upper,p['maximum_self_noise_spl_db']),
                  'headroom_passed':db_at_least(headroom_low,p['minimum_electrical_headroom_db']),
                  'next_experiment':experiment,'headroom_scope':'SIGNAL_ONLY_NOISE_PEAKS_UNBOUNDED','capsule_overload_verified':False}
        observations={'counter_hypothesis':'frontend or ambient floor instead of intrinsic capsule noise',
                      'limitation':'common-bandwidth uncorrelated subtraction; signal-only headroom is not capsule AOP or total peak immunity'}
    else:
        raise ValueError('domain reviewer not implemented')
    return _finish_review(domain,candidate,expected,observations,microphone,speaker)


def _finish_review(domain,candidate,expected,observations,microphone,speaker):
    expected.update(physical_measurement_verified=False,lifetime_verified=False)
    expected['counter_hypotheses']=(['room noise rather than capsule self-noise','frontend noise rather than capsule noise',
        'calibrator coupling or gain-reference error rather than capsule sensitivity drift'] if microphone else
        ['amplifier clipping rather than transducer nonlinearity',
        'limiter gain reduction rather than thermal compression','fixture response change rather than power compression'] if speaker else
        ['seal leakage rather than insufficient bass EQ','feedback delay rather than feedforward filter magnitude',
         'outward-mic wind rather than stationary ambient noise'])
    if set(candidate)!=set(expected): raise ValueError('exact scoped candidate assertions required')
    disagreements=[]
    for key,wanted in expected.items():
        actual=candidate[key]
        matches=_same_assertion(actual,wanted)
        if not matches: disagreements.append({'field':key,'asserted':actual,'expected':wanted})
    return {'domain':domain,'decision':'CHANGES_REQUIRED' if disagreements else 'BOUNDED_REVIEW_ACCEPT',
            'disagreements':disagreements,'observations':observations,
            'human_approval':False,'role_l3_awarded':False,'scope':'bounded software report consistency only'}


def _same_assertion(actual,wanted):
    if isinstance(wanted,bool) or wanted is None: return actual is wanted
    if isinstance(wanted,(float,int)):
        return (isinstance(actual,(float,int)) and not isinstance(actual,bool) and math.isfinite(actual)
                and math.isclose(actual,wanted,rel_tol=1e-9,abs_tol=1e-12))
    if isinstance(wanted,list):
        return isinstance(actual,list) and len(actual)==len(wanted) and all(_same_assertion(a,b) for a,b in zip(actual,wanted))
    return actual==wanted


_DELEGATED_REVIEW_DEPENDENCIES={
    'speaker-fr-uncertainty':('speaker_fr_review.py','speaker_fr.py','numerical_policy.py'),
    'speaker-sealed-lumped':('sealed_alignment_review.py','sealed_alignment.py'),
    'speaker-port-lumped':('ported_alignment_review.py','ported_alignment.py'),
    'microphone-array-pattern':('array_beam_review.py','array_beam.py'),
    'microphone-capture-clock':('capture_clock_review.py','capture_clock.py'),
    'microphone-array-geometry':('array_doa_review.py','array_doa.py','numerical_policy.py'),
    'failure-hypothesis':('faca_review.py','faca.py'),
    'requirement-association':('requirement_trace_review.py','requirement_trace.py'),
    'standards-metadata':('standard_metadata_review.py','standard_metadata.py'),
}


def capability_source_digest(domain):
    """Hash the exact domain branch, declared dependencies and shared predicates."""
    if domain not in DOMAIN_SKILLS: raise ValueError('unknown review domain')
    source=textwrap.dedent(inspect.getsource(review)); tree=ast.parse(source)
    fragments=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.If):
            names={item.id for item in ast.walk(node.test) if isinstance(item,ast.Name)}
            constants={item.value for item in ast.walk(node.test) if isinstance(item,ast.Constant)}
            if 'domain' in names and domain in constants:
                fragments.append(ast.dump(ast.Module(body=node.body,type_ignores=[]),include_attributes=False))
    if not fragments: raise ValueError('domain review branch source missing')
    files=list(_DELEGATED_REVIEW_DEPENDENCIES.get(domain,('numerical_policy.py',)))
    folder=Path(__file__).parent
    shared=(applicable,_validate,_review_envelope) if domain in _DELEGATED_REVIEW_DEPENDENCIES else \
           (applicable,_validate,_review_envelope,_validate_inline_family,_finish_review,_same_assertion)
    payload={'domain':domain,'branch_ast':fragments,
             'shared':{fn.__name__:inspect.getsource(fn) for fn in shared},
             'dependencies':{name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in files}}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


def execution_context(request,role_id,skill_id,source_kind):
    """Capture applicability before execution; subsequent review uses its seal."""
    return {'source_kind':source_kind,'objective':request['requirement'],
            'role_id':role_id,'skill_id':skill_id,'physical_verification':False,
            'applicability':{key:copy.deepcopy(request[key]) for key in
                ('product','transducer','lifecycle','risk','required_evidence')},
            'required_review_domains':list(REQUIRED_DOMAINS.get(skill_id,[])),
            'conflicted_role_ids':copy.deepcopy(request.get('conflicted_role_ids',[])),
            'review_policy_version':'H0001-bounded-software-review-v1'}


def _candidate(domain,output):
    """Project executor assertions, never recompute answers for the reviewer."""
    v=output['values']; checks={c['id']:c for c in v['checks']}
    if domain in {'speaker-fr-uncertainty','microphone-array-geometry','failure-hypothesis','requirement-association','standards-metadata','speaker-sealed-lumped','speaker-port-lumped','microphone-array-pattern','microphone-capture-clock'}:
        return {**copy.deepcopy(v),
                'physical_measurement_verified':output['physical_measurement_verified']}
    truth={'physical_measurement_verified':output['physical_measurement_verified'],
           'lifetime_verified':v.get('lifetime_verified',False),'counter_hypotheses':v.get('counter_hypotheses')}
    if domain=='speaker-thermal':
        experiment={
            'Measure resistance-derived coil temperature and repeat the level sweep after cooling at identical gain':'COOLING_RESISTANCE_SWEEP',
            'Record amplifier output and limiter gain at matched cold-coil conditions before attributing loss to heat':'COLD_AMPLIFIER_LIMITER_CAPTURE',
            'Measure harmonic order trends with verified amplifier headroom and matched acoustic fixture':'HARMONIC_HEADROOM_SWEEP',
        }.get(v.get('next_discriminating_experiment'),'UNRECOGNIZED_EXPERIMENT')
        return {**truth,'predicted_coil_temperature_c':v['predicted_coil_temperature_c'],
                'compression_db':v['compression_db'],'thermal_passed':checks['COIL_TEMPERATURE_C']['passed'],
                'next_experiment':experiment}
    if domain=='speaker-nonlinear':
        return {**truth,'thd_percent':v['thd_percent'],'compression_db':v['compression_db'],
                'thd_passed':checks['THD_PERCENT']['passed'],'compression_passed':checks['COMPRESSION_DB']['passed'],
                'transducer_cause_verified':v.get('transducer_cause_verified',False)}
    if domain=='tws-anc':
        return {**truth,'phase_margin_deg':v['phase_margin_deg'],'feedback_passed':checks['FEEDBACK_PHASE_MARGIN_DEG']['passed'],
                'feedforward_passed':checks['OUTWARD_FF_WIND_RMS_PA']['passed'],'anc_topology_candidate':v['anc_topology_candidate'],
                'full_loop_stability_verified':v.get('full_loop_stability_verified',False)}
    if domain=='tws-fit-capture':
        revisions=v['required_revisions']
        experiment=('RESEAL_BEFORE_EQ' if 'RECHECK_TIP_SEAL_BEFORE_BASS_EQ' in revisions else
                    'WIND_SHIELD_AND_PORT_ORIENTATION' if 'DISABLE_OR_LIMIT_WIND_EXPOSED_FEEDFORWARD_PATH' in revisions else
                    'STATIONARY_NOISE_AND_CAPTURE_PATH' if 'REVISE_CALL_CAPTURE_PATH_OR_WIND_SHIELDING' in revisions else
                    'FIT_DISTRIBUTION_AND_PORT_TRANSFER')
        return {**truth,'leak_loss_db':v['leak_loss_db'],'call_snr_db':v['call_snr_db'],
                'seal_passed':checks['SEAL_LEAK_LOSS_DB']['passed'],'capture_passed':checks['OUTWARD_CALL_SNR_DB']['passed'],
                'excursion_passed':checks['MINIATURE_DRIVER_EXCURSION_MM']['passed'],
                'occlusion_passed':checks['OCCLUSION_BOOST_DB']['passed'],
                'next_experiment':experiment,'excursion_measured':v.get('excursion_measured',False),
                'occlusion_measured':v.get('occlusion_measured',False)}
    if domain=='microphone-reference':
        return {**truth,'sensitivity_dbv_per_pa':v['sensitivity_dbv_per_pa'],
                'sensitivity_interval_dbv_per_pa':v['sensitivity_interval_dbv_per_pa'],
                'sensitivity_passed':checks['SENSITIVITY_INTERVAL']['passed'],
                'capsule_overload_verified':v['capsule_overload_verified']}
    if domain=='microphone-noise-headroom':
        return {**truth,**{key:v[key] for key in ('noise_resolved','self_noise_rms_pa','self_noise_spl_db',
                    'self_noise_upper_spl_db','noise_upper_scope','electrical_headroom_db','electrical_headroom_lower_db','headroom_scope','capsule_overload_verified')},
                'noise_passed':checks['SELF_NOISE_UPPER_BOUND']['passed'],'headroom_passed':checks['ELECTRICAL_HEADROOM']['passed'],
                'next_experiment':v['next_discriminating_experiment']}
    raise ValueError('unknown domain')


def _assess_execution(run_id):
    from .. import evidence
    from ..skills_runtime import run_skill
    from . import catalog,factory,domain_methods
    if not evidence.validate_bundle(run_id).get('valid'): raise ValueError('executor evidence integrity failed')
    root=evidence.bundle_dir(run_id)
    context=factory.read(root/'raw/engineering-context.json')
    params=factory.read(root/'raw/engineering-input.json')
    output=factory.read(root/'processed/skill_result.json')
    method=factory.read(root/'method_snapshot.json')
    skill=context['skill_id']; role=context['role_id']
    domains=REQUIRED_DOMAINS.get(skill)
    if (not domains or context['required_review_domains']!=domains
            or context.get('review_policy_version')!='H0001-bounded-software-review-v1'
            or method['skill_id']!=skill or output['skill_id']!=skill
            or output['input_sha256']!=catalog.digest(params)
            or output['implementation_sha256']!=domain_methods.capability_source_digest(skill)
            or output.get('evidence_class')!='DETERMINISTIC_ROLE_DOMAIN_CALCULATION'
            or output.get('professional_tool_verified') is not False
            or context.get('physical_verification') is not False):
        raise ValueError('sealed context/Skill/source/review domain mismatch')
    if skill not in factory.load_pack(role)['required_skills']: raise ValueError('executor seat/Skill mismatch')
    request={**context['applicability'],'source_kind':context['source_kind'],'needed_skills':[skill],
             'conflicted_role_ids':context['conflicted_role_ids']}
    selection=select_reviewers(request,[role])
    if not selection['complete']: raise ValueError('missing current independent qualifications or unsupported applicability')
    reviews=[]
    for seat in selection['reviewers']:
        inputs={'parameters':params,'candidate':_candidate(seat['domain'],output),'context':selection['context']}
        reviewed=run_skill(seat['skill_id'],inputs)
        reviews.append({**seat,'input':inputs,'output':reviewed})
    values=output['values']; checks=values['checks']
    all_passed=bool(checks) and all(c.get('passed') is True for c in checks)
    expected_disposition='BOUNDED_BASELINE_ACCEPT' if all_passed else 'DESIGN_REVISION_REQUIRED'
    expected_revisions=[c['on_failure'] for c in checks if c.get('passed') is not True]
    coherent=(_checks_coherent(skill,params,values) and values['disposition']==expected_disposition
              and values['required_revisions']==expected_revisions)
    review_passed=coherent and all(r['output']['values']['decision']=='BOUNDED_REVIEW_ACCEPT' for r in reviews)
    return {'execution_run_id':run_id,'execution_sha256':catalog.digest({'context':context,'parameters':params,'output':output,'method':method}),
            'review_source_sha256':domain_methods.LOADED_SHA256,'reviews':reviews,
            'decision':'CHANGES_REQUIRED' if not review_passed else 'BOUNDED_REVIEW_ACCEPT' if all_passed else 'DESIGN_REVISION_REQUIRED',
            'qualified_review':review_passed,'disposition_coherent':coherent,
            'human_approval':False,'role_l3_awarded':False,
            'scope':'bounded software review; original execution remains EVIDENCED, not physical/Human verified'}


def _checks_coherent(skill,params,values):
    """Require every bounded constraint and its actual units/action contract.

    Scalars used here are independently checked by domain reviewers. Comparing
    a caller-supplied set with itself cannot prove coverage or correct actions.
    """
    from .catalog import digest
    if skill=='microphone-capture-continuity-baseline':
        return [c.get('id') for c in values['checks']]==['CONTINUITY','RELATIVE_RATE','NOMINAL_RATE_TIMING_RESIDUAL','CHANNEL_ALIGNMENT','DELIVERY_LATENCY','CHANNEL_MAPPING','PCM_PACKING','PDM_RATE_RELATION']
    if skill=='microphone-array-taper-baseline':
        return [c.get('id') for c in values['checks']]==['SPATIAL_SAMPLING_GUARD','FAR_FIELD_HEURISTIC','ANGULAR_SAMPLING','DESIRED_GAIN_BOUND','SAMPLED_SIDELOBE_BOUND','WHITE_NOISE_GAIN_BOUND']
    if skill=='speaker-sealed-alignment-baseline':
        return [c.get('id') for c in values['checks']]==['F3_UPPER_BOUND','QTC_INTERVAL','EFFECTIVE_BOX_VOLUME','ANALYSIS_FREQUENCY_COVERAGE','LUMPED_GEOMETRY_VALIDITY']
    if skill=='speaker-ported-alignment-baseline':
        return [c.get('id') for c in values['checks']]==['TUNING_INTERVAL','PORT_VELOCITY','LONGITUDINAL_MODE_SEPARATION','LUMPED_GEOMETRY_VALIDITY']
    if skill=='speaker-fr-reference-baseline':
        # Every check/value is independently recomputed by the dedicated reviewer.
        return [c.get('id') for c in values['checks']]==['WINDOW_VALIDITY','SAMPLED_INTERVAL_MASK']
    if skill=='microphone-array-tdoa-baseline':
        return [c.get('id') for c in values['checks']]==['POLARITY_CONSISTENCY','PEAK_IDENTIFIABILITY','ALIAS_FREE_DECLARED_BAND','DIRECTION_INTERVAL_VALIDITY']
    if skill=='failure-hypothesis-experiment-baseline':
        return [c.get('id') for c in values['checks']]==['LEADING_MODEL_POSTERIOR','MODEL_SEPARATION_MARGIN']
    if skill=='requirement-association-baseline':
        return [c.get('id') for c in values['checks']]==['REQUIRED_ASSOCIATION_COVERAGE','CURRENT_REVISION_AND_SEMANTICS','BOUNDED_REQUIREMENT_INTERVALS']
    if skill=='standards-metadata-applicability-baseline':
        return [c.get('id') for c in values['checks']]==['DECLARED_SCOPE_APPLICABILITY','METADATA_COMPLETENESS_AND_FRESHNESS','DECLARED_ACCESS_FOR_INTENDED_USE','SEMANTIC_CHANGE_REVIEW']
    if skill=='speaker-power-distortion-baseline':
        rows=[
            ('THD_PERCENT',values['thd_percent'],params['max_thd_percent'],'<=','LOWER_DRIVE_AND_DISCRIMINATE_TRANSDUCER_FROM_AMPLIFIER_NONLINEARITY'),
            ('COMPRESSION_DB',values['compression_db'],params['max_compression_db'],'<=','SEPARATE_THERMAL_COMPRESSION_FROM_LIMITER_GAIN'),
            ('COIL_TEMPERATURE_C',values['predicted_coil_temperature_c'],params['max_coil_temperature_c'],'<=','REDUCE_DUTY_AND_RECHECK_COIL_TEMPERATURE')]
    elif skill=='tws-fit-anc-call-baseline':
        rows=[
            ('SEAL_LEAK_LOSS_DB',values['leak_loss_db'],params['max_leak_loss_db'],'<=','RECHECK_TIP_SEAL_BEFORE_BASS_EQ'),
            ('FEEDBACK_PHASE_MARGIN_DEG',values['phase_margin_deg'],params['min_phase_margin_deg'],'>=','LOWER_CROSSOVER_OR_LATENCY_AND_REMEASURE_LOOP'),
            ('OUTWARD_FF_WIND_RMS_PA',params['ff_wind_rms_pa'],params['max_ff_wind_rms_pa'],'<=','DISABLE_OR_LIMIT_WIND_EXPOSED_FEEDFORWARD_PATH'),
            ('OUTWARD_CALL_SNR_DB',values['call_snr_db'],params['min_call_snr_db'],'>=','REVISE_CALL_CAPTURE_PATH_OR_WIND_SHIELDING'),
            ('MINIATURE_DRIVER_EXCURSION_MM',params['driver_peak_excursion_mm'],params['safe_peak_excursion_mm'],'<=','LIMIT_BASS_DRIVE_OR_REVISE_RECEIVER'),
            ('OCCLUSION_BOOST_DB',params['occlusion_boost_db'],params['max_occlusion_boost_db'],'<=','REVISE_VENT_OR_SIDETONE_WITH_SEAL_RETEST')]
    elif skill=='microphone-reference-noise-headroom-baseline':
        interval=values['sensitivity_interval_dbv_per_pa']; resolved=values['noise_resolved']
        expected=[
            {'id':'SENSITIVITY_INTERVAL','passed':db_at_least(interval[0],params['minimum_sensitivity_dbv_per_pa']) and db_at_most(interval[1],params['maximum_sensitivity_dbv_per_pa']),
             'on_failure':'RECHECK_PRESSURE_GAIN_AND_REFERENCE_COUPLING'},
            {'id':'IDENTIFIABLE_SELF_NOISE','passed':resolved,'on_failure':'SEPARATE_ROOM_AND_FRONTEND_NOISE_BEFORE_CAPSULE_ATTRIBUTION'},
            {'id':'SELF_NOISE_UPPER_BOUND','passed':resolved and db_at_most(values['self_noise_upper_spl_db'],params['maximum_self_noise_spl_db']),
             'on_failure':'REDUCE_INPUT_NOISE_AND_REPEAT_COMMON_BANDWIDTH_RUN'},
            {'id':'ELECTRICAL_HEADROOM','passed':db_at_least(values['electrical_headroom_lower_db'],params['minimum_electrical_headroom_db']),
             'on_failure':'REDUCE_DEPLOYMENT_GAIN_OR_REVISE_ADC_RANGE'}]
        return digest(expected)==digest(values['checks'])
    else: return False
    expected=[{'id':key,'actual':actual,'limit':limit,'operator':op,
               'margin':limit-actual if op=='<=' else actual-limit,
               'passed':actual<=limit if op=='<=' else actual>=limit,'on_failure':action}
              for key,actual,limit,op,action in rows]
    return digest(expected)==digest(values['checks'])


def review_bundle(run_id):
    from .. import evidence
    from . import factory
    try: record=_assess_execution(run_id)
    except (OSError,ValueError,KeyError,TypeError,RuntimeError) as exc:
        return {'decision':'REVIEW_BLOCKED','qualified_review':False,'human_approval':False,'reason':str(exc)}
    bundle=evidence.create_bundle('DOMAIN-REVIEW','AERIS bounded review',
        method_snapshot={'execution_run_id':run_id,'review_source_sha256':record['review_source_sha256']})
    review_id=bundle['run_id']
    factory.write(evidence.bundle_dir(review_id)/'processed/domain-review.json',record)
    evidence.seal_bundle(review_id,'AERIS bounded review')
    return {**record,'review_run_id':review_id}


def review_status(review_id):
    from .. import evidence
    from . import factory,catalog
    try:
        if not evidence.validate_bundle(review_id).get('valid'): raise ValueError('review evidence integrity failed')
        record=factory.read(evidence.bundle_dir(review_id)/'processed/domain-review.json')
        replay=_assess_execution(record['execution_run_id'])
        if catalog.digest(record)!=catalog.digest(replay): raise ValueError('review source/qualification/decision replay mismatch')
        return {'valid':True,'decision':record['decision'],'human_approval':False}
    except (OSError,ValueError,KeyError,TypeError,RuntimeError) as exc:
        return {'valid':False,'decision':'REVIEW_BLOCKED','reason':str(exc)}
