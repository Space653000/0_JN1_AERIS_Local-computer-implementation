"""Same-origin capability API integrated into the existing AERIS control plane."""
from urllib.parse import urlsplit,parse_qs
import threading
import time

from . import catalog,factory
from .harness import Harness
from .orchestration import route_pod,run_role

_matrix_lock=threading.Lock()
_matrix_cache=None
_matrix_at=0.0


def live_matrix():
    global _matrix_cache,_matrix_at
    catalog.implementation_digest()
    factory.acceptance_engine_digest()
    with _matrix_lock:
        if _matrix_cache is None or time.monotonic()-_matrix_at>2:
            _matrix_cache=factory.matrix(); _matrix_cache["cache_max_age_s"]=2
            _matrix_at=time.monotonic()
        return _matrix_cache


def get(url):
    parsed=urlsplit(url); path=parsed.path; query=parse_qs(parsed.query)
    if path=="/api/v1/capabilities": return live_matrix()
    if path=="/api/v1/capabilities/skills":
        return {"skills":[{k:v for k,v in d.items() if k!="fixture"} for d in catalog.definitions().values()]}
    if path.startswith("/api/v1/capabilities/roles/"):
        return factory.load_pack(path.rsplit("/",1)[1])
    if path.startswith("/api/v1/capabilities/fixture/"):
        role=path.rsplit("/",1)[1]; pack=factory.load_pack(role)
        skill=query.get("skill",[pack["required_skills"][0]])[0]
        if skill not in pack["required_skills"]: raise ValueError("fixture outside role scope")
        return {"source_kind":"SYNTHETIC","fixture":factory.fixture_for(role,skill)}
    if path=="/api/v1/capabilities/memory": return Harness().context(query.get("project",["CAPABILITY_FACTORY"])[0])
    if path=="/api/v1/capabilities/knowledge":
        corpus=factory.read(factory.ROOT/"knowledge"/"engineering"/"manifest.json")
        from .knowledge_registry import summary
        classified=summary(corpus,root=factory.ROOT)
        if query.get("q"):
            return catalog.execute("provenance-research",{"query":query["q"][0],"documents":corpus["documents"]})
        return classified
    raise KeyError("capability endpoint not found")


def post(path,payload):
    if path=="/api/v1/capabilities/standards/applicability":
        from ..standards_registry import assess_applicability
        return assess_applicability(payload['record'],payload['context'])
    if path=="/api/v1/capabilities/standards/change-impact":
        from ..standards_registry import change_impact
        return change_impact(payload['previous'],payload['current'],payload['requirement_links'])
    if path=="/api/v1/capabilities/intake":
        from .intake import understand
        return understand(payload["description"],product=payload.get("product",""),transducer=payload.get("transducer","Both"),lifecycle=payload.get("lifecycle","EVT"),project=payload.get("project","CAPABILITY_FACTORY"))
    if path=="/api/v1/capabilities/pod": return route_pod(payload)
    if path=="/api/v1/capabilities/execute":
        return run_role(str(payload["role_id"]),str(payload["skill_id"]),payload["params"],objective=str(payload["objective"]),
                        project_id=payload.get("project_id"),risk=payload.get("risk","R1"),source_kind=payload.get("source_kind","USER_SUPPLIED_UNVERIFIED"),context=payload.get("context"))
    if path=="/api/v1/capabilities/memory":
        return Harness().append(payload["project"],payload["kind"],payload["payload"],payload["actor"])
    if path=="/api/v1/capabilities/retrospective": return Harness().distill(payload["project"])
    if path=="/api/v1/capabilities/reproduce":
        from ..reproduction import reproduce_run
        return reproduce_run(payload["run_id"])
    raise KeyError("capability mutation endpoint not found")
