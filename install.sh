#!/usr/bin/env bash
set -euo pipefail
[[ $(id -u) -ne 0 ]] || { echo 'Run as a normal user; sudo is requested only for installation.' >&2; exit 1; }
command -v pacman >/dev/null || { echo 'AmneziaWG-Nexus supports Arch/Garuda (pacman) only.' >&2; exit 1; }
missing=(); for p in python python-gobject gtk4 libadwaita curl; do pacman -Q "$p" >/dev/null 2>&1 || missing+=("$p"); done
if ((${#missing[@]})); then sudo pacman -S --needed "${missing[@]}"; fi
for tool in awg awg-quick; do command -v "$tool" >/dev/null || echo "Warning: $tool is missing; install an AmneziaWG package before connecting." >&2; done
root=$(cd "$(dirname "$0")" && pwd)
sudo install -d /usr/local/lib/amneziawg-nexus/assets/styles /usr/share/icons/hicolor/scalable/apps /usr/share/applications /etc/amnezia
sudo cp -a "$root/app" /usr/local/lib/amneziawg-nexus/
sudo install -m 644 "$root/assets/styles/main.css" /usr/local/lib/amneziawg-nexus/assets/styles/main.css
sudo install -m 644 "$root/assets/icons/amneziawg-nexus.svg" /usr/share/icons/hicolor/scalable/apps/amneziawg-nexus.svg
sudo install -m 644 "$root/data/amneziawg-nexus.desktop" /usr/share/applications/amneziawg-nexus.desktop
printf '#!/usr/bin/env bash\nexport PYTHONPATH=/usr/local/lib/amneziawg-nexus${PYTHONPATH:+:$PYTHONPATH}\nexec python3 -m app.main "$@"\n' | sudo tee /usr/local/bin/amneziawg-nexus >/dev/null
sudo chmod 755 /usr/local/bin/amneziawg-nexus
echo 'AmneziaWG-Nexus installed. Launch with: amneziawg-nexus'
