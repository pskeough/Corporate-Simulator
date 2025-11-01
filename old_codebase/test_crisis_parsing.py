from engines.visual_engine import _parse_crisis_prompts
from engines.prompt_loader import load_prompt

content = load_prompt('visuals/crisis_illustration')
sections = content.split('---')
print(f'Found {len(sections)} sections\n')

for i, section in enumerate(sections):
    section = section.strip()
    if not section:
        print(f'Section {i}: EMPTY')
        continue

    # Check if it starts with ##
    lines = section.split('\n')
    header = None
    for line in lines:
        if line.startswith('## '):
            header = line
            break

    print(f'Section {i}: Header = {header}, Length = {len(section)} chars')

print('\n' + '='*60)
print('Testing parser:')
print('='*60)

prompts = _parse_crisis_prompts(content)
print(f'\nParsed {len(prompts)} crisis types:')
for key in prompts.keys():
    print(f'  - {key}: {len(prompts[key])} chars')
