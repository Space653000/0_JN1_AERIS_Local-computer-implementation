"""Deterministic technical plots and reports, with explicit units and provenance."""
from __future__ import annotations

import html
import math
from pathlib import Path

from .catalog import canonical


def plot(values: dict, params: dict) -> str:
    x=None; y=None; xlabel="sample / index"; ylabel="dimensionless model output"
    choices=[("frequency_hz","amplitude","Hz","amplitude"),("frequency_hz","smoothed_db","Hz","dB"),
             ("frequency_hz","psd_unit2_per_hz","Hz","unit²/Hz"),("angles_deg","normalized_power","degrees","normalized power"),
             ("centers_hz","band_power_unit2","Hz","unit²"),("frequency_hz","absorption_normal_incidence","Hz","absorption"),
             ("time_s","temperature_c","s","degrees C")]
    for xkey,ykey,xunit,yunit in choices:
        if isinstance(values.get(ykey),list):
            y=values[ykey]; x=values.get(xkey,params.get(xkey)); xlabel=xunit; ylabel=yunit; break
    if y is None:
        for key,value in values.items():
            if isinstance(value,list) and value and all(isinstance(v,(float,int)) and not isinstance(v,bool) for v in value):
                y=value; ylabel=key; break
    if y is None:
        pairs=[(key,float(value)) for key,value in values.items() if isinstance(value,(float,int)) and not isinstance(value,bool)]
        y=[v for _,v in pairs] or [0]; ylabel="scalar metrics (see labeled JSON units)"
    if x is None or not isinstance(x,list) or len(x)!=len(y): x=list(range(len(y)))
    if not y: y=[0]; x=[0]
    if not all(math.isfinite(float(v)) for v in [*x,*y]): raise ValueError("cannot plot nonfinite values")
    xmin,xmax=min(x),max(x); ymin,ymax=min(y),max(y)
    dx=xmax-xmin or 1; dy=ymax-ymin or 1
    step=max(1,len(y)//1500)
    points=" ".join(f"{70+(a-xmin)/dx*700:.3f},{330-(b-ymin)/dy*270:.3f}" for a,b in zip(x[::step],y[::step]))
    labels=[]
    for i in range(5):
        labels.append(f'<text x="{70+i*175}" y="352">{xmin+dx*i/4:.4g}</text>')
        labels.append(f'<text x="8" y="{334-i*67.5}">{ymin+dy*i/4:.4g}</text>')
    return '<svg xmlns="http://www.w3.org/2000/svg" width="840" height="400" viewBox="0 0 840 400"><rect width="840" height="400" fill="white"/><g fill="#222" font-family="sans-serif" font-size="12"><text x="70" y="25">FREE_LOCAL_BASELINE — analytical output; not calibrated measurement</text><path d="M70 50 V330 H780" fill="none" stroke="#555"/><polyline points="'+points+'" stroke="#087f8c" fill="none"/>'+''.join(labels)+f'<text x="330" y="383">{html.escape(xlabel)}</text><text x="70" y="44">{html.escape(ylabel)}</text></g></svg>'


def write_artifacts(root: Path, params: dict, result: dict, context=None):
    context=context or {"source_kind":"UNVERIFIED_UNSPECIFIED","physical_verification":False}
    (root/"raw"/"engineering-context.json").write_bytes(canonical(context)+b"\n")
    (root/"raw"/"engineering-input.json").write_bytes(canonical(params)+b"\n")
    (root/"plots"/"engineering.svg").write_text(plot(result["values"],params),encoding="utf-8")
    lines=[f"# {result['skill_id']} — numerical engineering report", "", "Tool layer: FREE_LOCAL_BASELINE.",
           "",f"Source kind: {context['source_kind']} (not calibrated measurement).",
           "",f"Method version: {result['version']}",f"Input SHA-256: {result['input_sha256']}",
           f"Implementation SHA-256: {result['implementation_sha256']}","","## Results",""]
    for key,value in result["values"].items():
        text=str(value) if not isinstance(value,list) else f"{len(value)} values; full array in processed/skill_result.json"
        lines.append(f"- {key}: {text}")
    lines += ["","## Uncertainty and counter-hypotheses","",result["uncertainty"],
              "","Wrong geometry, units, excitation, data window or fixture could explain the result. Check these alternatives before making a physical product claim.",
              "","## Reproduction","","Replay the sealed raw engineering-input.json with the same method/source version. No Human or licensed-tool approval is granted."]
    (root/"report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
