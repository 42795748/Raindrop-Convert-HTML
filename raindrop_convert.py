import pandas as pd
from datetime import datetime
import html

def create_bookmark_html(title, url, created=None):
    """Create an HTML bookmark entry."""
    if created:
        try:
            # Convert ISO format to Unix timestamp
            add_date = int(datetime.fromisoformat(created.replace('Z', '+00:00')).timestamp())
        except (ValueError, AttributeError):
            add_date = int(datetime.now().timestamp())
    else:
        add_date = int(datetime.now().timestamp())
    
    return f'<DT><A HREF="{html.escape(url)}" ADD_DATE="{add_date}">{html.escape(title)}</A>'

class BookmarkFolder:
    def __init__(self, name):
        self.name = name
        self.subfolders = {}  # Dictionary of subfolder name -> BookmarkFolder
        self.bookmarks = []   # List of bookmark HTML strings

def add_to_folder_structure(root, folder_path, bookmark_html):
    """Add a bookmark to the nested folder structure."""
    current = root
    
    if folder_path and pd.notna(folder_path):
        # Split folder path and clean each folder name
        folders = [f.strip() for f in folder_path.split('/')]
        
        # Navigate/create folder structure
        for folder_name in folders:
            if folder_name not in current.subfolders:
                current.subfolders[folder_name] = BookmarkFolder(folder_name)
            current = current.subfolders[folder_name]
    
    current.bookmarks.append(bookmark_html)

def create_folder_structure(bookmarks_df):
    """Create a nested folder structure from the bookmarks DataFrame."""
    root = BookmarkFolder("root")
    
    # Sort bookmarks by folder path to ensure parent folders are processed first
    bookmarks_df = bookmarks_df.sort_values('folder', na_position='last')
    
    # Add each bookmark to the folder structure
    for _, row in bookmarks_df.iterrows():
        bookmark_html = create_bookmark_html(
            title=row['title'] if pd.notna(row['title']) else row['url'],
            url=row['url'],
            created=row['created'] if pd.notna(row['created']) else None
        )
        add_to_folder_structure(root, row['folder'], bookmark_html)
    
    return root

def generate_folder_html(folder, level=0):
    """Recursively generate HTML for a folder and its contents."""
    content = []
    indent = "    " * level
    
    # Add folder header if it's not the root
    if folder.name != "root":
        content.append(f'{indent}<DT><H3>{html.escape(folder.name)}</H3>')
        content.append(f'{indent}<DL><p>')
        level += 1
        indent = "    " * level
    
    # Add bookmarks in this folder
    for bookmark in folder.bookmarks:
        content.append(f'{indent}{bookmark}')
    
    # Add subfolders recursively
    for subfolder in sorted(folder.subfolders.values(), key=lambda x: x.name.lower()):
        content.extend(generate_folder_html(subfolder, level))
    
    # Close folder if it's not the root
    if folder.name != "root":
        content.append(f'{"    " * (level-1)}</DL><p>')
    
    return content

def generate_bookmarks_html(root_folder):
    """Generate the complete bookmarks HTML file."""
    header = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!-- This is an automatically generated file.
     It will be read and overwritten.
     DO NOT EDIT! -->
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>"""

    footer = "</DL><p>"
    
    # Generate content recursively
    content = generate_folder_html(root_folder)
    
    return '\n'.join([header] + content + [footer])

def convert_raindrop_to_browser_bookmarks(input_csv, output_file):
    """Convert Raindrop.io CSV export to browser bookmarks format."""
    try:
        # Read the CSV file
        df = pd.read_csv(input_csv)
        
        # Create nested folder structure
        root_folder = create_folder_structure(df)
        
        # Generate bookmarks HTML
        bookmarks_html = generate_bookmarks_html(root_folder)
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(bookmarks_html)
        
        # Count total folders recursively
        def count_folders(folder):
            return len(folder.subfolders) + sum(count_folders(subfolder) 
                                              for subfolder in folder.subfolders.values())
        
        total_folders = count_folders(root_folder)
        
        print(f"Successfully converted bookmarks to {output_file}")
        print(f"Total bookmarks processed: {len(df)}")
        print(f"Number of folders: {total_folders}")
        
    except Exception as e:
        print(f"Error converting bookmarks: {str(e)}")

if __name__ == "__main__":
    input_csv = "Backups.csv"  # Your input CSV file
    output_file = "bookmarks.html"  # Output HTML file
    convert_raindrop_to_browser_bookmarks(input_csv, output_file)