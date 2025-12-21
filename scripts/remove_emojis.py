"""
Script to remove emoji characters from logger messages to fix Unicode encoding warnings on Windows
"""
import re
from pathlib import Path

# Emoji to text replacement mapping
EMOJI_REPLACEMENTS = {
    '✅': '[OK]',
    '❌': '[ERROR]',
    '⏸️': '[PAUSED]',
    '📋': '[INFO]',
    '🔄': '[RESUME]',
    '⏳': '[WAITING]',
    '🎉': '[COMPLETE]',
    '📨': '[RECEIVED]',
}

def remove_emojis_from_file(file_path):
    """Remove emoji characters from a Python file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Replace each emoji with text equivalent
    for emoji, replacement in EMOJI_REPLACEMENTS.items():
        content = content.replace(emoji, replacement)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {file_path}")
        return True
    return False

# Files to update
files_to_update = [
    'src/invoice_agent/nodes/workflow_nodes_1.py',
    'src/invoice_agent/nodes/workflow_nodes_2.py',
    'src/invoice_agent/agent/langgraph_workflow.py',
    'src/invoice_agent/agent/workflow_executor.py',
    'src/invoice_agent/api/main.py',
    'src/invoice_agent/api/routes/human_review.py',
]

if __name__ == '__main__':
    updated_count = 0
    for file in files_to_update:
        file_path = Path(file)
        if file_path.exists():
            if remove_emojis_from_file(file_path):
                updated_count += 1
    
    print(f"\n✓ Updated {updated_count} files")
    print("Run the server again to verify no Unicode warnings")
