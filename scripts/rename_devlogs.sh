#!/bin/bash

# Function to show usage
show_usage() {
    echo "Usage: $0 [-f|--force]"
    echo "  -f, --force    Apply changes without confirmation"
    echo "  -h, --help     Show this help message"
}

# Parse command line arguments
FORCE=0
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--force)
            FORCE=1
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Function to convert a filename to the standard format
standardize_filename() {
    local file="$1"
    local basename=$(basename "$file")
    
    # Skip if file doesn't exist
    [ ! -f "$file" ] && return
    
    # Get file creation date for all files
    created_date=$(stat -f "%SB" -t "%Y-%m-%d" "$file")
    
    # Extract description part, removing any existing date prefix
    desc=$(echo "$basename" | sed -E 's/^([0-9]{4}[-_]?[0-9]{2}[-_]?[0-9]{2}[-_]?)?//')
    
    # Clean up description: remove leading separators, convert to kebab-case
    desc=$(echo "$desc" | sed 's/^[-_]*//' | sed 's/_/-/g')
    
    # Combine date and description
    new_name="${created_date}-${desc}"
    
    echo "$file" "$new_name"
}

# Process all md files in devlog directory
cd "$(dirname "$0")/../docs/devlog" || exit 1

echo "Previewing changes:"
echo "------------------"
for file in *.md; do
    standardize_filename "$file"
done

if [ $FORCE -eq 0 ]; then
    echo -e "\nDo you want to proceed with these changes? [y/N] "
    read -r response
    [[ "$response" =~ ^[Yy]$ ]] || { echo "Operation cancelled."; exit 0; }
fi

echo "Applying changes..."
while IFS= read -r line; do
    if [ -n "$line" ]; then
        read -r old_name new_name <<< "$line"
        mv "$old_name" "$new_name"
        echo "Renamed: $old_name -> $new_name"
    fi
done < <(for file in *.md; do standardize_filename "$file"; done)
echo "Done!" 