#!/usr/bin/env bash
set -euo pipefail
sudo rm -rf /usr/local/lib/amneziawg-nexus /usr/local/bin/amneziawg-nexus
sudo rm -f /usr/share/applications/amneziawg-nexus.desktop /usr/share/icons/hicolor/scalable/apps/amneziawg-nexus.svg
if [[ ${1:-} == --purge-profiles ]]; then sudo rm -rf /etc/amnezia; else echo 'VPN profiles under /etc/amnezia were preserved.'; fi
echo 'AmneziaWG-Nexus removed.'
