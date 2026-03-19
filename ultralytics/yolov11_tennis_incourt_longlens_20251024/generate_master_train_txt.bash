#!/bin/bash

# Clear out any old master file
> master_train.txt

# Check if you actually provided any folders
if [ "$#" -eq 0 ]; then
    echo "Error: You must specify which folders to merge."
    echo "Usage: ./merge_selected.bash folder1 folder2 ..."
    exit 1
fi

# Loop through every folder you passed in the command line ("$@")
for folder in "$@"; do
    txt_path="$folder/Train.txt"

    # Verify the folder actually contains a Train.txt
    if [ -f "$txt_path" ]; then
        # Strip leading slashes and prepend the folder name
        sed 's|^\./||' "$txt_path" | sed "s|^|$folder/|" >> master_train.txt
        echo "✅ Added: $folder"
    else
        echo "⚠ Warning: No Train.txt found in '$folder' (Skipped)"
    fi
done

echo "Done! Master file has $(wc -l < master_train.txt) images."
