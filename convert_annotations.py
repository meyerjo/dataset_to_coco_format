import errno
import json
import re
import os
import shutil
from datetime import datetime

from PIL import Image

from utils.boxes import Boxes


def get_files_in_path(path, m_regex=None):
    if m_regex is not None:
        if m_regex is str:
            m_regex = re.compile(m_regex)
    files = os.listdir(path)
    if m_regex:
        files = [f for f in files if m_regex.search(f) is not None]
    files = [os.path.join(path, f) for f in files]
    return files

DEEPDRIVE_FOLDS = ['train', 'val', 'test']
DEEPDRIVE_VERSIONS = ['100k', '10k']
DEEPDRIVE_LABELS = ['bus', 'traffic light', 'traffic sign', 'person', 'bike', 'truck', 'motor', 'car', 'train', 'rider']

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

if __name__ == '__main__':
    dataset_path = os.path.expanduser(os.path.join('~', '.deepdrive', ))
    required_paths = ['images', 'labels']

    # validate that he paths are available
    for p in required_paths:
        assert(os.path.exists(os.path.join(dataset_path, p)))

    image_path = os.path.join(dataset_path, 'images', 'bdd100k/images/100k/')
    label_path = os.path.join(dataset_path, 'labels', 'bdd100k/labels/100k/')

    # get files in path
    folds = ['train', 'val']
    year = 2017
    overall_annotation_id = 0
    for fold in folds:
        images = get_files_in_path(os.path.join(image_path, fold))
        labels = get_files_in_path(os.path.join(label_path, fold))

        # sort the elements
        images, labels = sorted(images), sorted(labels)

        # number_files = 2048
        #
        # images = images[:number_files]

        if not os.path.exists(os.path.join('.', 'deepdrive', '{}{}'.format(fold, year))):
            mkdir_p(os.path.join('.', 'deepdrive', '{}{}'.format(fold, year)))

        if not os.path.exists(os.path.join('.', 'deepdrive', 'annotations')):
            mkdir_p(os.path.join('.', 'deepdrive', 'annotations'))

        if not os.path.exists(os.path.join('.', 'deepdrive_yolo',)):
            mkdir_p(os.path.join('.', 'deepdrive_yolo'))


        label_object = {
            'info': {
                'description': '',
                'url': 'deepdrive.org',
                'version': 'v1.0',
                'year': 2018,
                'contributor': 'Berkeley',
                'date_created': '2019-01-01 09:00:00.00000'
            },
            'licenses': [
                {
                    'url': '',
                    'id': 1,
                    'name': 'COCO'
                }
            ],
            'images': [],
            'type': 'instances',
            'annotations': []
        }

        label_object['categories'] = []
        for i, c in enumerate(DEEPDRIVE_LABELS):
            label_object['categories'] += [{
                'id': i + 1,
                'name': c
            }]

        for i, im in enumerate(images):
            head_im, tail_im = os.path.split(im)
            head_lb, tail_lb = os.path.split(labels[i])

            if re.match('^(.*)\.[a-z]+$', tail_im).groups()[0] != \
                    re.match('^(.*)\.[a-z]+$', tail_lb).groups()[0]:
                print('Tail differs')
                continue

            shutil.copy(im, os.path.join(
                '.', 'deepdrive', '{}{}'.format(fold, year), tail_im
            ))

            pil_im = Image.open(im)

            rgb_im = pil_im.convert('RGB')
            rgb_im.save(os.path.join(
                '.', 'deepdrive', '{}{}'.format(fold, year), '{}{}'.format(tail_im[:-4], '.jpg')
            ))

            obj_im = {
                'license': 1,
                'url': '',
                # 'file_name': tail_im,
                'file_name': '{}{}'.format(tail_im[:-4], '.jpg'),
                'height': pil_im.height,
                'width': pil_im.width,
                'date_captured': datetime.now().strftime('%Y-%m-%d %H:%M:00'),
                'id': i
                # 'id': tail_im[:-4]
            }


            with open(labels[i], 'r') as f:
                obj = json.loads(f.read())

            annotations = []
            for tmp in obj['frames'][0]['objects']:
                if 'box2d' in tmp:
                    box = Boxes(
                        xmin=tmp['box2d']['x1'], xmax=tmp['box2d']['x2'],
                        ymin=tmp['box2d']['y1'], ymax=tmp['box2d']['y2'],
                        label=DEEPDRIVE_LABELS.index(tmp['category']) + 1
                    )

                    label_object['annotations'] += [
                        {
                            'segmentation': [],
                            'iscrowd': 0,
                            'image_id': i,
                            'id': overall_annotation_id,
                            'area': box.size,
                            'category_id': box.label,
                            'bbox': box.to_xywh()
                        }
                    ]
                    overall_annotation_id += 1

            label_object['images'] += [obj_im]

        output_file = os.path.join(
            './deepdrive',
            'annotations/instances_{}{}.json'.format(fold, year))
        with open(output_file, 'w') as f:
            json.dump(label_object, f)