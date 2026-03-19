#!/bin/bash

# unzip_all.bash
# Extracts all .zip files in the current directory into folders named after the file.

# 1. Check if there are any zip files in the current directory
# (Prevents the loop from running on a literal '*.zip' string if none exist)
shopt -s nullglob
zip_files=(*.zip)

if [ ${#zip_files[@]} -eq 0 ]; then
    echo "No .zip files found in the current directory."
    exit 1
fi

echo "Found ${#zip_files[@]} .zip file(s). Starting extraction..."

# 2. Loop through each zip file
for f in "${zip_files[@]}"; do
    # Strip the .zip extension to get the clean folder name
    folder_name="${f%.zip}"

    echo "Extracting '$f' into '$folder_name/'..."

    # Unzip quietly (-q) into the destination directory (-d)
    unzip -q "$f" -d "$folder_name"

    # 3. Check if the extraction was successful
    if [ $? -eq 0 ]; then
        echo "  -> Success!"
        # OPTIONAL: Remove the '#' on the line below to delete the zip file after successful extraction
        # rm "$f"
    else
        echo "  -> Error: Failed to extract '$f'"
    fi
done

echo "All done!"
