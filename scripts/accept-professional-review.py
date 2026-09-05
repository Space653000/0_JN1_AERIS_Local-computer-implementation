"""Retain a real rejected claim and its evidence-bounded correction, without Human approval."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from aeris_runtime.engineering import catalog,factory
from aeris_runtime.engineering.harness import Harness
from aeris_runtime.evidence import create_bundle,bundle_dir,seal_bundle,validate_bundle


def main():
    acceptance=factory.read(factory.STATE/'PROFESSIONAL_ACCEPTANCE.json')
    ref=acceptance['skill_workflows'][0]['evidence_run_id']
    if not validate_bundle(ref)['valid']: raise ValueError('source Evidence invalid')
    bad={'classification':'EVIDENCE','evidence_refs':[ref],'uncertainty':'model only',
         'counter_hypothesis':'fixture may explain this','source_kind':'SYNTHETIC','real_measurement_verified':True}
    params={'executor_role':'R001','reviewer_role':'R098','approved_evidence_refs':[ref],'claims':[bad]}
    rejected=catalog.execute('evidence-counterreview',params)
    corrected={**bad,'real_measurement_verified':False}
    accepted=catalog.execute('evidence-counterreview',{**params,'claims':[corrected]})
    if rejected['values']['decision']=='BASELINE_REVIEW_PASS' or accepted['values']['decision']!='BASELINE_REVIEW_PASS':
        raise AssertionError('counterargument/correction did not change the decision')
    report={'original_claim':bad,'rejected_review':rejected,'corrected_claim':corrected,'corrected_review':accepted,
            'human_approval':False,'source_evidence':ref,'correction':'Remove unsupported physical verification; retain synthetic computational evidence only.'}
    bundle=create_bundle('PROFESSIONAL-REVIEW-CORRECTION','R098',method_snapshot={'skill_id':'evidence-counterreview'})
    run_id=bundle['run_id']; factory.write(bundle_dir(run_id)/'processed'/'review-correction.json',report)
    seal_bundle(run_id,'R099')
    if not validate_bundle(run_id)['valid']: raise AssertionError('review evidence failed sealing')
    harness=Harness(); project=acceptance['project_id']
    for kind,payload in [('FAILURE_LIBRARY',{'rejected_claim':bad,'findings':rejected['values']}),
                         ('DECISION_MEMORY',{'correction':report['correction'],'decision':accepted['values']}),
                         ('CROSS_ROLE_REVIEW',{'executor':'R001','reviewer':'R098','curator':'R099'})]:
        harness.append(project,kind,{**payload,'evidence_run_ids':[run_id]},'R098')
    harness.distill(project)
    factory.write(factory.STATE/'REVIEW_CORRECTION_ACCEPTANCE.json',{'result':'PASS','run_id':run_id,**report,'harness':harness.verify()})
    print('COUNTERREVIEW_REJECT_CORRECT_SEAL=PASS')


if __name__=='__main__': main()
