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
_matrix_refreshing=False
# factory.matrix() cost scales with the local evidence store (one
# validate_bundle per sealed RUN- directory across all 100 roles) and can
# take well over a minute on a store with 1000+ bundles -- the original
# design (recompute synchronously, inline, whenever the cache is >2s old)
# meant nearly every request blocked for the full computation. This mirrors
# aeris_runtime.telemetry.TelemetryProjection's pattern instead: serve the
# last-known matrix immediately and refresh it in the background, only
# blocking the caller on the very first cold-start call when no cache exists
# yet.
_MATRIX_REFRESH_AFTER_S=20.0


def _decorate(matrix):
    # Source-of-truth presentation fields keep canonical skill IDs stable.
    labels={
        "engineering-requirements":"工程需求分析","lumped-speaker":"集中參數揚聲器分析",
        "microphone-sensitivity":"麥克風靈敏度分析","free-local-acoustic-baseline":"免費本機聲學基準",
    }
    capability_items = matrix.get("capabilities",[])
    if isinstance(capability_items, dict):
        capability_items = list(capability_items.values())
    for item in capability_items:
        sid=item.get("skill_id") or item.get("id") or item.get("capability")
        item["display_name"] = labels.get(sid, "本機能力：" + str(sid))
        item["display_description"] = "可重現的本機分析能力；結果仍須依證據與人工關卡判定。"
    return matrix


def _refresh_matrix():
    global _matrix_cache,_matrix_at,_matrix_refreshing
    try:
        result=_decorate(factory.matrix())
    except Exception:
        with _matrix_lock:
            _matrix_refreshing=False
        raise
    with _matrix_lock:
        _matrix_cache=result; _matrix_at=time.monotonic(); _matrix_refreshing=False


def live_matrix():
    global _matrix_refreshing
    catalog.implementation_digest()
    factory.acceptance_engine_digest()
    with _matrix_lock:
        cache=_matrix_cache
        age=None if cache is None else time.monotonic()-_matrix_at
        stale=cache is None or age>=_MATRIX_REFRESH_AFTER_S
        start_refresh = stale and not _matrix_refreshing
        if start_refresh:
            _matrix_refreshing=True
    if cache is None:
        # Cold start: nothing to serve yet, so this one call has to wait.
        _refresh_matrix()
        with _matrix_lock:
            return _matrix_cache
    if start_refresh:
        threading.Thread(target=_refresh_matrix,daemon=True,name="aeris-matrix-refresh").start()
    result=dict(cache)
    result["snapshot_age_s"]=age
    result["cache_max_age_s"]=_MATRIX_REFRESH_AFTER_S
    result["refresh_in_progress"]=_matrix_refreshing
    return result


def get(url):
    parsed=urlsplit(url); path=parsed.path; query=parse_qs(parsed.query)
    if path=="/api/v1/capabilities": return live_matrix()
    if path=="/api/v1/capabilities/skills":
        from .domain_methods import HANDLERS
        domain=[factory.read(factory.ROOT/f'skills/{skill}/manifest.json') for skill in HANDLERS]
        return {"skills":[{k:v for k,v in d.items() if k!="fixture"} for d in catalog.definitions().values()]+domain}
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
