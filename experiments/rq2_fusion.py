from pathlib import Path
import argparse
import sys
import uuid
from dataclasses import asdict
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.files import ROOT, write_csv, read_csv, text_sha256
from src.experiment_support import RunArtifacts
from src.fusion import accepted_scores, Normalizer, fuse_scores, RQ2_FIELDS
from src.fusion_reporting import evaluate_conditions, verify_metrics, rq2_comparison


def run(run_id=None, root=ROOT):  # fit normalization using accepted validation scores and evaluate equal-weight fusion on test claims
    root = Path(root)
    pointer, baseline, config, partitions, trials, tables = accepted_scores(root)  # recover the accepted baseline and its exact validation and test claims
    validation_hash = pointer['score_sha256']['validation_scores.csv']
    normalizer = Normalizer.fit(tables['validation'], trials['validation'], split='validation',  # learn normalization exclusively from validated rq1 development scores
                                validation_sha256=validation_hash, baseline_id=pointer['run_id'])
    with RunArtifacts(root, run_id or 'rq2_' + uuid.uuid4().hex[:12], latest_name='rq2_latest.json') as artifacts:
        normalizer_path = artifacts.metrics_dir / 'normalizer.json'
        normalizer.save(normalizer_path, dict(artifacts.provenance, baseline_id=pointer['run_id'],
                                            input_score_sha256=pointer['score_sha256']))
        normalizer = Normalizer.load(normalizer_path)
        rows = fuse_scores(tables['test'], tables['test'], normalizer, trials['test'])  # combine held-out face and palm scores with the frozen equal-weight rule
        scores_path = artifacts.metrics_dir / 'rq2_fusion_scores.csv'
        write_csv(scores_path, rows, RQ2_FIELDS)
        rows = read_csv(scores_path)
        summary = evaluate_conditions(rows, artifacts, 'rq2_clear', 0.0)
        verify_metrics(rows, summary)  # check the exported metrics against the stored trial scores
        for saved in baseline['test_metrics']:
            calculated = next(r for r in summary if r['modality'] == saved['modality'])
            for field in ['eer', 'auc', 'd_prime']:
                if abs(calculated[field] - saved[field]) > 1e-12:
                    raise ValueError('Recomputed RQ1 metrics differ from accepted values')
        write_csv(artifacts.metrics_dir / 'master_metrics.csv', summary)
        rq2_comparison(summary, artifacts.figures_dir / 'rq2_comparison.png')
        current = accepted_scores(root)[0]  # ensure the baseline pointer was not replaced while fusion executed
        if current != pointer:
            raise ValueError('Baseline reference changed during run')
        required = sorted(artifacts.metrics_dir.glob('*.csv')) + [normalizer_path]
        required += sorted(artifacts.metrics_dir.glob('*_metrics.json')) + sorted(artifacts.figures_dir.glob('*.png'))
        metadata = artifacts.complete({'experiment': 'rq2', 'baseline_id': pointer['run_id'],
                                       'protocol': config, 'normalization': asdict(normalizer),
                                       'normalizer_sha256': text_sha256(normalizer_path),
                                       'input_score_sha256': pointer['score_sha256'], 'test_metrics': summary,
                                       'evidence_scope': 'recomputed from hash-verified accepted score CSVs; '
                                                         'raw-image/model reproduction is a separate gate'}, required)
    return metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='RQ2 from verified accepted scores; does not refit either model.')
    parser.add_argument('--run-id')
    args = parser.parse_args()
    result = run(args.run_id)
    print('Completed', result['run_id'])
    for row in result['test_metrics']:
        print(row['modality'], 'EER', row['eer'], 'AUC', row['auc'], 'd-prime', row['d_prime'])
