# PhaethonVPN

**PhaethonVPN** is a free, open-source VPN designed to connect you securely and privately—anywhere, anytime. It prioritizes user privacy while maintaining ease of use.

---

## ⚙ Requirements/Installation

- **Python** 3.10 or higher  
- **Operating System**: Currently supports **Windows only**.  
  Support for **Linux** and **macOS** is actively in development.

---

## ✅ Installation Instructions
### 1. Install Python 3.10+
Make sure you are using Python 3.10 or higher. You can check this by running:
```bash
python --version
```
If not installed, download it from: https://www.python.org/downloads/
### 2. Create and activate a virtual environment (optional but recommended)
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Unix/macOS:
source venv/bin/activate
```
### 3. Install required Python packages
Ensure you have a requirements.txt file (provided below), then install with:
```bash
pip install -r requirements.txt
```
### (OPTIONAL) 4. Replace relay.csv
Ensure the following file exists:
```bash
./servers/tor_relays_by_country.csv
```
Feel free to replace the list to use your own dataset, make sure it follows the following format:
```bash
ip,country_code,port
1.2.3.4,us,9001
...
```
---

## 🚀 How to Run

1. Open a terminal and navigate to the cloned repository directory.
2. Run the script:
```bash
python main.py
```
3. Grant administrator privileges when prompted.
4. Choose a country from the displayed list of available country codes.
5. Wait while PhaethonVPN locates the fastest and most reliable relay.
6. Once connected, enjoy private browsing through the VPN tunnel.

## ⚠️ Disclaimer
While PhaethonVPN does not log any data locally or send information to centralized servers, it uses **volunteer-run servers**, which may log activity depending on the operator. Use at your own discretion when handling sensitive data.

## 👤 About
This project is developed and maintained by a single student passionate about open privacy tools and decentralized networking. Buy him a coffee

[![Buy Me a Coffee](https://img.shields.io/badge/Buy_Me_A_Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/s3ba)
