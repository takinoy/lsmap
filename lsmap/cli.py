#!/usr/bin/python3

import click
import json
import os
import re
import subprocess as sp
from tabulate import tabulate
# importing the required classes from the rich module
# from rich.console import Console
# from rich.table import Table


from lxml import etree


def get_disk_info_lshw(file=None):
    # https://towardsdatascience.com/processing-xml-in-python-elementtree-c8992941efd2
    # https://python.doctor/page-xml-python-xpath

    if file:
        try:
            tree = etree.parse(file)
        except OSError as e:
            file = None
    if not file:
        proc = sp.run(['sudo', 'lshw', '-class', 'disk', '-xml'], stdout=sp.PIPE)
        tree = etree.ElementTree(etree.fromstring(proc.stdout.decode()))

    root = tree.getroot()

    blockdevices = {
        'ata': {},
        'nvme': {},
    }

    for child in root:
        description = model = serial = path = port = ''
        port = None
        for element in child:
            # import ipdb; ipdb.set_trace()
            if element.tag == 'description':
                description = element.text

            if element.tag == 'businfo':
                port = int(
                    re.split(r'@', re.findall(r'\@[0-9]', element.text)[0])[1]
                )
            if element.tag == 'product':
                model = element.text
            if element.tag == 'serial':
                serial = element.text
            if element.tag == 'logicalname':
                path = element.text

        if port is None:
            continue
        if re.findall(r'ATA', description):
            device_type = 'ata'
        elif re.findall(r'NVM', description):
            device_type = 'nvme'
        else:
            continue

        blockdevices[device_type][port] = {
            'model': model,
            'path': path,
            'serial': serial,
            'map-id': (None, None),
            'map-name': None,
            'label': None,
            'disk-id': device_type + '-' + model + '_' + serial,
        }

    return blockdevices


def get_disk_info_lsblk(file=None):
    # load json file
    # https://www.geeksforgeeks.org/read-json-file-using-python/

    if file:
        try:
            file = open(file)
        except FileNotFoundError as e:
            file = None
        else:
            data = json.load(file)

    if not file:
        proc = sp.run(['lsblk', '-o', 'path,name,model,serial,label', '--json'], stdout=sp.PIPE)
        data = json.loads(proc.stdout.decode())

    devices = data['blockdevices']
    blockdevices = {
        'ata': {},
        'nvme': {},
    }

    for device in devices:
        # https://willhaley.com/blog/find-correspond-disk-belongs-which-hard-drive-controller-linux/
        # https://superuser.com/questions/1352337/how-to-tell-which-sata-controller-a-drive-is-using
        proc = sp.run(
            ['udevadm', 'info', '-q', 'path', '-n', device['path']], stdout=sp.PIPE
        )
        stdout = proc.stdout.decode()
        port = None
        if re.findall(r'ata', stdout):
            # Is ata drive
            port = int(
                re.split(r':', re.findall(r'[0-9]:[0-9]:[0-9]:[0-9]', stdout)[0])[0]
            )
            device_type = 'ata'
        elif re.findall(r'nvme', stdout):
            # Is nvme drive
            ids = re.split(r'nvme', re.findall(r'nvme[0-9]', stdout)[0])[1]
            port = int(ids)
            device_type = 'nvme'

        if port is None:
            continue

        device['map-id'] = (None, None)
        device['map-name'] = None
        device['label'] = None
        device['disk-id'] = (
            device_type + '-' + device['model']  + '_' + device['serial']
        )

        blockdevices[device_type][port] = device

    return blockdevices


def get_device_from_attribute(devices, attribute, value):
    for port, device in devices.items():
        if device[attribute] == value:
            return port, device

    # No mapped device found
    return None, None


def get_map_size(devices):
    nb_col, nb_row = 0, 0
    for key, device in devices.items():
        col_id, row_id = device['map-id']
        if col_id and col_id > nb_col:
            nb_col = col_id
        if row_id and row_id > nb_row:
            nb_row = row_id

    return nb_col, nb_row


