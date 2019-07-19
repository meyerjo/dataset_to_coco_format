import errno
import json
import re
import os
import shutil
from datetime import datetime

import yaml
from PIL import Image
from typing import List

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

INOUTDOOR_LABELS = ['person']

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def write_labels(label_object: dict, labels: List[str] ) :
    label_object['categories'] = []
    for i, c in enumerate(labels):
        label_object['categories'] += [{
            'id': i + 1,
            'name': c
        }]
    return


if __name__ == '__main__':
    dataset_path = os.path.expanduser(os.path.join('~', 'dataset', 'inoutdoorpeoplergbd' ))
    required_paths = ['Annotations', 'ImageSets', 'ImagesQhd', 'DepthJetQhd']
    modality = 'rgb'

    # validate that he paths are available
    for p in required_paths:
        assert(os.path.exists(os.path.join(dataset_path, p)))

    if modality == 'rgb':
        image_path = os.path.join(dataset_path, 'ImagesQhd')
    else:
        image_path = os.path.join(dataset_path, 'DepthJetQhd')
    label_path = os.path.join(dataset_path, 'Annotations')
    imageset_path = os.path.join(dataset_path, 'ImageSets')

    # get files in path
    folds = {
        'train': ['seq0.txt', 'seq1.txt', 'seq2.txt'],
        'test': ['seq3.txt']
    }
    year = 2015
    overall_annotation_id = 0

    data_folder = os.path.join('.', 'inoutdoor_yolo', 'data', modality)
    if not os.path.exists(data_folder):
        mkdir_p(data_folder)

    overall_annotation_id = 0
    for fold in folds.keys():
        print('Writing {}'.format(fold))
        from utils.read import get_files_in_set
        files_in_sets = get_files_in_set(imageset_path, folds[fold])

        # convert to true names
        images = [os.path.join(image_path, f + '.png') for f in files_in_sets]
        labels = [os.path.join(label_path, f + '.yml') for f in files_in_sets]

        # sort the elements
        images, labels = sorted(images), sorted(labels)

        # number_files = 2048
        #
        # images = images[:number_files]

        if not os.path.exists(os.path.join('.', 'inoutdoor', modality, '{}{}'.format(fold, year))):
            mkdir_p(os.path.join('.', 'inoutdoor', modality, '{}{}'.format(fold, year)))

        if not os.path.exists(os.path.join('.', 'inoutdoor', modality, 'annotations')):
            mkdir_p(os.path.join('.', 'inoutdoor', modality, 'annotations'))

        label_object = {
            'info': {
                'description': '',
                'url': 'ais.informatik.uni-freiburg.derg',
                'version': 'v1.0',
                'year': 2015,
                'contributor': 'University of Freiburg',
                'date_created': '2019-01-01 09:00:00.00000'
            },
            'licenses': [
                {
                    'url': '',
                    'id': 1,
                    'name': 'CC'
                }
            ],
            'images': [],
            'type': 'instances',
            'annotations': []
        }

        write_labels(label_object, INOUTDOOR_LABELS)

        for i, im in enumerate(images):
            head_im, tail_im = os.path.split(im)
            head_lb, tail_lb = os.path.split(labels[i])

            if re.match('^(.*)\.[a-z]+$', tail_im).groups()[0] != \
                    re.match('^(.*)\.[a-z]+$', tail_lb).groups()[0]:
                print('Tail differs')
                continue

            if not os.path.exists(im):
                continue

            shutil.copy(im, os.path.join(
                '.', 'inoutdoor', modality, '{}{}'.format(fold, year), tail_im
            ))

            # read the data
            with open(labels[i], 'r') as f:
                obj = yaml.load(f)

            height, width = obj['annotation']['size']['height'], \
                obj['annotation']['size']['width']

            pil_im = Image.open(im)

            obj_im = {
                'license': 1,
                'url': '',
                'file_name': tail_im,
                'height': height,
                'width': width,
                'date_captured': datetime.now().strftime('%Y-%m-%d %H:%M:00'),
                'id': i
                # 'id': tail_im[:-4]
            }

            annotations = []

            for tmp in obj['annotation'].get('object', []):
                if 'bndbox' in tmp:
                    label_id = INOUTDOOR_LABELS.index(tmp['name']) + 1
                    box2d = tmp['bndbox']
                    box2d = {key: int(value) for key, value in box2d.items()}
                    box = Boxes(box2d['xmin'], box2d['xmax'], box2d['ymin'], box2d['ymax'], tmp['name'])

                    box_xywh = box.to_xywh(normalization=[width, height])
                    box_yhwh = [box_
                    label_object['annotations'] += [
                        {
                            'segmentation': [],
                            'area': box.dimension,
                            'iscrowd': 0,
                            'image_id': i,
                            'id': overall_annotation_id,
                            'category_id': label_id,
                            'bbox': box.to_xywh()
                        }
                    ]
                    overall_annotation_id += 1

            if len(label_object['annotations']) != 0:
                label_object['images'] += [obj_im]

            # label_object['annotations'] += [annotations]

        with open(os.path.join(
                './inoutdoor/', modality,
                'annotations', 'instances_{}{}.json'.format(fold, year))
                , 'w') as f:
            json.dump(label_object, f)