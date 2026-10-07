import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add new tool definitions before workspace()
new_tools = """
def tool_wireshark():
    log_action("Opened Tool: Wireshark")
    back_button()
    st.markdown('<div class="tool-header"><div class="tool-title">🦈 Wireshark — Network Analyzer</div><div class="tool-sub">PCAP Analysis | Packet Sniffing</div></div>', unsafe_allow_html=True)
    if st.button("🚀 LAUNCH WIRESHARK (.exe)", use_container_width=True, type="primary"):
        import subprocess
        try:
            subprocess.Popen([r"C:\\Program Files\\Wireshark\\Wireshark.exe"])
            st.success("✅ Launched Wireshark on your Windows Desktop!")
            log_action("Launched Real Wireshark (.exe)")
            log_tool_to_coc("Wireshark", "Launched external GUI application for PCAP analysis.")
        except Exception as e:
            st.error(f"Failed to launch: {e} (Is Wireshark installed in C:\\\\Program Files\\\\Wireshark?)")
            log_tool_to_coc("Wireshark", "Launched Wireshark (Failed/Simulated).")

def tool_burpsuite():
    log_action("Opened Tool: Burp Suite")
    back_button()
    st.markdown('<div class="tool-header"><div class="tool-title">🕸️ Burp Suite — Web Scanner</div><div class="tool-sub">Web Vulnerability Scanning | Intercepting Proxy</div></div>', unsafe_allow_html=True)
    if st.button("🚀 LAUNCH BURP SUITE (.exe)", use_container_width=True, type="primary"):
        import subprocess
        try:
            subprocess.Popen(["cmd.exe", "/c", "start", "burpsuite"])
            st.success("✅ Attempted to launch Burp Suite!")
            log_action("Launched Real Burp Suite")
            log_tool_to_coc("Burp Suite", "Launched external GUI application for web vulnerability scanning.")
        except Exception as e:
            st.error(f"Failed to launch: {e}")

def tool_sleuthkit():
    log_action("Opened Tool: The Sleuth Kit")
    back_button()
    st.markdown('<div class="tool-header"><div class="tool-title">🕵️ The Sleuth Kit (TSK)</div><div class="tool-sub">Command Line File System Forensics | Autopsy Backend</div></div>', unsafe_allow_html=True)
    if st.button("🚀 LAUNCH TSK COMMAND PROMPT", use_container_width=True, type="primary"):
        import subprocess
        try:
            subprocess.Popen(["cmd.exe", "/c", "start", "cmd.exe", "/k", "echo Launching The Sleuth Kit (TSK) Environment..."])
            st.success("✅ Launched TSK Command Prompt!")
            log_action("Launched TSK CLI")
            log_tool_to_coc("The Sleuth Kit", "Launched CLI tools for raw file system parsing.")
        except Exception as e:
            st.error(f"Failed to launch: {e}")

def tool_retina():
    log_action("Opened Tool: Retina")
    back_button()
    st.markdown('<div class="tool-header"><div class="tool-title">👁️ Retina — Network Security Scanner</div><div class="tool-sub">Vulnerability Assessment | Compliance</div></div>', unsafe_allow_html=True)
    if st.button("🚀 LAUNCH RETINA", use_container_width=True, type="primary"):
        st.success("✅ Attempted to launch Retina Scanner!")
        log_action("Launched Retina Scanner")
        log_tool_to_coc("Retina", "Launched network security and vulnerability scanner.")

def tool_nmap():
    log_action("Opened Tool: Nmap")
    back_button()
    st.markdown('<div class="tool-header"><div class="tool-title">🗺️ Nmap — Network Mapper</div><div class="tool-sub">Port Scanning | OS Detection</div></div>', unsafe_allow_html=True)
    if st.button("🚀 LAUNCH NMAP (Zenmap)", use_container_width=True, type="primary"):
        import subprocess
        try:
            subprocess.Popen(["cmd.exe", "/c", "start", "zenmap"])
            st.success("✅ Attempted to launch Nmap (Zenmap GUI)!")
            log_action("Launched Nmap")
            log_tool_to_coc("Nmap", "Launched Network Mapper for port and service enumeration.")
        except Exception as e:
            st.error(f"Failed to launch: {e}")

def tool_hydra():
    log_action("Opened Tool: Hydra")
    back_button()
    st.markdown('<div class="tool-header"><div class="tool-title">🐉 Hydra — Network Logon Cracker</div><div class="tool-sub">Brute Force Authentication Cracking</div></div>', unsafe_allow_html=True)
    if st.button("🚀 LAUNCH HYDRA CLI", use_container_width=True, type="primary"):
        import subprocess
        try:
            subprocess.Popen(["cmd.exe", "/c", "start", "cmd.exe", "/k", "echo Type 'hydra -h' to see usage..."])
            st.success("✅ Launched Command Prompt for Hydra!")
            log_action("Launched Hydra CLI")
            log_tool_to_coc("Hydra", "Launched Hydra for authentication cracking.")
        except Exception as e:
            st.error(f"Failed to launch: {e}")

# ══════════════════════════════════════════════════════════════════════════════
#  WORKSPACE DASHBOARD (Case Management & Tools)
"""

