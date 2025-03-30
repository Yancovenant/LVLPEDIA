from pdfminer.high_level import extract_text
import re

def extract_clean_text(pdf_path, start_page=1, end_page=None, check_page_numbers=True):
    """
        pdf_path : uploaded pdf file path,
        start_page : int(), default = 1,
        end_page : int(), default = None,
        check_page_number : bool(), default = True,
    """

    # extract text from pdf with pages selection
    text = extract_text(pdf_path, page_numbers=range(start_page-1, end_page) if end_page else None)

    # PDFMiner separates pages using '\f' (form feed character)
    pages = text.split("\f")

    # pattern to check
    valid_endings = (".", "!", "?", '"', "”", "»", "«")  # Common sentence-ending characters
    title_pattern = re.compile(r"^(?![IVXLCDM]+$)[A-Z][A-Z\s,.:'’-]{3,}$")
    mixed_case_header_pattern = re.compile(r"^[A-Za-z]+:\s*$")  # Names like "Homer:", "Shakespeare:"
    number_pattern = re.compile(r"^\s*\d+\s*$")  # Detects page numbers (e.g., 1, 2, 3...)
    roman_pattern = re.compile(r"^(?=[MDCLXVI])M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$")  # Roman numerals
    bracketed_number_pattern = re.compile(r"^\{?\s*\d+[-–]?\d*\s*\}?$")

    header_candidates = {}

    for i, page in enumerate(pages):
        lines = page.strip().split("\n")

        # Ignore empty pages
        if not lines:
            continue

        # Track first and last lines for possible headers/footers
        first_idx, last_idx = 0, len(lines) - 1

        final_first_idx = 0
        # Detect multi-line headers (e.g., "THE\nHOMER")
        while first_idx < last_idx:
             current_line = lines[first_idx].strip()

             if not current_line:  # Skip empty lines
                 first_idx += 1
                 continue

             if title_pattern.match(current_line):
                final_first_idx = last_idx

             next_line = lines[first_idx + 1].strip() if first_idx + 1 < len(lines) else ""

             if next_line:
                 if title_pattern.match(next_line):
                     first_idx += 1  # Continue checking next line
                 else:
                     break  # Stop if it's not fully uppercase
             else:
                first_idx += 1
                continue

        final_last_idx = -1
        # Detect multi-line footers (same logic as headers)
        while last_idx > first_idx:
            current_line = lines[last_idx].strip()

            if not current_line:  # Skip empty lines
                last_idx -= 1
                continue

            if title_pattern.match(current_line):
                final_last_idx = last_idx

            prev_line = lines[last_idx - 1].strip() if last_idx - 1 >= 0 else ""

            if prev_line:
                if title_pattern.match(prev_line):
                    last_idx -= 1  # Continue checking previous line
                else:
                    break
            else:
                last_idx -= 1
                continue



        # Store detected header/footer lines
        for line_group in [lines[0:final_first_idx], lines[final_last_idx:-1]]:
            for line in line_group:
                #print(line)
                if not number_pattern.match(line) and not roman_pattern.match(line):
                    #print(line)
                    header_candidates[line] = header_candidates.get(line, 0) + 1

        """
        first_line = lines[0].strip()
        last_line = lines[-1].strip()

        # Detect recurring header/footer candidates
        for line in [first_line, last_line]:
            print(line)
            if line:  # Avoid removing real titles
                header_candidates[line] = header_candidates.get(line, 0) + 1
        """
    recurring_threshold = 3  # If it appears in ~1/3 of pages, it's a recurring header

    # Remove headers appearing frequently
    recurring_headers = {line for line, count in header_candidates.items() if count > recurring_threshold}

    full_text = "\n".join(pages)
    lines = full_text.split("\n")

    cleaned_lines = []
    buffer = ""

    for line in lines:
        #line = line.strip()  # Remove leading/trailing spaces

        if check_page_numbers and (line in recurring_headers or number_pattern.match(line) or roman_pattern.match(line) or mixed_case_header_pattern.match(line) or bracketed_number_pattern.match(line)):
            continue  # Ignore these lines
        #print(line)
        if buffer:
            if line:
                #print(buffer)
                if title_pattern.match(line):
                    continue # we'll delete the pageheader is exists after buffer
                if buffer.endswith(" ") and re.match(r"^[a-z]", line):
                    buffer = buffer.strip()
                    line = buffer + line
                else:
                    line = buffer + " " + line  # Append previous unfinished line
            else:
                continue

        if title_pattern.match(line):
            cleaned_lines.append(line)  # Keep real titles
            continue

        if line.endswith(valid_endings):
            cleaned_lines.append(line)
            buffer = ""  # Reset buffer
        else:
            buffer = line

    if buffer:
        cleaned_lines.append(buffer)

    return "\n\n".join(cleaned_lines)

def split_text_by_titles(text, max_chunk_size=29000):
    """Splits text into logical chunks using detected titles, ensuring chunk size is under max_chunk_size."""
    title_pattern = re.compile(r"^(?![IVXLCDM]+$)[A-Z][A-Z\s,.:'’-]{3,}$")
    valid_endings = (".", "!", "?", '"', "”", "»", "«")

    sections = []
    current_title = "Introduction"  # Default title if none is found at the beginning
    current_chunk = ""

    for line in text.split("\n"):
        if line.strip():
            if title_pattern.match(line.strip()) or not line.endswith(valid_endings):
                if current_chunk and len(current_chunk) >= max_chunk_size:
                    sections.append({"title": current_title, "chunk": current_chunk.strip()})
                    current_title = line.strip()
                    current_chunk = ""
                current_chunk += "\n\n" + line
            else:
                current_chunk += "\n\n" + line

    if current_chunk:
        sections.append({"title": current_title, "chunk": current_chunk.strip()})

    return sections
    
