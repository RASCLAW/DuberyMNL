import os, json, re

images = []
for root, dirs, files in os.walk('.'):
    # Skip passed/, failed/, and don't pick up loose root files here
    parts = root.replace(os.sep, '/').split('/')
    if 'passed' in parts or 'failed' in parts:
        continue
    if root == '.':
        continue
    for f in sorted(files):
        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            path = os.path.join(root, f).replace(os.sep, '/').lstrip('./')
            folder = path.split('/')[0]
            images.append({'folder': folder, 'name': f, 'path': path})

# Root-level images
for f in sorted(os.listdir('.')):
    if os.path.isfile(f) and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
        images.append({'folder': 'loose', 'name': f, 'path': f})

with open('index.html', 'r') as fh:
    content = fh.read()

data_json = json.dumps(images, ensure_ascii=False)
content = re.sub(r'const IMAGES_DATA = \[.*?\];', f'const IMAGES_DATA = {data_json};', content)

with open('index.html', 'w') as fh:
    fh.write(content)

print(f'{len(images)} images injected')
