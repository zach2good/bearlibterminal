# Scripts/clang-format.py
#
# Run from repository root
# Find and run local clang-format on Samples/*, Terminal/Source/*

import os
import subprocess
import sys

def main():
    files = []
    for dir in ['Samples', 'Terminal/Source']:
        for root, _, filenames in os.walk(dir):
            for filename in filenames:
                if filename.endswith(('.cpp', '.hpp')):
                    files.append(os.path.join(root, filename))

    for file in files:
        subprocess.run(['clang-format', '-i', file])

if __name__ == "__main__":
    main()
