#!/bin/bash

# merge_datasets.bash
# Merges multiple _{idx} folders into a single _{largest_idx}_merged folder.

shopt -s nullglob

# 1. Find all directories starting with "_"
dirs=(_*/)
# Remove the trailing slashes for easier processing
dirs=("${dirs[@]%/}")

if [ ${#dirs[@]} -eq 0 ]; then
    echo "No directories starting with '_' found."
    exit 1
fi

# 2. Find the largest idx
max_idx=-1
for d in "${dirs[@]}"; do
    # Strip the leading underscore
    rest="${d#_}"
    # Keep only the leading digits
    idx="${rest%%[!0-9]*}"

    # Check if we successfully extracted a number
    if [[ -n "$idx" ]] && [[ "$idx" =~ ^[0-9]+$ ]]; then
        if (( idx > max_idx )); then
            max_idx=$idx
        fi
    fi
done

if [[ max_idx -eq -1 ]]; then
    echo "Could not find any valid indices in the folder names."
    exit 1
fi

# 3. Create the merged directory structure
merged_dir="_${max_idx}_merged"
echo "Largest index found: $max_idx"
echo "Creating merged directory: $merged_dir/"

mkdir -p "$merged_dir/labels"
> "$merged_dir/Train.txt" # Initialize empty Train.txt
yaml_moved=false

# 4. Process each directory
for d in "${dirs[@]}"; do
    # Skip if it is the merged directory itself
    if [[ "$d" == "$merged_dir" ]]; then continue; fi

    echo "  -> Merging contents from: $d"

    # --- A. Merge labels ---
    if [ -d "$d/labels" ]; then
        # cp -a safely merges subdirectories together, rm acts as the "move"
        cp -a "$d/labels/." "$merged_dir/labels/"
        rm -rf "$d/labels"
    fi

    # --- B. Append Train.txt ---
    if [ -f "$d/Train.txt" ]; then
        cat "$d/Train.txt" >> "$merged_dir/Train.txt"
        # Add a protective newline so paths don't accidentally merge on the same line
        echo "" >> "$merged_dir/Train.txt"
        rm "$d/Train.txt" # Clean up original
    fi

    # --- C. Move one data.yaml ---
    if [ -f "$d/data.yaml" ]; then
        if [ "$yaml_moved" = false ]; then
            mv "$d/data.yaml" "$merged_dir/data.yaml"
            yaml_moved=true
        else
            # If we already moved the first one, just delete the redundant ones
            rm "$d/data.yaml"
        fi
    fi
done

# Clean up any blank lines in the final merged Train.txt
sed -i '/^$/d' "$merged_dir/Train.txt"

echo "Merge complete! All data consolidated into $merged_dir/"
