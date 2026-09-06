"""Real local acceptance: 100 seats, 42 distinct Skills, 24 Product Chief workflows."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from aeris_runtime.controlplane import ControlStore
from aeris_runtime.engineering import catalog,factory
from aeris_runtime.engineering.harness import Harness
from aeris_runtime.engineering.orchestration import run_role
from aeris_runtime.evidence import validate_bundle
from aeris_runtime.reproduction import reproduce_run


def main():
    matrix=factory.matrix()
    if matrix["100_role_L2"]!=100: raise AssertionError("all 100 seats must have current executable evidence first")
    store=ControlStore(); project=store.create_project("Professional Company Acceptance — synthetic engineering cases")
    runs=[]
    for skill in catalog.definitions():
        role=next(r for r in matrix["roles"] if skill in r["skills"])
        fixture=factory.fixture_for(role["id"],skill)
        result=run_role(role["id"],skill,fixture["input"],objective=fixture["reason"],project_id=project["id"],source_kind="SYNTHETIC")
        check=reproduce_run(result["evidence_run_id"])
        if result["state"]!="EVIDENCED" or check["result"]!="PASS": raise AssertionError((skill,result["state"],check))
        if store.get_task(result["task_id"])["state"]!="EVIDENCED": raise AssertionError("SQLite state is stale")
        root=factory.ROOT/".aeris"/"evidence"/result["evidence_run_id"]
        if not (root/"plots"/"engineering.svg").is_file() or not (root/"report.md").is_file(): raise AssertionError("missing technical artifact")
        if factory.read(root/"raw"/"engineering-context.json")["source_kind"]!="SYNTHETIC": raise AssertionError("source classification not sealed")
        runs.append({"role_id":role["id"],"skill_id":skill,"workflow_id":result["workflow_id"],"evidence_run_id":result["evidence_run_id"],"reproduction":check["result"]})
        print(f"SKILL {skill}: EVIDENCED + REPRODUCED",flush=True)
    products=[]
    for i in range(45,69):
        role=f"R{i:03d}"; fixture=factory.fixture_for(role,"product-system-plan")
        result=run_role(role,"product-system-plan",fixture["input"],objective=fixture["input"]["objective"],project_id=project["id"],source_kind="SYNTHETIC")
        if result["pod"]["lead"]!=role or result["pod"]["executors"]!=[role]: raise AssertionError("wrong Product Chief assignment")
        if not validate_bundle(result["evidence_run_id"])["valid"]: raise AssertionError("product evidence integrity failed")
        products.append({"role_id":role,"workflow_id":result["workflow_id"],"evidence_run_id":result["evidence_run_id"],"state":result["state"]})
        print(f"PRODUCT {role}: SQLITE + WORKFLOW + POD + EVIDENCE",flush=True)
    matrix=factory.matrix(); factory.write(factory.STATE/"CAPABILITY_MATRIX.json",matrix)
    report={"result":"PASS","assessed_at_utc":factory.now(),"implementation_sha256":catalog.implementation_digest(),
            "matrix_counts":matrix["maturity_counts"],"100_role_L2":matrix["100_role_L2"],"project_id":project["id"],
            "skill_workflows":runs,"product_chief_workflows":products,"harness_integrity":Harness().verify(),
            "unresolved_capability_gaps":matrix["unresolved_capability_gaps"],"source_kind":"SYNTHETIC","physical_or_licensed_verification":False}
    factory.write(factory.STATE/"PROFESSIONAL_ACCEPTANCE.json",report)
    print("PROFESSIONAL_COMPANY_ACCEPTANCE=PASS",flush=True)
    return 0


if __name__=="__main__": raise SystemExit(main())
