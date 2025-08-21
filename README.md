# HackMyVM CLI

A powerful Python command-line interface for interacting with the [HackMyVM](https://hackmyvm.eu) platform. This tool enables cybersecurity practitioners to efficiently search, download, and manage virtual machines with persistent authentication and comprehensive filtering capabilities.

## ✨ Features

- **🔍 Advanced Machine Search**
  - Multiple filter options: difficulty, category, tags, and machine names
  - Color-coded difficulty levels for quick identification
  - Pagination support for large result sets
  - Real-time search with partial name matching

- **🎯 Difficulty Level Filtering** with visual indicators:
  - 🟢 **Easy** → Green highlighting
  - 🟡 **Medium** → Yellow highlighting  
  - 🔴 **Hard** → Red highlighting

- **📂 Category & Tag Filtering**
  - Categories: `windows`, `linux`, `size`, `hacked`, `all`
  - 25+ specialized tags: `web`, `docker`, `suid`, `sqli`, `cve`, etc.

- **⚡ Efficient Operations**
  - Flag submission for completed challenges
  - Direct machine downloads as ZIP files
  - Writeup search functionality
  - Persistent session management

- **🔐 Secure Authentication**
  - Encrypted credential storage
  - Automatic session persistence
  - No repeated login requirements

## 🚀 Quick Start

### Prerequisites
- Python 3.6 or higher
- Active HackMyVM account

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Yanxinwu946/hackmyvm-cli.git
   cd hackmyvm-cli
   ```

2. **Install dependencies**
   ```bash
   pip install requests beautifulsoup4 prettytable
   ```

3. **Configure credentials**
   ```bash
   python3 hmvcli.py config
   ```

4. **Start exploring**
   ```bash
   python3 hmvcli.py search
   ```

### Optional: Global Installation

For system-wide access, create a symbolic link:
```bash
chmod +x hmvcli.py
sudo ln -s $(pwd)/hmvcli.py /usr/local/bin/hmvcli
```

Then use `hmvcli` instead of `python3 hmvcli.py`

## 📖 Usage Guide

### Initial Setup
Configure your HackMyVM credentials (required for first use):
```bash
hmvcli config
```
*This creates `~/.hmv_config.json` with encrypted credential storage.*

### Machine Search & Discovery

#### Basic Operations
```bash
# List all available machines (first page)
hmvcli search

# Search by machine name (partial matching)
hmvcli search -n todd
hmvcli search -n aria

# Filter by difficulty level
hmvcli search -l easy
hmvcli search -l medium
hmvcli search -l hard
```

#### Advanced Filtering
```bash
# Filter by specialized tags
hmvcli search -t web
hmvcli search -t docker
hmvcli search -t sqli

# Combine filters with pagination
hmvcli search -f medium -p 2
hmvcli search -t web -f hard

# Browse by categories
hmvcli search -l windows
hmvcli search -l linux
```

#### Available Tags
`bruteforce` • `suid` • `wordpress` • `cron` • `smb` • `docker` • `sudo` • `web` • `fileupload` • `pathhijacking` • `stego` • `binary` • `capabilities` • `cve` • `commandinjection` • `portknocking` • `ssti` • `libraryhijack` • `sqli` • `lfi` • `rce` • `logpoisoning` • `nfs` • `xxe`

### Writeup Discovery
Search for community writeups and walkthroughs:
```bash
hmvcli writeup Todd
hmvcli writeup "machine name"
```

### Flag Submission
Submit flags for completed challenges:
```bash
hmvcli flag -i "flag{your_captured_flag}" -vm MachineName
```

### Machine Downloads
Download virtual machines for local setup:
```bash
hmvcli download Soul
hmvcli download TryHarder
```

### Help & Documentation
```bash
hmvcli --help              # Main help
hmvcli search --help       # Search options
hmvcli flag --help         # Flag submission help
```

## ⚙️ Configuration & Files

### Configuration Files
- **`~/.hmv_config.json`** - Stores your HackMyVM credentials securely
- **`~/.hmv_session.pkl`** - Maintains active session data
- **`~/.hmv_writeups.csv`** - Cached writeup database (auto-updated)

### Pagination Behavior
- **Basic search**: Returns paginated results (use `-p` for navigation)
- **Filtered searches** (`-l`, `-n`, `-t`): Return all matching results
- **Client-side filtering** (`-f`): Works with pagination for refined browsing

### Security Notes
- Credentials are stored locally in JSON format
- Session data persists until manual credential update
- Never share configuration files containing your credentials

## 🔧 Technical Details

### Dependencies
- **requests** - HTTP client for API communication
- **beautifulsoup4** - HTML parsing and data extraction
- **prettytable** - Formatted console output

### Compatibility
- **Python**: 3.6+ required
- **Platform**: Cross-platform (Linux, macOS, Windows)
- **Authentication**: Persistent session management

### Data Sources
- Machine data: Web scraping from HackMyVM platform
- Writeups: Community-contributed walkthroughs
- Downloads: Direct links to official machine archives



## 🙏 Acknowledgments


Thanks to the HackMyVM community for providing a great platform for cybersecurity practice.