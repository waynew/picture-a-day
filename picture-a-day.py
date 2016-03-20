#!/usr/bin/env python
from __future__ import print_function, unicode_literals

import glob
import os
import shutil
import subprocess
import sys

try:
    import configparser
except ImportError:
    # I hope we're on Python2. Otherwise this will fail too, sorry
    import ConfigParser as configparser

forcing = False
config = configparser.ConfigParser()
dirname = os.path.dirname(os.path.abspath(__file__))
config.read(os.path.join(dirname, 'picture_a_day.conf'))
config.read(os.path.expanduser('~/.picture_a_day.conf'))

if not config['pad']['theme_dir']:
    config['pad']['theme_dir'] = os.path.join(dirname, 'theme')

if not config['pad']['images_dir']:
    config['pad']['images_dir'] = os.path.join(dirname, 'images')

if not os.path.exists(config['pad']['images_dir']):
    sys.exit('ERROR: Image directory {!r} does not exist.'
             .format(config['pad']['images_dir']))
elif not os.path.isdir(config['pad']['images_dir']):
    sys.exit('ERROR: Image directory {!r} is not a directory.'
             .format(config['pad']['images_dir']))

if not config['pad']['output_dir']:
    config['pad']['output_dir'] = os.path.abspath(os.path.join(os.curdir,
                                                               'output'))
img_dir = os.path.join(config['pad']['output_dir'], 'img')
thumbs_dir = os.path.join(img_dir, 'thumb')
# TODO: Python2 needs a fallback - exist_ok is new in 3 -W. Werner, 2016-03-20
os.makedirs(thumbs_dir, exist_ok=True)

existing_thumbs = [
    _.replace('_thumb.jpg', '.jpg') 
    for _ in os.listdir(thumbs_dir)
]
pattern = os.path.join(config['pad']['images_dir'], config['pad']['file_glob'])
all_images = glob.glob(pattern) 
images = [
    img for img in all_images
    if os.path.basename(img) not in existing_thumbs
]

def run():
    if not images:
        if forcing:
            sys.exit(0)
        else:
            sys.exit('Nothing to do. Did you add any new images?')

    command = ['convert'] + images + [
        '-auto-orient',
        '-resize',
        'x175',
        '-quality',
        config['pad']['thumb_quality'],
        '-set',
        'filename:f',
        '%t',
        os.path.join(thumbs_dir,'%[filename:f]_thumb.jpg'),
    ]
    subprocess.check_call(command)

    if config['pad'].getboolean('copy_images'):
        for image in images:
            shutil.copy(image, img_dir)

    generate_html()

def generate_html():
    template_filename = os.path.join(config['pad']['theme_dir'], 'index.html')
    output_filename = os.path.join(config['pad']['output_dir'], 'index.html')
    with open(template_filename) as template,\
            open(output_filename, 'w') as f:
        fmt = (
            '<a href="{base_url}/img/{filename}">'
            '<img src="{base_url}/img/thumb/{img_name}_thumb.jpg">'
            '</a>'
        )

        f.write(template.read().replace(
            '{{ content }}',
            '\n'.join(
                fmt.format(
                    base_url=config['pad']['base_url'],
                    filename=os.path.basename(image),
                    img_name=os.path.splitext(os.path.basename(image))[0],
                )
                for image in all_images
            )
        ))

if __name__ == '__main__':
    if '--force-html' in sys.argv:
        forcing = True
        generate_html()
    if '--regen-thumbs' in sys.argv:
        images = all_images
    run()
