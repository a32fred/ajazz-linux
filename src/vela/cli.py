"""Read-only command line interface; no Qt import and no implicit demo fallback."""
import argparse
from dataclasses import asdict
import json
import sys

from .domain import VelaError
from .service import MouseService


def run(argv=None, *, service_factory=MouseService, stdout=None, stderr=None):
    stdout, stderr = stdout or sys.stdout, stderr or sys.stderr
    parser = argparse.ArgumentParser(prog='vela --cli', description='Read AJ199 devices as JSON. No settings are written.')
    parser.add_argument('command', choices=('scan', 'status', 'dump', 'listen'))
    parser.add_argument('--demo', action='store_true', help='Use the in-memory simulator only')
    parser.add_argument('--device', help='Exact device ID from scan; required if several are found')
    parser.add_argument('--length', type=lambda text: int(text, 0), default=0x1000, help='dump: bytes to read from address 0 (default 0x1000)')
    parser.add_argument('--seconds', type=int, default=30, help='listen: how long to listen (default 30)')
    args = parser.parse_args(argv)
    service = service_factory(demo=args.demo)
    try:
        devices = service.scan()
        if args.command == 'scan':
            document = {'demo': args.demo, 'devices': [
                {key: getattr(item, key) for key in ('id', 'name', 'vid', 'pid', 'serial')} for item in devices]}
        else:
            matches = [d for d in devices if args.device is None or d.id == args.device]
            if not matches:
                raise VelaError('No matching mouse found. Run scan; on Linux check hidraw permissions.')
            if len(matches) != 1:
                raise VelaError('Several mice found. Choose an exact --device ID from scan.')
            snapshot = service.connect(matches[0])
            if args.command == 'dump':
                document = {'demo': args.demo, 'device': snapshot.device.id, 'regions': {'0x0000': service.dump(args.length).hex()}}
            elif args.command == 'listen':
                document = {'demo': args.demo, 'device': snapshot.device.id, 'seconds': args.seconds,
                            'reports': [{'at': at, 'events': events, 'raw': raw} for at, events, raw in service.listen(args.seconds)]}
            else:
                document = {'demo': args.demo, 'device': snapshot.device.id,
                    'battery_percent': snapshot.battery_percent, 'charging': snapshot.charging,
                    'current_profile': snapshot.current_profile, 'firmware': snapshot.firmware,
                    'settings': asdict(snapshot.settings), 'macros': [asdict(m) for m in service.macros]}
        print(json.dumps(document, ensure_ascii=False, indent=2), file=stdout)
        return 0
    except (VelaError, OSError) as exc:
        print(f'Vela: {exc}', file=stderr)
        return 1
    finally:
        service.disconnect()
