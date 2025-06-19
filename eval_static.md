# Static Evaluation Results - Base vs Fine-tuned Model

| Prompt | Base Output | Fine-tuned Output | ROUGE-L | Quality (0-2) |
|--------|-------------|-------------------|---------|---------------|
| Create a new Git branch and switch to it. | `Use: git checkout -b <branch-name> Switch to the new branch named "my-new-branch". Use: git switch -c <branch-name> Switch to the current branch named "my-new-branch".` | `Use: git checkout -b <branch-name> Switch to the new branch named "my-new-branch". Use: git switch -c <branch-name> Switch to the current branch named "my-new-branch".` | 0.256 | 1 |
| Compress the folder reports into reports.tar.gz. | `Use tar -czvf reports.tar.gz reports/ && mv reports.tar.gz reports/ || echo "Error compressing reports" && exit 1 # Use tar -czvf reports.tar.gz reports/` | `Use tar -czvf reports.tar.gz reports/ && mv reports.tar.gz reports/ || echo "Error compressing reports" && exit 1 # Use tar -czvf reports.tar.gz reports/` | 0.303 | 0 |
| List all Python files in the current directory recursively. | `Use: find. -type f -name '*.py' Use: find. -type f -name '*.py' -print0 | xargs -0 basename # or: find. -type f -name '*.py` | `Use: find. -type f -name '*.py' Use: find. -type f -name '*.py' -print0 | xargs -0 basename # or: find. -type f -name '*.py` | 0.000 | 1 |
| Set up a virtual environment and install requests. | `Use: python -m venv env && source env/bin/activate && pip install requests Alternatively: Use: python -m venv env && source env/bin/activate && pip install -U pip` | `Use: python -m venv env && source env/bin/activate && pip install requests Alternatively: Use: python -m venv env && source env/bin/activate && pip install -U pip` | 0.118 | 1 |
| Fetch only the first ten lines of a file named output.log. | `git log --first-line=10 output.log || true # or use --first-line=10 or --first-line=10 --first-line=1000000000000` | `git log --first-line=10 output.log || true # or use --first-line=10 or --first-line=10 --first-line=1000000000000` | 0.250 | 1 |
| Delete all files with .tmp extension in /tmp directory safely. | `Use: find /tmp -name '*.tmp' -delete Use: find /tmp -type d -name '*.tmp' -delete Use: find /tmp -type f -name '*.tmp' -delete Use:` | `Use: find /tmp -name '*.tmp' -delete Use: find /tmp -type d -name '*.tmp' -delete Use: find /tmp -type f -name '*.tmp' -delete Use:` | 0.182 | 1 |
| Find and replace text 'old_text' with 'new_text' in all .py files recursively. | `Use: find. -type f -name '*.py' -exec sed -i's/old_text/new_text/g' {} + Replace 'old_text' with 'new_text' in all.py` | `Use: find. -type f -name '*.py' -exec sed -i's/old_text/new_text/g' {} + Replace 'old_text' with 'new_text' in all.py` | 0.526 | 1 |

## Summary Metrics
- **Average ROUGE-L**: 0.234
- **Average Quality**: 0.9
- **Valid Commands**: 0/7
- **Improvement over base**: Minimal (identical outputs in all cases)