def get_mapping(devices, attribute=None):
    # Physical mapping of pci drive
    # Get coordinates
    mapping = []

    nb_col, nb_row = get_map_size(devices)

    for y in range(1, nb_row + 1):
        row = []
        for x in range(1, nb_col + 1):
            port, device = get_device_from_attribute(devices, 'map-id', (x, y))

            if port is not None and attribute:
                if attribute == 'port':
                    # populate port state
                    row.append(port)
                else:
                    # populate data layout
                    try:
                        row.append(device[attribute])
                    except KeyError:
                        print(f"Attribute {attribute} doesn't exist")
                        continue
            else:
                # Return empty map
                row.append(None)

        mapping.append(row)

    if mapping:
        return mapping
    else:
        return [[]]


def set_devices_mapping(devices, device_type):
    print("Configure physical device mapping (Column[A-Z]Row[1-100], example B2):")
    print_mapping(devices, 'serial', device_type, True)

    answer = 'n'
    while answer not in ('y', 'Y'):
        for port, device in devices.items():
            map_name = device['map-name']
            if map_name:
                answer = input(
                    f"Device {device_type}-{device['model']}_{device['serial']} (port {port}, mapped to '{map_name}'): "
                )
            else:
                answer = input(
                    f"Device {device_type}-{device['model']}_{device['serial']} (port {port}): "
                )

            if answer:
                col_name = answer[0].upper()
                row_name = answer[1:]

                # converting char into int
                col_id = ord(col_name) - 64
                row_id = int(row_name)

                # Register mapping
                map_id = (col_id, row_id)
                map_name = f'disk {col_name}{row_name}'
            elif map_name:
                map_id = device['map-id']
            else:
                map_id, map_name = (None, None), None

            # Register mapping
            devices[port]['map-id'] = map_id
            devices[port]['map-name'] = map_name

        print_mapping(devices, 'serial', device_type, True)
        answer = input("Correct (Y/y/N/n) ?")
        if not answer:
            answer = 'y'

    return devices


def set_labels(devices, device_type):
    print("Configure disk labels:")
    print_mapping(devices, 'label', device_type, True)

    nb_col, nb_row = get_map_size(devices)

    answer = 'n'
    while answer not in ('y', 'Y'):

        for y in range(1, nb_row + 1):
            for x in range(1, nb_col + 1):
                port, device = get_device_from_attribute(devices, 'map-id', (x, y))
                label = devices[port]['label']

                answer = input(
                    f"""{device['map-name']} ata-{device['model']}_{device['serial']}\
                        (label: '{label}'): """
                )
                if answer:
                    label = answer
                elif label:
                    continue

                devices[port]['label'] = label

                print_mapping(devices, 'label', True)

        answer = input("Correct (Y/y/N/n) ? ")
        if not answer:
            answer = 'y'

    return devices


def load_blockdevice_mapping(blockdevices, blockdevices_config):
    for device_type, devices in blockdevices.items():
        devices_config = blockdevices_config[device_type]
        for port, _ in devices.items():
            if port is None:
                continue

            try:
                label = devices_config[str(port)]['label']
                serial = devices_config[str(port)]['serial']
                map_id = tuple(devices_config[str(port)]['map-id'])
                map_name = devices_config[str(port)]['map-name']
            except KeyError as e:
                print(e)
                return blockdevices, False

            # Map id is loaded relative to the physical device port
            devices[port]['map-id'] = map_id
            devices[port]['map-name'] = map_name

            # Label is loaded relative to the saved serial number of the disk
            port2, _ = get_device_from_attribute(devices, 'serial', serial)
            if port2 is not None:
                devices[port2]['label'] = label
            else:
                devices[port2]['label'] = None


        blockdevices[device_type] = devices

    return blockdevices, True


