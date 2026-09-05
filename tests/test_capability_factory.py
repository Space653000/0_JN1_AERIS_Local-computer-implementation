import copy
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aeris_runtime.engineering import catalog,factory
from aeris_runtime.engineering.harness import Harness,KINDS
from aeris_runtime.engineering.orchestration import route_pod


class CapabilityFactoryTests(unittest.TestCase):
    def test_all_canonical_seats_have_complete_domain_packs(self):
        roles=factory.canonical_roles()
        self.assertEqual(len(roles),100)
        for role in roles:
            with self.subTest(role=role["id"]):
                pack=factory.load_pack(role["id"])
                self.assertEqual(factory.contract_errors(pack),[])
                self.assertEqual(pack["identity"],role)
                self.assertTrue(pack["required_skills"])
                self.assertNotEqual(pack["review_requirements"]["reviewer"],role["id"])

    def test_twenty_four_product_packs_have_distinct_architecture_and_executable_plans(self):
        topologies=set()
        for i in range(45,69):
            role=f"R{i:03d}"; pack=factory.load_pack(role)
            topologies.add(pack["product_architecture"]["speaker_topology_considerations"])
            fixture=factory.fixture_for(role,"product-system-plan")
            out=catalog.execute("product-system-plan",fixture["input"])
            self.assertTrue(all(c["passed"] for c in catalog.verify_checks(out["values"],fixture["checks"])))
        self.assertEqual(len(topologies),24)

    def test_bad_seat_and_skill_cannot_escape_scope(self):
        for role in ("../../.env","R000","R101","r001"):
            with self.assertRaises(ValueError): factory.load_pack(role)
        with self.assertRaises(KeyError): catalog.execute("../../private",{})

    def test_metadata_label_cannot_upgrade_maturity(self):
        pack=factory.load_pack("R009"); modified=copy.deepcopy(pack)
        modified["current_maturity_level"]="L4"
        self.assertEqual(factory.pack_digest(pack),factory.pack_digest(modified))
        # A failed integrity check removes all execution-derived maturity.
        with patch.object(factory,"validate_bundle",return_value={"valid":False}):
            result=factory.matrix()
        self.assertEqual(result["100_role_L2"],0)
        self.assertEqual(result["maturity_counts"]["L4"],0)

    def test_capability_router_needs_actual_available_skills_not_keywords(self):
        roles=[]
        for role in factory.canonical_roles():
            skills=factory.load_pack(role['id'])['required_skills']
            roles.append({**role,"level":"L2","skills":skills,'executable_skills':skills})
        request={"product":"TWS Earbuds","transducer":"Microphone","lifecycle":"EVT","risk":"R1",
                 "requirement":"bound known delay","required_evidence":["numerical lag check"],
                 "needed_skills":["gcc-phat-tdoa"],"available_tools":["FREE_LOCAL_BASELINE"]}
        pod=route_pod(request,{"roles":roles})
        self.assertEqual(pod["lead"],"R048")
        self.assertEqual(pod["uncovered_skills"],[])
        # Execution fixtures do not establish independent review qualification.
        self.assertIsNone(pod['reviewer'])
        self.assertFalse(pod['pod_complete'])
        for lifecycle in ('Architecture','Prototype','Field Return'):
            core_pod=route_pod({**request,'transducer':'microphone','lifecycle':lifecycle},{'roles':roles})
            self.assertEqual(core_pod['state'],'EXECUTION_READY_REVIEW_BLOCKED')
            self.assertEqual(core_pod['request']['transducer'],'Microphone')
        unavailable=route_pod({**request,"available_tools":[]},{"roles":roles})
        self.assertEqual(unavailable["state"],"BLOCKED")
        with self.assertRaises(ValueError): route_pod({"query":"lots of microphone keywords"},{"roles":roles})
        label_only=[{k:v for k,v in role.items() if k!='executable_skills'} for role in roles]
        rejected=route_pod(request,{'roles':label_only})
        self.assertEqual(rejected['state'],'BLOCKED')
        self.assertEqual(rejected['uncovered_skills'],['gcc-phat-tdoa'])
        wrong_executor=route_pod({**request,'execution_role_id':'R016'},{'roles':roles})
        self.assertEqual(wrong_executor['state'],'BLOCKED')
        self.assertFalse(wrong_executor['software_execution_permitted'])

    def test_partial_role_routes_only_its_exact_evidenced_skill(self):
        request={"product":"","transducer":"Speaker","lifecycle":"EVT","risk":"R1",
                 "requirement":"bounded execution","required_evidence":["sealed numerical run","independent counterreview"],
                 "needed_skills":["speaker-power-distortion-baseline"],"available_tools":["FREE_LOCAL_BASELINE"],
                 "execution_role_id":"R016","source_kind":"SYNTHETIC"}
        partial={"id":"R016","name":"Speaker Power & Linearity","group":"Speaker CoE","level":"L1",
                 "skills":["speaker-power-distortion-baseline","speaker-fr-reference-baseline"],
                 "executable_skills":["speaker-power-distortion-baseline"]}
        pod=route_pod(request,{"roles":[partial]})
        self.assertTrue(pod['software_execution_permitted'])
        self.assertEqual(pod['executors'],['R016'])
        blocked=route_pod({**request,"needed_skills":["speaker-fr-reference-baseline"]},{"roles":[partial]})
        self.assertFalse(blocked['software_execution_permitted'])

    def test_memory_is_append_only_and_cannot_mutate_evidence(self):
        temp_root=factory.ROOT/".aeris"/"test-temp"; temp_root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as directory:
            harness=Harness(Path(directory)/"memory.sqlite3")
            for kind in KINDS:
                event=harness.append("test",kind,{"memory_is_evidence":True,"text":"synthetic memory"},"test")
                self.assertFalse(event["payload"]["memory_is_evidence"])
            self.assertTrue(harness.verify()["valid"])
            with harness.connect() as conn:
                with self.assertRaises(sqlite3.IntegrityError): conn.execute("UPDATE events SET actor='forged'")
                with self.assertRaises(sqlite3.IntegrityError): conn.execute("DELETE FROM events")
            with self.assertRaises(ValueError): harness.append("test","LESSON_MEMORY",{"evidence_run_ids":["MISSING-BUNDLE"]},"test")
            self.assertFalse(harness.context("test")["memory_is_evidence"])
