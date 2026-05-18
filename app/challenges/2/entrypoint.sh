#!/bin/bash
set -e
cd /challenge && python3 -c "from app import FLAG; open('/opt/index.html', 'w').write(f'<title>{{{FLAG}}}</title>')"
python3 -m http.server 8080 --directory /opt/ &
/usr/bin/python3 /challenge/core.py 9002
