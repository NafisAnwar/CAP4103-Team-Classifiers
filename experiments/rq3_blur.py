from pathlib import Path
import argparse
from dataclasses import asdict
import json
import sys
import uuid
import joblib
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.files import ROOT, read_csv, write_csv, write_json, text_sha256
from src.datasets import dataset_images
from src.experiment_support import RunArtifacts, load_frozen_models
from src.fusion import accepted_scores, completed_run, Normalizer, fuse_scores, require_assets, RQ3_FIELDS
from src.blur import prepare_plan, load_plan, frozen_face_scores, assert_equal_scores, DEFAULT_SIGMAS
from src.fusion_reporting import evaluate_conditions, verify_metrics, comparison_plot


def run(rq2_run_id, plan_path, run_id=None, root=ROOT, model_run_id=None):
    root, plan_path = Path(root), Path(plan_path)
    pointer, baseline, config, partitions, trials, tables = accepted_scores(root)
    rq2_folder, rq2_metadata = completed_run(root, rq2_run_id, 'rq2')
    normalizer_path = rq2_folder/'normalizer.json'
    normalizer = Normalizer.load(normalizer_path)
    if (normalizer.baseline_id != pointer['run_id'] or rq2_metadata['baseline_id'] != pointer['run_id']
        or normalizer.validation_sha256 != pointer['score_sha256']['validation_scores.csv']
        or asdict(normalizer) != rq2_metadata['normalization']):
        raise ValueError('RQ2 normalizer does not match accepted validation scores')
    models_paths = [root/info['path'] if model_run_id is None else
                   root/'data/processed/models'/model_run_id/f'{m}.joblib'
                   for m,info in baseline['models'].items()]
    require_assets(models_paths + [root/'data/raw/face/olivetti.npz'])
    models, _ = load_frozen_models(root,model_run_id=model_run_id)
    plan = load_plan(plan_path,root)
    plan_hash, norm_hash = text_sha256(plan_path), text_sha256(normalizer_path)
    models_hash = {m:joblib.hash(model) for m,model in models.items()}
    faces = dataset_images([r for r in partitions if r['modality']=='face'], 'test',root)['face']
    clear = read_csv(rq2_folder/'rq2_fusion_scores.csv')
    with RunArtifacts(root,run_id or 'rq3_'+uuid.uuid4().hex[:12],latest_name='rq3_latest.json') as artifacts:
        write_json(artifacts.metrics_dir/'blur_plan.json',plan)
        sweeps = frozen_face_scores(models['face'],faces,trials['test'],plan['sigmas'])
        all_rows, summary = [], []
        for index, sigma in enumerate(plan['sigmas']):
            rows = fuse_scores(sweeps[sigma],tables['test'],normalizer,trials['test'])
            assert_equal_scores(rows,clear,['palm_score_raw','palm_score_normalized'])
            if sigma == 0:
                zero_difference = assert_equal_scores(rows,clear,['face_score_raw','palm_score_raw','face_score_normalized',
                                               'palm_score_normalized','fusion_score'], atol=1e-12)
            exported = [{k:row[k] for k in RQ3_FIELDS if k!='blur_sigma'} for row in rows]
            for row in exported:
                row['blur_sigma'] = sigma
            all_rows.extend(exported)
            condition = f'rq3_level_{index:02d}_sigma_{sigma:g}'.replace('.','p')
            summary.extend(evaluate_conditions(rows,artifacts,condition,sigma))
        scores_path = artifacts.metrics_dir/'rq3_blur_scores.csv'
        write_csv(scores_path,all_rows,RQ3_FIELDS)
        exported = read_csv(scores_path)
        for sigma in plan['sigmas']:
            subset = [r for r in exported if float(r['blur_sigma'])==sigma]
            verify_metrics(subset,[r for r in summary if r['blur_sigma']==sigma])
        zero_rows = [r for r in exported if float(r['blur_sigma']) == 0]
        verify_metrics(zero_rows, rq2_metadata['test_metrics']) #roundoff must not change the clear-condition metrics
        palm_metrics = [r for r in summary if r['modality']=='palm']
        for field in ['eer','auc','d_prime','genuine_count','impostor_count']:
            if any(r[field] != palm_metrics[0][field] for r in palm_metrics):
                raise ValueError('Palm metrics changed across conditions')
        write_csv(artifacts.metrics_dir/'master_metrics.csv',summary)
        comparison_plot(summary,artifacts.figures_dir/'rq3_comparison.png','RQ3: frozen fusion under facial blur')
        if (text_sha256(plan_path)!=plan_hash or text_sha256(normalizer_path)!=norm_hash
            or asdict(normalizer)!=rq2_metadata['normalization']
            or models_hash!={m:joblib.hash(model) for m,model in models.items()}):
            raise ValueError('Frozen inputs changed during the sweep')
        load_frozen_models(root,model_run_id=model_run_id)
        completed_run(root,rq2_run_id,'rq2')
        required = sorted(artifacts.metrics_dir.glob('*.csv'))+sorted(artifacts.metrics_dir.glob('*_metrics.json'))
        required += [artifacts.metrics_dir/'blur_plan.json']+sorted(artifacts.figures_dir.glob('*.png'))
        result = artifacts.complete({'experiment':'rq3','baseline_id':pointer['run_id'],'rq2_run_id':rq2_run_id,
                                     'protocol':config,'normalization':asdict(normalizer),'normalizer_sha256':norm_hash,
                                     'plan_sha256':plan_hash,'model_run_id':model_run_id or pointer['run_id'],
                                     'model_sha256':{m:info['sha256'] for m,info in baseline['models'].items()},
                                     'test_metrics':summary,'sigma_zero_max_absolute_difference':zero_difference,
                                     'sigma_zero_absolute_tolerance':1e-12,
                                     'palm_max_absolute_difference':0.0,'face_model_refitted':False},required)
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description='Prepare a validation-only blur plan, record review, then run frozen RQ3.')
    sub=parser.add_subparsers(dest='command',required=True)
    prep=sub.add_parser('prepare')
    prep.add_argument('--output',required=True)
    prep.add_argument('--sigmas',nargs='+',type=float,default=DEFAULT_SIGMAS)
    review=sub.add_parser('review')
    review.add_argument('--plan',required=True)
    review.add_argument('--note',required=True,help='Your observations after viewing the validation preview.')
    execute=sub.add_parser('run')
    execute.add_argument('--rq2-run',required=True)
    execute.add_argument('--plan',required=True)
    execute.add_argument('--run-id')
    execute.add_argument('--model-run-id')
    args=parser.parse_args()
    try:
        if args.command=='prepare':
            print(prepare_plan(ROOT,args.output,args.sigmas))
        elif args.command=='review':
            plan=load_plan(args.plan,ROOT,reviewed=False)
            if plan['reviewed'] or not args.note.strip():
                raise ValueError('Plan already reviewed or note empty; create a new plan to revise it')
            plan.update(reviewed=True,review_note=args.note)
            write_json(args.plan,plan)
            print('Review recorded; use this frozen plan for the held-out sweep.')
        else:
            result=run(args.rq2_run,args.plan,args.run_id,model_run_id=args.model_run_id)
            print('Completed',result['run_id'])
    except (ValueError,FileNotFoundError) as error:
        parser.exit(2,f'Error: {error}\n')
