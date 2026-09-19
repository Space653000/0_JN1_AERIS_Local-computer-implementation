import json, re, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ALLOW={"API","SHA","HTTP","JSON","Runtime","Evidence","PASS","BLOCKED","UNKNOWN","Ollama","Git","Python","PowerShell","AERIS","SQLite","FREE_BASELINE","LOCAL","G0","G1","G2","G3","G4","G5","R0","R1","R2","R3","R4","P0","P1","P2","P3","P4","P5","P6"}
class SiteZhTwTests(unittest.TestCase):
 def test_dictionary_contains_forbidden_ui_terms(self):
  d=json.loads((ROOT/"ui/web/zh-TW.json").read_text(encoding="utf-8"))
  for term in ("Dashboard","Workspace","Activity","Roles","Capabilities","Research","Skills","Standards","Evidence","Services","Capability Library","100-Seat Role Library","Chief Acoustic Architect","Speaker Engineering Director","Microphone Engineering Director","Product Audio System Architect"):
   self.assertIn(term,d)
   self.assertNotEqual(term,d[term])
 def test_ui_has_zh_hant_documents(self):
  for p in (ROOT/"ui/web").glob("*.html"):
   self.assertIn('lang="zh-Hant"',p.read_text(encoding="utf-8"))