def layout_size(layout):
    nb_row = len(layout)
    nb_columns = len(layout[0])

    return nb_columns, nb_row


def nb_items(layout):
    items = []
    for y in layout:
        for x in y:
            items.append(x)

    return len(items)


def set_table(mapping, title, headers):
    # creating the table object

    table = Table(title=title)

    # adding the columns
    # for header in headers:
    #     # table.add_column(header, style="cyan", no_wrap=True)
    #     table.add_column("")

    # adding the rows
    for row in mapping:
        table.add_row(*row)

    # creating the console object
    console = Console()

    # displaying the table using the console object
    console.print(table)


def print_mapping(devices, data, device_type, headers=False):
    mapping = get_mapping(devices, data)
    # TODO add headersord(col_name) - 64
    nb_columns = len(mapping[0])

    if nb_columns:
        A = ord("A")
        if headers:
            headers = []
            for char_num in range(A, A + nb_columns):
                headers.append(chr(char_num))
        else:
            headers = []

        title = str(device_type) + " devices:"

        print(title.upper())
        print(tabulate(mapping, headers, tablefmt='fancy_grid', stralign='center'))
        print()


def save_config(config_file, blockdevices):
    with open(os.path.expanduser(config_file), 'w') as outfile:
        json.dump(blockdevices, outfile)


def get_drive_temp(devices):
    # TODO
    # https://www.simplified.guide/linux/disk-temperature-view
    pass


@click.group()
def cli(**kwargs):
    pass


@cli.command('disks')
@click.option(
    '--add-labels', '-l', default=False, is_flag=True, help='Add devices label'
)
@click.option(
    '--ata', '-a', default=False, is_flag=True, help='display ata disks'
)
@click.option(
    '--configure', '-c', default=False, is_flag=True, help='Configure devices maps'
)
@click.option(
    '--nvme', '-n', default=False, is_flag=True, help='display nvme disks'
)
@click.argument('attribute', required=False, nargs=1, type=click.Path())
def _disks(**kwargs):
    """
    Display disks mapping\n
    ATTRIBUTE: disk-id, label, name, map-id, map-name, model, port, path, serial.
    """
    attribute = kwargs['attribute']

    # blockdevices = get_disk_info_lshw('/home/cedric/dev/lsidrivemap/falk.lshw')
    # blockdevices = get_disk_info_lshw()
    blockdevices = get_disk_info_lsblk()

    config_file = '~/.config/blockdevices.json'

    try:
        # load from config
        with open(os.path.expanduser(config_file)) as json_file:
            blockdevices_config = json.load(json_file)
            blockdevices, result = load_blockdevice_mapping(blockdevices, blockdevices_config)
            if not result and not kwargs['configure']:
                exit(1)
    except FileNotFoundError as e:
        print(f"No config file found: run `lsmap disks --configure`")
        if not kwargs['configure']:
            exit(1)
    except ValueError as e:
        print(e)
        if not kwargs['configure']:
            exit(1)

    if kwargs['configure']:
        for device_type, devices in blockdevices.items():
            if devices:
                devices = set_devices_mapping(devices, device_type)
                # Save to json config
                # https://stackabuse.com/reading-and-writing-json-to-a-file-in-python/
        save_config(config_file, blockdevices)

    if kwargs['add_labels']:
        for device_type, devices in blockdevices.items():
            if devices:
                devices = set_labels(devices, device_type)
        save_config(config_file, blockdevices)

    data_types = [
        'disk-id',
        'label',
        'name',
        'map-id',
        'map-name',
        'model',
        'port',
        'path',
        'serial',
    ]
    for device_type, devices in blockdevices.items():
        if devices:
            if not attribute:
                if not kwargs['configure'] and not kwargs['add_labels']:
                    print_mapping(devices, 'path', device_type)
            else:
                for data_type in data_types:
                    if attribute == data_type:
                        print_mapping(devices, attribute, device_type)

