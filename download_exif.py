import urllib.request, re, zipfile, os
url = 'https://exiftool.org/'
try:
    html = urllib.request.urlopen(url).read().decode('utf-8')
    match = re.search(r'href="(exiftool-\d+\.\d+\.zip)"', html)
    if match:
        zip_url = url + match.group(1)
        print('Downloading', zip_url)
        urllib.request.urlretrieve(zip_url, 'exiftool.zip')
        with zipfile.ZipFile('exiftool.zip', 'r') as zip_ref:
            zip_ref.extractall('.')
        os.rename('exiftool(-k).exe', 'exiftool.exe')
        print('Success!')
    else:
        print('Failed to find zip link')
except Exception as e:
    print('Error:', e)
