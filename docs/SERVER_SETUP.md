# Minimal Ubuntu Server AmneziaWG setup

Install a supported AmneziaWG package for your Ubuntu release, then:
```bash
sudo apt update
sudo apt install -y curl iptables
sudo modprobe amneziawg
sudo mkdir -p /etc/amnezia/amneziawg
sudo chmod 700 /etc/amnezia/amneziawg
cd /etc/amnezia/amneziawg
awg genkey | tee server_private.key | awg pubkey > server_public.key
awg genkey | tee client_private.key | awg pubkey > client_public.key
```
Create `/etc/amnezia/awg0.conf` with placeholders only:
```ini
[Interface]
Address = 10.66.66.1/24
ListenPort = 51820
PrivateKey = <SERVER_PRIVATE_KEY>
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -A FORWARD -o %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -D FORWARD -o %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE
[Peer]
PublicKey = <CLIENT_PUBLIC_KEY>
AllowedIPs = 10.66.66.2/32
```
```bash
echo 'net.ipv4.ip_forward=1' | sudo tee /etc/sysctl.d/99-amneziawg.conf
sudo sysctl --system
sudo chmod 600 /etc/amnezia/awg0.conf /etc/amnezia/amneziawg/*_private.key
sudo systemctl enable --now awg-quick@awg0
sudo awg show
```
Build the client using `<CLIENT_PRIVATE_KEY>`, `<SERVER_PUBLIC_KEY>`, and `<SERVER_PUBLIC_IP>:51820`. Never publish keys.
