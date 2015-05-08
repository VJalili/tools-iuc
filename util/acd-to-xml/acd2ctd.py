#!/usr/bin/env python
from lxml import etree as ET
import sys
from CTDopts.CTDopts import CTDModel

ACD_INPUTS = ('additional', 'advanced', 'input', 'required')
ACD_OUTPUTS = ('output', )

INPUT_TYPE_MAPPING = {
    'assembly': {},
    'codon': {},
    'cpdb': {},
    'datafile': {'file_formats': ['data']},
    'directory': {},
    'dirlist': {},
    'features': {},
    'filelist': {},
    'infile': {'file_formats': ['data']},
    'matrix': {},
    'matrixf': {},
    'obo': {'file_formats': ['obo']},
    'pattern': {},
    'refseq': {},
    'regexp': {},
    'resource': {'file_formats': ['data']},
    'scop': {},
    'sequence': {'file_formats': ['fasta']},
    'seqall': {'file_formats': ['fasta']},
    'seqset': {'file_formats': ['fasta']},
    'seqsetall': {'file_formats': ['fasta']},
    'url': {'type': str},
    'variation': {'file_formats': ['vcf']},
    'xml': {'file_formats': ['xml']},
    'taxon': {'type': str},
    'text': {'type': str},
}


tree = ET.parse(sys.argv[1])
root = tree.getroot()

tool = CTDModel(
    name=root.attrib['id'],
    version='6.6.0',
    description=root.find('metadata').find('documentation').text
)

def handle_parameter(child):
    kwargs = {
        'type': child.attrib['type']
    }
    if child.attrib['type'] in INPUT_TYPE_MAPPING.keys():
        kwargs['type'] = 'input-file'
        if child.find('knowntype') is not None:
            kwargs['file_formats'] = [child.find('knowntype').text]

        kwargs.update(INPUT_TYPE_MAPPING[child.attrib['type']])
    elif child.attrib['type'] in ('integer', 'float'):
        num_min = None
        num_max = None
        if child.find('minimum') is not None:
            try:
                num_min = float(child.find('minimum').text)
            except Exception:
                pass
        if child.find('maximum') is not None:
            try:
                num_max = float(child.find('maximum').text)
            except Exception:
                pass

        try:
            num_default = float(child.find('default').text)
        except Exception:
            num_default = 0

        if child.attrib['type'] == 'integer':
            if num_min is not None:
                num_min = int(num_min)
            if num_max is not None:
                num_max = int(num_max)
            num_default = int(num_default)

        kwargs['num_range'] = (num_min, num_max)
        kwargs['default'] = num_default
        kwargs['type'] = int if child.attrib['type'] == 'integer' else float
    elif child.attrib['type'] in ('boolean', 'toggle'):
        kwargs['type'] = str
        kwargs['choices'] = ['true', 'false']
    elif child.attrib['type'] == 'list':
        if child.find('delimiter') is not None:
            delimiter = child.find('delimiter').text
        else:
            delimiter = ';'

        if child.find('codedelimiter') is not None:
            codedelimiter = child.find('codedelimiter').text
        else:
            codedelimiter = ':'

        kv = {}
        for x in child.find('values').text.split(delimiter):
            if len(x.strip()) > 0:
                try:
                    key, value = x.split(codedelimiter)
                except:
                    tmp = x.split()
                    key = tmp[0]
                    value = ' '.join(tmp[1:])

                kv[key.strip()] = value.strip()

        kwargs['type'] = str
        kwargs['choices'] = [kv[k] for k in kv.keys()]
    elif child.attrib['type'] == 'selection':
        if child.find('delimiter') is not None:
            delimiter = child.find('delimiter').text
        else:
            delimiter = ';'

        kv = {}
        for i, x in enumerate(child.find('values').text.split(delimiter)):
            if len(x.strip()) > 0:
                kv[str(i)] = x.strip()

        kwargs['type'] = str
        kwargs['choices'] = [kv[k] for k in kv.keys()]
    elif child.attrib['type'] == 'range':
        # TODO
        kwargs['type'] = 'string'
    elif child.attrib['type'] == 'array':
        # TODO
        kwargs['type'] = 'string'

    if child.find('information') is not None:
        kwargs['description'] = child.find('information').text

    kwargs['required'] = required

    print kwargs
    return kwargs


def handle_section(section, subparams, required=False):
    for child in section.getchildren():
        if child.tag == 'parameter':
            kwargs = handle_parameter(child)
            subparams.add(
                child.attrib['name'],
                **kwargs
            )
        elif child.tag == 'section':
            subsubparams = subparams.add_group(
                section.attrib['id'],
                section.find('metadata').find('information').text)
            handle_section(child, subsubparams, required=required)
        else:
            print child.tag


output_section = None
for section in root.findall('section'):
    print section.attrib
    if section.attrib['id'] in ACD_INPUTS:
        required = section.attrib['id'] in ('required', 'input')
        subparams = tool.add_group(section.attrib['id'],
                                   section.find('metadata').find('information').text)
        handle_section(section, subparams, required=required)
    else:
        if output_section is None:
            output_section = tool.add_group('output', 'Output Options')

        for parameter in section.findall('parameter'):
            if parameter.attrib['type'] in ('toggle', ):
                kwargs = handle_parameter(parameter)
                output_section.add(
                    parameter.attrib['name'],
                    **kwargs
                )
            else:
                print parameter.attrib
                kwargs = {
                    'required': True,
                    'type': 'output-file',
                }
                if parameter.find('extension') is not None:
                    kwargs['file_formats'] = [parameter.find('extension').text]
                if parameter.find('information') is not None:
                    kwargs['description'] = parameter.find('information').text

                tool.add(
                    parameter.attrib['name'],
                    **kwargs
                )

tool.write_ctd(sys.argv[2])
