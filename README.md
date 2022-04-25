lsmap
=====

This tool is intended to create a physical map of which drive is in which slot.

## Example output

    root@nas:~# lsmap disks
    ATA DEVICES:
    ╒══════════╤══════════╕
    │ /dev/sdi │ /dev/sdh │
    ├──────────┼──────────┤
    │ /dev/sdj │ /dev/sdg │
    ├──────────┼──────────┤
    │ /dev/sdf │ /dev/sdd │
    ├──────────┼──────────┤
    │ /dev/sda │ /dev/sdc │
    ├──────────┼──────────┤
    │ /dev/sdb │ /dev/sde │
    ╘══════════╧══════════╛

    NVME DEVICES:
    ╒══════════════╕
    │ /dev/nvme0n1 │
    ╘══════════════╛

    root@nas:~# lsmap disks disk-id
    ATA DEVICES:
    ╒═══════════════════════════════════════════╤══════════════════════════════════════════╕
    │      ata-ST2000LM007-XXXXXXXXXXXXXXX      │ ata-WDC_XXXXXXXX-XXXXXXXXXXXXXXXXXXXXXXX │
    ├───────────────────────────────────────────┼──────────────────────────────────────────┤
    │ ata-ST1000LM024_XXXXXXXXXX_XXXXXXXXXXXXXX │ ata-WDC_XXXXXXXXXXXXXXXX_XXXXXXXXXXXXXXX │
    ├───────────────────────────────────────────┼──────────────────────────────────────────┤
    │  ata-HGST_XXXXXXXXXXXXXXX_XXXXXXXXXXXXXX  │ ata-HGST_XXXXXXXXXXXXXXX_XXXXXXXXXXXXXX  │
    ├───────────────────────────────────────────┼──────────────────────────────────────────┤
    │  ata-HGST_XXXXXXXXXXXXXXX_XXXXXXXXXXXXXX  │ ata-HGST_XXXXXXXXXXXXXXX_XXXXXXXXXXXXXX  │
    ├───────────────────────────────────────────┼──────────────────────────────────────────┤
    │  ata-HGST_XXXXXXXXXXXXXXX_XXXXXXXXXXXXXX  │     ata-TOSHIBA_XXXXXXXXXX_XXXXXXXXX     │
    ╘═══════════════════════════════════════════╧══════════════════════════════════════════╛

    NVME DEVICES:
    ╒════════════════════════════════════════════════╕
    │ nvme-SAMSUNG MZVPV256HDGL-XXXXXXXXXXXXXXXXXXXX │
    ╘════════════════════════════════════════════════╛

    root@nas:~# lsmap disks map-name
    ATA DEVICES:
    ╒═════════╤═════════╕
    │ disk A1 │ disk B1 │
    ├─────────┼─────────┤
    │ disk A2 │ disk B2 │
    ├─────────┼─────────┤
    │ disk A3 │ disk B3 │
    ├─────────┼─────────┤
    │ disk A4 │ disk B4 │
    ├─────────┼─────────┤
    │ disk A5 │ disk B5 │
    ╘═════════╧═════════╛

    NVME DEVICES:
    ╒═════════╕
    │ disk A1 │
    ╘═════════╛

    root@nas:~# lsmap disks port
    ATA DEVICES:
    ╒═══╤═══╕
    │ 8 │ 7 │
    ├───┼───┤
    │ 9 │ 6 │
    ├───┼───┤
    │ 5 │ 3 │
    ├───┼───┤
    │ 0 │ 2 │
    ├───┼───┤
    │ 1 │ 4 │
    ╘═══╧═══╛

    NVME DEVICES:
    ╒═══╕
    │ 0 │
    ╘═══╛

This tool is inspired from [lsidrivemap](https://github.com/louwrentius/lsidrivemap)


## Configuration

The tool can be configured using `lsmap --reconfigure` to make the correspondence
between logical en physical layout.

## Requirements
- The script requires Python 3 and python3-tabulate.

## TODO
- Support for nvme drives.
- In the future the tool may also show the temperature of the drive (using `hddtemp` or
similar tool).

Contributions are welcome!
