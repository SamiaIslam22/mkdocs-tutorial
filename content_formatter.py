import re
import os
from pathlib import Path


def clean_and_format_content(content):
    """
    Clean and format scraped content for better readability
    """
    # Remove excessive whitespace and clean up
    content = re.sub(r"\n\s*\n\s*\n+", "\n\n", content)

    # Fix date formatting - make them proper headings
    content = re.sub(
        r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s*([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?,?\s*\d{4})",
        r"\n## \1, \2\n",
        content,
    )

    # Clean up event titles - make them subheadings
    content = re.sub(
        r"^([A-Z][^.!?]*(?:VIRTUAL|Social|Expo|Summit|Day)[^.!?]*)\s*$",
        r"\n### \1\n",
        content,
        flags=re.MULTILINE,
    )

    # Format locations with admonition
    content = re.sub(
        r"Location:\s*([^.!?]+(?:\.|!|\?|$))",
        r'\n!!! info "Location"\n    \1\n',
        content,
    )

    # Clean up image references and file names
    content = re.sub(
        r"\b\w*\.(jpg|jpeg|png|gif|webp)\b", "", content, flags=re.IGNORECASE
    )
    content = re.sub(
        r"\b[A-Z0-9_]{10,}\b", "", content
    )  # Remove long caps strings (likely file names)

    # Remove duplicate content and clean up
    content = re.sub(r"(\b\w+\b)(\s+\1\b)+", r"\1", content)  # Remove word repetitions

    # Add proper spacing around sections
    content = re.sub(r"(#{2,3}\s+[^\n]+)\n([A-Z])", r"\1\n\n\2", content)

    # Clean up extra spaces
    content = re.sub(r" +", " ", content)
    content = re.sub(r"\n +", "\n", content)

    # Remove standalone numbers/ratios that don't make sense
    content = re.sub(r"\n\d+/\d+\n", "\n", content)

    return content.strip()


def format_activity_page(content):
    """
    Specifically format the activity page content
    """
    lines = content.split("\n")
    formatted_lines = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines but preserve single empty line
        if not line:
            if formatted_lines and formatted_lines[-1] != "":
                formatted_lines.append("")
            i += 1
            continue

        # Format upcoming events section
        if "upcoming" in line.lower():
            formatted_lines.append("## Upcoming Events")
            formatted_lines.append("")

        # Format previous events section
        elif "previous" in line.lower():
            formatted_lines.append("## Previous Events")
            formatted_lines.append("")

        # Keep the line as is for now, cleaning will happen later
        else:
            formatted_lines.append(line)

        i += 1

    content = "\n".join(formatted_lines)
    return clean_and_format_content(content)


def process_markdown_files(directory):
    """
    Process all markdown files in the scraped directory
    """
    scraped_dir = Path(directory) / "docs" / "scraped"

    if not scraped_dir.exists():
        print(f"Directory {scraped_dir} does not exist!")
        return

    # Process all .md files
    for md_file in scraped_dir.rglob("*.md"):
        print(f"Processing: {md_file}")

        try:
            # Read the file
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract title and source from the top
            title_match = re.search(r"^# (.+)$", content, re.MULTILINE)
            source_match = re.search(r"\*\*Source:\*\* \[(.+?)\]\((.+?)\)", content)

            # Remove the title and source from content for processing
            content = re.sub(r"^# .+$", "", content, flags=re.MULTILINE)
            content = re.sub(r"\*\*Source:\*\* \[.+?\]\(.+?\)", "", content)
            content = re.sub(r"^---+$", "", content, flags=re.MULTILINE)

            # Apply formatting
            if "activity" in md_file.name.lower():
                formatted_content = format_activity_page(content)
            else:
                formatted_content = clean_and_format_content(content)

            # Rebuild the file with proper header
            final_content = []
            if title_match:
                final_content.append(f"# {title_match.group(1)}")
                final_content.append("")

            if source_match:
                final_content.append(
                    f"**Source:** [{source_match.group(1)}]({source_match.group(2)})"
                )
                final_content.append("")
                final_content.append("---")
                final_content.append("")

            final_content.append(formatted_content)

            # Write the formatted content back
            with open(md_file, "w", encoding="utf-8") as f:
                f.write("\n".join(final_content))

            print(f"✓ Formatted: {md_file.name}")

        except Exception as e:
            print(f"✗ Error processing {md_file}: {e}")


def main():
    """
    Main function to run the formatter
    """
    # Get the current directory (where the script is run)
    current_dir = os.getcwd()

    print("🔧 Starting content formatting...")
    process_markdown_files(current_dir)


if __name__ == "__main__":
    main()
