from pathlib import Path
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from src.blur import prepare_plan, load_plan
from src.files import write_json


class BlurPlanTest(unittest.TestCase):  # group the regression checks and shared test fixtures for this component
    def test_only_validation_is_used_and_review_and_hashes_are_required(self):  # verify that only validation is used and review and hashes are required
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'src').mkdir()
            (root/'src/blur.py').write_text('synthetic test implementation')
            (root/'data/raw/face').mkdir(parents=True)
            (root/'data/raw/face/olivetti.npz').write_bytes(b'fixture')
            pointer={'run_id':'fixture','manifest_sha256':{'fixture':'hash'}}
            accepted=(pointer,{}, {},[{'modality':'face'}],{}, {})
            images={'face_000':np.eye(8,dtype=float)*.5}
            with patch('src.blur.accepted_scores',return_value=accepted), \
                 patch('src.blur.dataset_images',return_value={'face':images}) as load:
                path=prepare_plan(root,root/'plan',[0,1])
                self.assertEqual(load.call_args.args[1],'validation')
                with self.assertRaisesRegex(ValueError,'review'):
                    load_plan(path,root)
                plan=load_plan(path,root,reviewed=False)
                plan.update(reviewed=True,review_note='Synthetic test review only')
                write_json(path,plan)
                self.assertTrue(load_plan(path,root)['reviewed'])
                (path.parent/'validation_blur_preview.png').write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError,'changed'):
                    load_plan(path,root)


if __name__=='__main__':
    unittest.main()
