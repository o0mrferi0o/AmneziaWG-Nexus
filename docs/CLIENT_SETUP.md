# Client setup (Arch / Garuda)

```bash
sudo pacman -Syu python python-gobject gtk4 libadwaita curl
# Install an approved AmneziaWG package providing awg and awg-quick.
command -v awg awg-quick
sudo mkdir -p /etc/amnezia
sudo cp ~/Downloads/awg0.conf /etc/amnezia/
sudo chmod 600 /etc/amnezia/awg0.conf
./install.sh
amneziawg-nexus
```
Select the profile in Nexus. PolicyKit authenticates individual tunnel commands; do not launch the GUI with sudo.
