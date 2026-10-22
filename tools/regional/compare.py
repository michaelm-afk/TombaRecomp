"""Compare local metadata and reference hashes; never export original bytes."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    discs = {serial: json.loads((args.audit/(serial+'.json')).read_text())
             for serial in ('SCUS-94236','SCES-01330','SCES-01331','SLPS-01144')}
    result = {'discs': {}, 'reference_checks': {}}
    for serial, disc in discs.items():
        result['discs'][serial] = {k:disc[k] for k in ('size','hashes','system_cnf')}
        result['discs'][serial]['file_count'] = len(disc['files'])
        result['discs'][serial]['executables'] = [r for r in disc['files'] if 'exe' in r]
    eu1 = {r['name']:r for r in discs['SCES-01330']['files']}
    eu2 = {r['name']:r for r in discs['SCES-01331']['files']}
    shared = eu1.keys() & eu2.keys()
    result['eu_comparison'] = dict(shared_names=len(shared),
        identical_files=sum(eu1[n]['sha256']==eu2[n]['sha256'] for n in shared),
        different_files=[n for n in sorted(shared) if eu1[n]['sha256']!=eu2[n]['sha256']],
        only_eu1=sorted(eu1.keys()-eu2.keys()),only_eu2=sorted(eu2.keys()-eu1.keys()))
    for profile in ('sces_013.30','sces_013.31','scus_942.36','slps_011.44'):
        checksum = args.reference/'config'/profile/'checksum.sha'
        if not checksum.exists():
            continue
        references = {}
        for line in checksum.read_text().splitlines():
            digest, path = line.split(maxsplit=1)
            references[path.split('/'+profile+'/',1)[1]] = digest
        result['reference_checks'][profile] = {}
        for serial, disc in discs.items():
            actual = {r['name']:r['sha256'] for r in disc['files']}
            result['reference_checks'][profile][serial] = {
                'matched':[n for n,h in references.items() if actual.get(n)==h],
                'mismatched':[n for n,h in references.items() if n in actual and actual[n]!=h]}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('EU shared/identical:',len(shared),result['eu_comparison']['identical_files'])
    for profile, checks in result['reference_checks'].items():
        print(profile, {serial:len(check['matched']) for serial,check in checks.items()})


if __name__ == '__main__':
    main()
