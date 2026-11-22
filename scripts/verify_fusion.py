
from pathlib import Path  # compare two completed rq2 runs; does not train or modify the accepted baseline
from dataclasses import asdict
import argparse
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.files import ROOT, read_csv, write_json, text_sha256
from src.fusion import completed_run, Normalizer, accepted_scores, fuse_scores
from src.blur import assert_equal_scores
from src.fusion_reporting import verify_metrics


def verify(first,second,output,root=ROOT):  # compare two completed rq2 runs against the accepted baseline and normalization fit
    root,output=Path(root),Path(output)
    if first==second:
        raise ValueError('Choose two distinct completed run IDs')
    if output.exists():
        raise FileExistsError('Verification output exists; choose a fresh path')
    pointer,_,_,_,trials,tables=accepted_scores(root)
    data=[]
    for run_id in [first,second]:
        folder,metadata=completed_run(root,run_id,'rq2')
        norm=Normalizer.load(folder/'normalizer.json')
        if norm.baseline_id!=pointer['run_id'] or norm.validation_sha256!=pointer['score_sha256']['validation_scores.csv']:
            raise ValueError('Normalizer uses different baseline inputs')
        rows=read_csv(folder/'rq2_fusion_scores.csv')
        verify_metrics(rows,metadata['test_metrics'])
        expected=fuse_scores(tables['test'],tables['test'],norm,trials['test'])
        fields=['face_score_raw','palm_score_raw','face_score_normalized','palm_score_normalized','fusion_score']
        assert_equal_scores(rows,expected,fields)
        data.append((folder,metadata,norm,rows))
    if asdict(data[0][2])!=asdict(data[1][2]):
        raise ValueError('Normalizer parameters differ between runs')
    difference=assert_equal_scores(data[0][3],data[1][3],fields)
    if data[0][1]['test_metrics']!=data[1][1]['test_metrics']:
        raise ValueError('Metrics differ between runs')
    report={'status':'passed','runs':[first,second], 'baseline_id':pointer['run_id'],
            'trial_count':len(data[0][3]),'maximum_absolute_score_difference':difference,
            'identical_normalizer_parameters':True,'recomputed_exported_metrics':True,
            'score_file_sha256':[text_sha256(d[0]/'rq2_fusion_scores.csv') for d in data],
            'scope':'RQ2 repeatability from accepted score files; not raw-model/RQ1 or real RQ3 reproduction'}
    write_json(output,report)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Compare two completed RQ2 runs; does not train or modify the accepted baseline.')
    parser.add_argument('--first',required=True)
    parser.add_argument('--second',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    print(verify(args.first,args.second,args.output))
