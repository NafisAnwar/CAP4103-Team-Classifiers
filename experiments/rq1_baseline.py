from pathlib import Path
import argparse
import json
import sys
import joblib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.datasets import dataset_images
from src.experiment_support import RunArtifacts, enroll, score_and_evaluate
from src.face_authentication import FaceAuthenticator
from src.files import ROOT, sha256, write_csv
from src.matching import combine_raw_scores
from src.palmprint_authentication import PalmAuthenticator
from src.trial_protocol import load_protocol


def run(run_id=None, root=ROOT):
    root = Path(root)
    with RunArtifacts(root, run_id) as artifacts:
        config, partitions, trials = load_protocol(root) #verify frozen bytes before reading any images
        enrollment = dataset_images(partitions, 'enrollment', root)
        validation = dataset_images(partitions, 'validation', root)
        choices = {'face': [16, 32, 64], 'palm': ['hog', 'lbp']}
        selection, chosen, validation_scores = [], {}, {}
        for modality in ['face', 'palm']:
            best = None
            for setting in choices[modality]:
                model = FaceAuthenticator(setting, config['seed']) if modality == 'face' else PalmAuthenticator(setting)
                enroll(model, enrollment, partitions, modality) #only enrollment controls learned features and templates
                rows, evaluator = score_and_evaluate(model, validation, trials['validation'], modality)
                metrics = evaluator.metrics()
                selection.append({'modality': modality, 'setting': str(setting), 'validation_eer': metrics['eer'],
                                  'validation_auc': metrics['auc'], 'score_direction_check': metrics['score_direction_check']})
                if metrics['score_direction_check'] == 'passed' and (best is None or metrics['eer'] < best):
                    best, chosen[modality], validation_scores[modality] = metrics['eer'], model, rows
            if modality not in chosen:
                raise ValueError(f'No {modality} validation candidate has the expected score direction')
        write_csv(artifacts.metrics_dir / 'validation_model_selection.csv', selection)
        write_csv(artifacts.metrics_dir / 'validation_scores.csv', combine_raw_scores(validation_scores['face'], validation_scores['palm']))
        test = dataset_images(partitions, 'test', root) #test stays unloaded until both choices are frozen
        results, test_scores = [], {}
        for modality in ['face', 'palm']:
            rows, evaluator = score_and_evaluate(chosen[modality], test, trials['test'], modality)
            test_scores[modality] = rows
            metrics = evaluator.export(artifacts.metrics_dir, artifacts.figures_dir, f'rq1_{modality}')
            results.append(dict(metrics, modality=modality, subjects=config['subjects'], seed=config['seed']))
            joblib.dump(chosen[modality], artifacts.model_dir / f'{modality}.joblib')
        write_csv(artifacts.metrics_dir / 'rq1_baseline_scores.csv', combine_raw_scores(test_scores['face'], test_scores['palm']))
        write_csv(artifacts.metrics_dir / 'rq1_summary.csv', results)
        metadata = {'protocol': config,
                    'models': {modality: {'path': (artifacts.model_dir / f'{modality}.joblib').relative_to(root).as_posix(),
                                          'sha256': sha256(artifacts.model_dir / f'{modality}.joblib'),
                                          'fit_sample_ids': chosen[modality].fit_sample_ids_} for modality in chosen},
                    'chosen_models': {'face_pca_components': chosen['face'].n_components, 'palm_feature': chosen['palm'].feature,
                                      'template_rule': 'mean unit enrollment vectors, normalized; cosine similarity'},
                    'test_metrics': results,
                    'limitations': ['Artificial identities link different real people.', 'No demographic fairness inference.',
                                    'BMPD license metadata is Unknown; raw images remain local.',
                                    'Heuristic palm ROI has no anatomical landmark or rotation alignment.',
                                    'EER is descriptive on this held-out set, not a deployment threshold.']}
        required = [artifacts.metrics_dir / name for name in ['validation_model_selection.csv', 'validation_scores.csv',
                                                            'rq1_baseline_scores.csv', 'rq1_summary.csv']]
        for modality in ['face', 'palm']:
            required += [artifacts.model_dir / f'{modality}.joblib', artifacts.metrics_dir / f'rq1_{modality}_metrics.json',
                         artifacts.metrics_dir / f'rq1_{modality}_rates.csv']
            required += [artifacts.figures_dir / f'rq1_{modality}_{plot}.png' for plot in ['roc', 'far_frr', 'scores']]
        metadata = artifacts.complete(metadata, required) #incomplete runs never replace the latest pointer
    print(json.dumps({'run_id': metadata['run_id'], 'chosen_models': metadata['chosen_models'], 'test_metrics': results}, indent=2))
    return metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id')
    run(parser.parse_args().run_id)
