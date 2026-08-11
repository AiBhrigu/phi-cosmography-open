#!/usr/bin/env python3
from __future__ import annotations
import csv,io,hashlib
import cosmography_engine_v1_1_encrypted_jpl_input_capsule_v02 as base

def vector_with_source_adapter(sp):
    attempts=[('NUMERIC_COMMON',str(sp)),('DES_EXPLICIT_FALLBACK',f'DES={sp};')]
    for mode,command in attempts:
        p={'format':'json','COMMAND':base.qq(command),'OBJ_DATA':base.qq('NO'),'MAKE_EPHEM':base.qq('YES'),'EPHEM_TYPE':base.qq('VECTORS'),'CENTER':base.qq('500@10'),'TLIST':base.qq(f'{base.T0_JD:.12f}'),'TLIST_TYPE':base.qq('JD'),'TIME_TYPE':base.qq('TDB'),'REF_PLANE':base.qq('FRAME'),'REF_SYSTEM':base.qq('ICRF'),'OUT_UNITS':base.qq('AU-D'),'CSV_FORMAT':base.qq('YES'),'VEC_TABLE':base.qq('2')}
        raw,d,u=base.fetch(base.HOR,p,True)
        lines=str(d.get('result') or '').splitlines()
        so=[i for i,x in enumerate(lines) if '$$SOE' in x]; eo=[i for i,x in enumerate(lines) if '$$EOE' in x]
        if not so or not eo or eo[0]<=so[0]:
            continue
        for line in lines[so[0]+1:eo[0]]:
            f=[x.strip() for x in next(csv.reader(io.StringIO(line)))]
            if len(f)>=8:
                try:
                    st=[float(f[k]) for k in range(2,8)]
                    return st,hashlib.sha256(raw).hexdigest(),{'jpl_signature':d.get('signature'),'source_adapter_mode':mode},u
                except Exception:
                    pass
    raise RuntimeError('HORIZONS_VECTOR_BOTH_COMMAND_MODES_FAILED')

base.vector=vector_with_source_adapter
base.NODE='COSMOGRAPHY_DYNAMICAL_ENGINE_V1_1_FRESH_HELDOUT_ENCRYPTED_JPL_INPUT_CAPSULE_v0_3'
if __name__=='__main__':
    base.main()
