
import argparse  # audit completed rq2/rq3 exports and write one rq1-rq3 master table
from dataclasses import asdict
import json
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.files import ROOT, read_csv, write_csv, write_json
from src.fusion import (accepted_scores, completed_run, Normalizer, fuse_scores,
                        validate_coverage, RQ2_FIELDS, RQ3_FIELDS)
from src.blur import assert_equal_scores, validate_sigmas
from src.fusion_reporting import verify_metrics

FIELDS=['face_score_raw','palm_score_raw','face_score_normalized','palm_score_normalized','fusion_score']
METRICS=['eer','auc','d_prime','genuine_count','impostor_count']


def review(rq2_id,rq3_id,repeat_id,output,root=ROOT):  # audit completed score tables, frozen inputs and repeat runs across the three research questions
    root,output=Path(root),Path(output)
    if output.exists():
        raise FileExistsError('Use a fresh audit output directory')
    if rq3_id==repeat_id:
        raise ValueError('Repeat run must be distinct')
    pointer,baseline,_,_,trials,tables=accepted_scores(root)
    folder2,m2=completed_run(root,rq2_id,'rq2')
    norm=Normalizer.load(folder2/'normalizer.json')
    fitted=Normalizer.fit(tables['validation'],trials['validation'],split='validation',
                          validation_sha256=pointer['score_sha256']['validation_scores.csv'],
                          baseline_id=pointer['run_id'])
    if asdict(norm)!=asdict(fitted):
        raise ValueError('Stored normalizer is not the accepted validation-only fit')
    clear=read_csv(folder2/'rq2_fusion_scores.csv')
    if list(clear[0])!=RQ2_FIELDS:
        raise ValueError('RQ2 schema differs from the contract')
    wanted=fuse_scores(tables['test'],tables['test'],norm,trials['test'])
    assert_equal_scores(clear,wanted,FIELDS)
    verify_metrics(clear,read_csv(folder2/'master_metrics.csv'))
    verify_metrics(clear,m2['test_metrics'])
    previous=None
    audit=[]
    master=[]
    for r in baseline['test_metrics']:
        master.append(dict(question='RQ1',run_id=pointer['run_id'],blur_sigma=0.,modality=r['modality'],
                           **{k:r[k] for k in METRICS}))
    for r in m2['test_metrics']:
        master.append(dict(question='RQ2',run_id=rq2_id,blur_sigma=0.,modality=r['modality'],
                           **{k:r[k] for k in METRICS}))
    for run_id in [rq3_id,repeat_id]:
        folder,metadata=completed_run(root,run_id,'rq3')
        if metadata['rq2_run_id']!=rq2_id or metadata['normalization']!=asdict(norm):
            raise ValueError('RQ3 parent or frozen normalization differs')
        plan=json.loads((folder/'blur_plan.json').read_text())
        sigmas=validate_sigmas(plan['sigmas'])
        if not plan['reviewed'] or not plan['review_note'].strip() or plan['selection_split']!='validation':
            raise ValueError('Missing validation plan review')
        rows=read_csv(folder/'rq3_blur_scores.csv')
        summary=read_csv(folder/'master_metrics.csv')
        if list(rows[0])!=RQ3_FIELDS or set(float(r['blur_sigma']) for r in rows)!=set(sigmas):
            raise ValueError('RQ3 schema or sigma coverage differs')
        if len(summary)!=3*len(sigmas):
            raise ValueError('Master table needs every system at every sigma')
        if previous is not None and rows!=previous:
            raise ValueError('Repeat run changed a score, label or row order')
        for sigma in sigmas:
            subset=[r for r in rows if float(r['blur_sigma'])==sigma]
            validate_coverage(subset,trials['test'],FIELDS)
            recomputed=fuse_scores(subset,subset,norm,trials['test'])
            assert_equal_scores(subset,recomputed,FIELDS)
            assert_equal_scores(subset,clear,['palm_score_raw','palm_score_normalized'])
            selected=[r for r in summary if float(r['blur_sigma'])==sigma]
            if {r['modality'] for r in selected}!={'face','palm','fusion'} or len(selected)!=3:
                raise ValueError('Missing or duplicate modality in master table')
            verify_metrics(subset,selected)
            verify_metrics(subset,[r for r in metadata['test_metrics'] if r['blur_sigma']==sigma])
            if sigma==0:
                zero=assert_equal_scores(subset,clear,FIELDS,atol=1e-12)
                verify_metrics(subset,m2['test_metrics'])
            if run_id==rq3_id:
                for r in selected:
                    master.append(dict(question='RQ3',run_id=run_id,blur_sigma=sigma,modality=r['modality'],
                                       **{k:float(r[k]) if k not in ['genuine_count','impostor_count'] else int(r[k]) for k in METRICS}))
        audit.append(dict(run_id=run_id,rows=len(rows),sigmas=list(sigmas),sigma_zero_max_difference=zero))
        previous=rows
    output.mkdir(parents=True)
    write_csv(output/'study_master_metrics.csv',master)
    report={'status':'passed','rq2_run':rq2_id,'rq3_runs':audit,'repeat_exact':True,
            'verified':['completed artifact hashes','exact score schemas','all trial keys and labels',
                        'validation-only fitted parameters','frozen equal-weight equation for every row',
                        'sigma-zero scores and metrics within 1e-12','exact unchanged palm scores',
                        'all exported metrics recomputed','all repeated scores identical'],
            'scope':'saved-score integration audit; raw-palm refitting and human team acceptance are separate'}
    write_json(output/'integration_audit.json',report)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Audit completed RQ2/RQ3 exports and write one RQ1-RQ3 master table.')
    parser.add_argument('--rq2-run',required=True)
    parser.add_argument('--rq3-run',required=True)
    parser.add_argument('--repeat-run',required=True)
    parser.add_argument('--output',required=True)
    a=parser.parse_args()
    print(review(a.rq2_run,a.rq3_run,a.repeat_run,a.output))
