import re
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('log_action("Launched Real FTK Imager (.exe)")', 'log_action("Launched Real FTK Imager (.exe)")\n            log_tool_to_coc("FTK Imager", "Launched external GUI application for disk imaging.")')
content = content.replace('log_action("Launched Real Autopsy (.exe)")', 'log_action("Launched Real Autopsy (.exe)")\n            log_tool_to_coc("Autopsy", "Launched external GUI application for disk analysis.")')
content = content.replace('log_action("Launched Windows Sandbox")', 'log_action("Launched Windows Sandbox")\n            log_tool_to_coc("Windows Sandbox", "Launched isolated Windows Sandbox for malware detonation.")')
content = content.replace('log_action("Launched Command Prompt for Volatility")', 'log_action("Launched Command Prompt for Volatility")\n            log_tool_to_coc("Volatility 3", "Launched Command Prompt for memory forensics.")')
content = content.replace('log_action("Checked for Cellebrite Hardware")', 'log_action("Checked for Cellebrite Hardware")\n            log_tool_to_coc("Cellebrite UFED", "Initiated Mobile Extraction hardware check.")')
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")
