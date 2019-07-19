import errno
import json
import re
import os
import shutil
from datetime import datetime

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

    data_folder = os.path.join('.', 'deepdrive_yolo', 'data')
    if not os.path.exists(data_folder):
        mkdir_p(data_folder)

    with open(os.path.join(data_folder, 'deepdrive.data'), 'w') as f:
        f.write('classes={}\n'.format(len(DEEPDRIVE_LABELS)))

        for key, item in zip(['train', 'valid'], folds):
            f.write('{}={}\n'.format(
                key,
                os.path.abspath(
                    os.path.join(data_folder, 'deepdrive_{}{}.txt'.format(
                        item, year
                    ))
                )
            ))
        f.write('names=data/deepdrive.names\n')
        f.write('backup=backup/\n')
        f.write('eval=deepdrive\n')

    for fold in folds:
        print('Writing {}'.format(fold))
        images = get_files_in_path(os.path.join(image_path, fold))
        labels = get_files_in_path(os.path.join(label_path, fold))

        # sort the elements
        images, labels = sorted(images), sorted(labels)

        # number_files = 16
        # images = images[:number_files]

        images_folder = os.path.join('.', 'deepdrive_yolo', 'images', '{}{}'.format(
            fold, year
        ))
        labels_folder = os.path.join('.', 'deepdrive_yolo', 'labels', '{}{}'.format(
            fold, year
        ))


        if not os.path.exists(images_folder):
            mkdir_p(images_folder)
        if not os.path.exists(labels_folder):
            mkdir_p(labels_folder)

        with open(os.path.join(data_folder, 'deepdrive.names'), 'w') as f:
            for label in DEEPDRIVE_LABELS:
                f.write('{}\n'.format(label))

        fold_files = open(os.path.join(data_folder, 'deepdrive_{}{}.txt'.format(
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

            pil_im = Image.open(im)
            rgb_im = pil_im.convert('RGB')
            rgb_im.save(os.path.join(
                images_folder, 'deepdrive_{}{}_{}{}'.format(
                    fold, year, tail_im[:-4], '.jpg')
            ))

            # read the data
            with open(labels[i], 'r') as f:
                obj = json.loads(f.read())

            fold_files.write('{}\n'.format(os.path.abspath(
                os.path.join(images_folder, 'deepdrive_{}{}_{}{}'.format(
                    fold, year, tail_im[:-4], '.jpg')
                             ))))

            label_file = open(os.path.join(labels_folder, 'deepdrive_{}{}_{}{}'.format(
                fold, year, tail_im[:-4], '.txt')), 'w')
            annotations = []
            for tmp in obj['frames'][0]['objects']:
                if 'box2d' in tmp:
                    label_id = DEEPDRIVE_LABELS.index(tmp['category']) + 1
                    box2d = tmp['box2d']

                    box_size = (box2d['y2'] - box2d['y1']) * (box2d['x2'] - box2d['x1'])
                    box_width = (box2d['x2'] - box2d['x1']) / pil_im.width
                    box_height = (box2d['y2'] - box2d['y1']) / pil_im.height

                    cx = (box2d['x1'] / pil_im.width + box_width / 2)
                    cy = (box2d['y1'] / pil_im.height + box_height / 2)

                    label_file.write(
                        '{} {} {} {} {}\n'.format(
                            label_id - 1,
                            cx, cy,
                            box_width, box_height
                        )
                    )
