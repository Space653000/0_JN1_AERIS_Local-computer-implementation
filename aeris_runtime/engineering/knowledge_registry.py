"""Source classification and provenance for engineering Knowledge (not Evidence)."""
from collections import Counter
import hashlib
import json
import re
from pathlib import Path

from ..config import ROOT

SOURCE_KINDS=('PUBLIC_EXTERNAL','OPEN_ACCESS_RESEARCH','PUBLIC_MANUFACTURER',
              'PUBLIC_STANDARDS_METADATA','USER_OWNED','AERIS_AUTHORED','SYNTHETIC','GENERATED_DERIVATION')
EXTERNAL_KINDS=set(SOURCE_KINDS[:4])


def authored_registry(corpus, *, root: Path=ROOT):
    """Classify legacy notes by observed provenance, not their marketing category."""
    role_refs={}
    for path in sorted((root/'company/capabilities').glob('R*/capability.json')):
        pack=json.loads(path.read_text(encoding='utf-8-sig'))
        for ref in pack.get('required_knowledge',[]):
            role_refs.setdefault(ref,[]).append(pack['identity']['id'])
    records=[]; seen=set()
    for note in corpus['documents']:
        identifier=note['id']
        if not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]*',identifier): raise ValueError('unsafe knowledge identifier')
        if identifier in seen: raise ValueError('duplicate knowledge source ID')
        seen.add(identifier)
        actual=hashlib.sha256(note['text'].encode('utf-8')).hexdigest()
        if actual!=note['sha256']: raise ValueError('knowledge note content hash mismatch: '+identifier)
        kind=('SYNTHETIC' if note.get('rights')=='SYNTHETIC' else
              'GENERATED_DERIVATION' if note.get('source_kind')=='GENERATED_METHOD_NOTE' else 'AERIS_AUTHORED')
        # PUBLIC_METADATA without source URL/retrieval evidence is an authored
        # bibliographic note, not a retrieved public standards document.
        note_name=identifier.removeprefix('METHOD-') if identifier.startswith('METHOD-') else identifier
        relative=f'knowledge/engineering/{note_name}.json'
        path=(root/relative).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            raise ValueError('missing or unsafe knowledge note file')
        on_disk=json.loads(path.read_text(encoding='utf-8-sig'))
        if on_disk.get('text')!=note['text'] or on_disk.get('sha256')!=actual:
            raise ValueError('knowledge manifest and source note drift')
        mapped=role_refs.get(relative,[])
        if re.fullmatch('PRODUCT-R[0-9]{3}',identifier): mapped=[identifier[-4:]]
        records.append({'id':identifier,'title':note['title'],'source_kind':kind,
            'author':'AERIS local engineering factory','source_url':None,'source_path':relative,
            'rights':note.get('rights','UNKNOWN'),'retrieved_at_utc':None,
            'retrieval_state':'NOT_RETRIEVED_EXTERNALLY','sha256':actual,'sha256_scope':'note text UTF-8',
            'domain_tags':[note['category']],'mapped_roles':sorted(set(mapped)),
            'provenance_pointer':note['source'],'is_evidence':False,
            'external_professional_document':False})
    return records


def summary(corpus, *, root: Path=ROOT):
    records=authored_registry(corpus,root=root)
    counts={kind:0 for kind in SOURCE_KINDS}
    counts.update(Counter(r['source_kind'] for r in records))
    return {'documents':len(records),'categories':corpus['categories'],'counts_by_source_kind':counts,
            'external_retrieved_documents':sum(counts[k] for k in EXTERNAL_KINDS),
            'source_registry':records,'memory_is_evidence':False,
            'truth':'Authored notes, synthetic cases and generated derivations are counted separately from retrieved external documents.'}
