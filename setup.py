import codecs
import setuptools

RFOX_VERSION = open('VERSION').read().strip()


def readme():
    with codecs.open('README.md', encoding='utf-8') as f:
        return f.read()


requirements = open('requirements.txt').read().splitlines()

setuptools.setup(
    name                          = 'rfox',
    version                       = RFOX_VERSION,
    description                   = 'Unified rfcat helper for sub-GHz RF work',
    long_description              = readme(),
    long_description_content_type = 'text/markdown',
    author                        = 'qu-crypt',
    author_email                  = 'qucrypt@0x3f.dev',
    url                           = 'https://github.com/qu-crypt/rfox',
    keywords                      = ['radio', 'subghz', 'rfcat', 'sdr', 'hacking', 'reverse engineering'],
    packages                      = ['rflib.rfox', 'rflib.rfox.commands'],
    package_dir                   = {
        'rflib.rfox':          'rflib/rfox',
        'rflib.rfox.commands': 'rflib/rfox/commands',
    },
    scripts                       = ['rfox'],
    install_requires              = requirements,
    classifiers                   = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Information Technology',
        'Topic :: Communications',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    python_requires               = '>=3.8',
)
