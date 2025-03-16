#!/bin/bash

# Function to show usage
show_usage() {
    echo "Usage: $0 [-f|--force] [-d|--dirs <directories...>]"
    echo "  -f, --force              Apply changes without confirmation"
    echo "  -d, --dirs <dirs...>     Space-separated list of directories to process (relative to docs/)"
    echo "                           Default: devlog devplan"
    echo "  -h, --help              Show this help message"
}

# Parse command line arguments
FORCE=0
DIRS=("devlog" "devplan")  # Default directories to process

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--force)
            FORCE=1
            shift
            ;;
        -d|--dirs)
            shift
            DIRS=()
            while [[ $# -gt 0 && ! $1 =~ ^- ]]; do
                DIRS+=("$1")
                shift
            done
            if [ ${#DIRS[@]} -eq 0 ]; then
                echo "Error: No directories specified after -d|--dirs"
                show_usage
                exit 1
            fi
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

# Get the docs directory path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
DOCS_DIR="$(dirname "$SCRIPT_DIR")/docs"

# Track if we found any files to process
FOUND_FILES=0

# Process all directories
echo "Previewing changes:"
echo "------------------"
for dir in "${DIRS[@]}"; do
    dir_path="$DOCS_DIR/$dir"
    if [ ! -d "$dir_path" ]; then
        echo "Warning: Directory $dir_path does not exist, creating it..."
        mkdir -p "$dir_path"
        continue
    fi
    
    echo "Processing directory: $dir_path"
    cd "$dir_path" || continue
    
    for file in *.md; do
        # Skip if no md files found
        [[ "$file" == "*.md" ]] && continue
        
        FOUND_FILES=1
        standardize_filename "$file"
    done
done

# Exit if no files found
if [ $FOUND_FILES -eq 0 ]; then
    echo "No .md files found in specified directories."
    exit 0
fi

if [ $FORCE -eq 0 ]; then
    echo -e "\nDo you want to proceed with these changes? [y/N] "
    read -r response
    [[ "$response" =~ ^[Yy]$ ]] || { echo "Operation cancelled."; exit 0; }
fi

echo "Applying changes..."
for dir in "${DIRS[@]}"; do
    dir_path="$DOCS_DIR/$dir"
    [ ! -d "$dir_path" ] && continue
    
    cd "$dir_path" || continue
    
    while IFS= read -r line; do
        if [ -n "$line" ]; then
            read -r old_name new_name <<< "$line"
            mv "$old_name" "$new_name"
            echo "Renamed: $dir/$old_name -> $dir/$new_name"
        fi
    done < <(for file in *.md; do [[ "$file" == "*.md" ]] && continue; standardize_filename "$file"; done)
done
echo "Done!" 