import errno
import json
import re
import os
import shutil
from datetime import datetime

import yaml
from PIL import Image

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

if __name__ == '__main__':
    dataset_path = os.path.expanduser(os.path.join('~', 'dataset', 'inoutdoorpeoplergbd' ))
    required_paths = ['Annotations', 'ImageSets', 'ImagesQhd', 'DepthJetQhd']
    modality = 'depth'

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

    with open(os.path.join(data_folder, 'inoutdoor.data'), 'w') as f:
        f.write('classes={}\n'.format(len(INOUTDOOR_LABELS)))

        for key in folds.keys():
            f.write('{}={}\n'.format(
                'valid' if key == 'test' else key,
                os.path.abspath(
                    os.path.join(data_folder, 'inoutdoor_{}{}.txt'.format(
                        key, year
                    ))
                )
            ))
        f.write('names=data/{}/inoutdoor.names\n'.format(modality))
        f.write('backup=backup/\n')
        f.write('eval=inoutdoor\n')

    for fold in folds.keys():
        print('Writing {}'.format(fold))
        from utils.read import get_files_in_set
        files_in_sets = get_files_in_set(imageset_path, folds[fold])

        images = [os.path.join(image_path, f + '.png') for f in files_in_sets]
        labels = [os.path.join(label_path, f + '.yml') for f in files_in_sets]

        # sort the elements
        images, labels = sorted(images), sorted(labels)

        images_folder = os.path.join('.', 'inoutdoor_yolo', modality, 'images', '{}{}'.format(
            fold, year
        ))
        labels_folder = os.path.join('.', 'inoutdoor_yolo', modality, 'labels', '{}{}'.format(
            fold, year
        ))


        if not os.path.exists(images_folder):
            mkdir_p(images_folder)
        if not os.path.exists(labels_folder):
            mkdir_p(labels_folder)

        with open(os.path.join(data_folder, 'inoutdoor.names'), 'w') as f:
            for label in INOUTDOOR_LABELS:
                f.write('{}\n'.format(label))

        fold_files = open(os.path.join(data_folder, 'inoutdoor_{}{}.txt'.format(
            fold, year
        )), 'w')

        for i, im in enumerate(images):
            if i % 100 == 0:
                print('\tWriting file: {}/{}'.format(i, len(images)))
            head_im, tail_im = os.path.split(im)
            head_lb, tail_lb = os.path.split(labels[i])

            if re.match('^(.*)\.[a-z]+$', tail_im).groups()[0] != \
                    re.match('^(.*)\.[a-z]+$', tail_lb).groups()[0]:
                print('Tail differs')
                continue

            if not os.path.exists(im):
                print('File missing: {}'.format(im))
                continue

            # TODO: o[ppen the original and rescale...
            shutil.copy(
                im,
                os.path.join(
                    images_folder, 'inoutdoor_{}{}_{}'.format(
                        fold, year, tail_im)
                )
            )

            # read the data
            with open(labels[i], 'r') as f:
                obj = yaml.load(f)
            if 'object' not in obj['annotation']:
                continue

            fold_files.write('{}\n'.format(os.path.abspath(
                os.path.join(images_folder, 'inoutdoor_{}{}_{}'.format(
                    fold, year, tail_im)
                             ))))

            label_file = open(os.path.join(labels_folder, 'inoutdoor_{}{}_{}{}'.format(
                fold, year, tail_im[:-4], '.txt')), 'w')
            annotations = []

            height, width = obj['annotation']['size']['height'], \
                obj['annotation']['size']['width']

            for tmp in obj['annotation']['object']:
                if 'bndbox' in tmp:
                    label_id = INOUTDOOR_LABELS.index(tmp['name'])
                    box2d = tmp['bndbox']
                    box2d = {key: int(value) for key, value in box2d.items()}

                    box_width = (box2d['xmax'] - box2d['xmin']) / float(width)
                    box_height = (box2d['ymax'] - box2d['ymin']) / float(height)

                    cx = (box2d['xmin'] / float(width) + box_width / 2)
                    cy = (box2d['ymin'] / float(height) + box_height / 2)

                    label_file.write(
                        '{} {} {} {} {}\n'.format(
                            label_id,
                            cx, cy,
                            box_width, box_height
                        )
                    )