content = content.replace("# ══════════════════════════════════════════════════════════════════════════════\n#  WORKSPACE DASHBOARD (Case Management & Tools)", new_tools)

# 2. Update tools_map
old_tools_map = '''    tools_map = {
        "ftk": tool_ftk, "defender": tool_defender, "sandbox": tool_sandbox,
        "volatility": tool_volatility, "cellebrite": tool_cellebrite, 
        "autopsy": tool_autopsy, "exiftool": tool_exiftool, "virustotal": tool_virustotal
    }'''
new_tools_map = '''    tools_map = {
        "ftk": tool_ftk, "defender": tool_defender, "sandbox": tool_sandbox,
        "volatility": tool_volatility, "cellebrite": tool_cellebrite, 
        "autopsy": tool_autopsy, "exiftool": tool_exiftool, "virustotal": tool_virustotal,
        "wireshark": tool_wireshark, "burpsuite": tool_burpsuite, "sleuthkit": tool_sleuthkit,
        "retina": tool_retina, "nmap": tool_nmap, "hydra": tool_hydra
    }'''
content = content.replace(old_tools_map, new_tools_map)

# 3. Update tool_cards list
old_cards = 'tool_cards = [("🖥️", "FTK Imager", "Disk imaging · Hash verification", "ftk"), ("🗂️", "Autopsy", "File system analysis · Carving", "autopsy"), ("📷", "ExifTool", "Metadata extraction · GPS maps", "exiftool"), ("🛡️", "Microsoft Defender", "Threat scanning · ATP", "defender"), ("📦", "Sandbox Environment", "Malware detonation", "sandbox"), ("🌐", "VirusTotal API", "Hash & IP Reputation", "virustotal"), ("🧠", "Volatility 3", "Memory forensics · Rootkits", "volatility"), ("📱", "Cellebrite UFED", "Mobile extraction · iOS/Android", "cellebrite")]'

new_cards = 'tool_cards = [("🖥️", "FTK Imager", "Disk imaging", "ftk"), ("🗂️", "Autopsy", "File system carving", "autopsy"), ("📷", "ExifTool", "Metadata extraction", "exiftool"), ("🛡️", "Defender", "Threat scanning", "defender"), ("📦", "Sandbox", "Malware detonation", "sandbox"), ("🌐", "VirusTotal", "Hash Reputation", "virustotal"), ("🧠", "Volatility 3", "Memory forensics", "volatility"), ("📱", "Cellebrite", "Mobile extraction", "cellebrite"), ("🦈", "Wireshark", "Network PCAP", "wireshark"), ("🕸️", "Burp Suite", "Web vulnerabilities", "burpsuite"), ("🕵️", "Sleuth Kit", "Command Line FS", "sleuthkit"), ("👁️", "Retina", "Network scanner", "retina"), ("🗺️", "Nmap", "Port scanning", "nmap"), ("🐉", "Hydra", "Logon cracker", "hydra")]'

content = content.replace(old_cards, new_cards)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")
