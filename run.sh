#!/bin/bash
cat > README.md << eof
# 40K-ancient-list
Just a way to list all of the new ancient adjectives and their behavior
## All Ancient Adjectives and Item Types:
eof
python3 parse_ancients.py >> README.md
