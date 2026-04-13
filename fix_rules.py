import glob
import os

files = glob.glob('**/*rules*', recursive=True) + glob.glob('**/team_project_rules.md', recursive=True) + glob.glob('team_project_rules.md')
files = list(set(files))

for file_path in files:
    if os.path.isfile(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace the problematic triple backticks inline
        content = content.replace('```jsx`, ```python`, ```java`', r'`jsx`, `python`, `java`')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
print('Fixed backticks in:', files)
