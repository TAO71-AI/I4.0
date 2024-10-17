# Install I4.0's system requirements
> [!NOTE]
> If you're using Windows, it's recommended to use WSL for I4.0.
> All the instructions here are for Debian and Arch GNU/Linux.

## Download Git
### Debian-based distributions
```bash
sudo apt-get update
sudo apt-get install git git-lfs
```

### Arch-based distributions
```bash
sudo pacman -Sy git git-lfs
```

---

## Download Python
### Debian-based distributions
```bash
sudo apt-get install software-properties-common curl  # Pre-requisites
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv python3.11-distutils  # Install Python 3.11 (recommended version)
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11  # Install PIP for Python 3.11
```

### Arch-based distributions
```bash
# Pre-requisites
git clone https://aur.archlinux.org/yay.git
cd yay
makepkg -si

yay -S python311  # Install Python 3.11 (recommended version)
```

---

## Download CMake
### Debian-based distributions
```bash
sudo apt-get install cmake
```

### Arch-based distributions
```bash
sudo pacman -S cmake
```