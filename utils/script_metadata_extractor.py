"""
Script Metadata Extractor
Extracts title, description, and keywords from script content for YouTube uploads
"""

import re
from typing import Dict, Any

def extract_metadata_from_script(script_content: str) -> Dict[str, Any]:
    """
    Extract metadata (title, description, keywords) from script content.
    Handles multiple formats and patterns.
    
    Returns:
        Dict with 'title', 'description', 'keywords' keys
    """
    metadata = {
        'title': '',
        'description': '',
        'keywords': []
    }
    
    if not script_content:
        return metadata
    
    # Normalize script content
    script_content = str(script_content).replace('\r\n', '\n').replace('\r', '\n')
    
    # PRIORITY: Strategy 0 - FIRST look for explicit "Title:" field anywhere in script
    # This is the most reliable method and should be tried BEFORE other strategies
    title_patterns = [
        r'(?:^|\n)\s*(\d+[\.\)])?\s*Title\s*[:：]\s*(.+?)(?:\n|$)',  # "Title:" or "1. Title:"
        r'(?:^|\n)\s*(\d+[\.\)])?\s*Video\s+Title\s*[:：]\s*(.+?)(?:\n|$)',  # "Video Title:"
        r'(?:^|\n)\s*(\d+[\.\)])?\s*YouTube\s+Title\s*[:：]\s*(.+?)(?:\n|$)',  # "YouTube Title:"
        r'Title\s*[:：]\s*([^\n]+)',  # Simple "Title: ..." anywhere
    ]
    
    for pattern in title_patterns:
        title_matches = re.finditer(pattern, script_content, re.IGNORECASE | re.MULTILINE)
        for match in title_matches:
            # Get title text - try different groups
            title_text = None
            if match.lastindex:
                title_text = match.group(match.lastindex)
            elif len(match.groups()) >= 2:
                # Usually the last group is the title
                title_text = match.group(len(match.groups()))
            else:
                title_text = match.group(1) if match.groups() else None
            
            if title_text:
                title_text = title_text.strip().strip('"').strip("'").strip()
                # Clean up - remove any "Title:" prefix that might remain
                title_text = re.sub(r'^(Title|Video Title|YouTube Title)\s*[:：]\s*', '', title_text, flags=re.IGNORECASE).strip()
                # Remove numbering if present at start
                title_text = re.sub(r'^\d+[\.\)]\s*', '', title_text).strip()
                
                # Validate: title should be meaningful (5+ chars)
                if title_text and len(title_text) >= 5:
                    # Reject common invalid patterns (category names, placeholders, script numbers)
                    invalid_patterns = [
                        r'^\d+\s+(Common\s+Mistake|Pro\s+Tip|Myth[- ]?Busting|Mini\s+Makeover|How[- ]?To)',
                        r'^(Common\s+Mistake|Pro\s+Tip|Myth[- ]?Busting|Mini\s+Makeover|How[- ]?To)$',
                        r'^Number\s*\+\s*Category$',
                        r'^\d+$',  # Just a number
                    ]
                    
                    is_invalid = False
                    for invalid_pattern in invalid_patterns:
                        if re.match(invalid_pattern, title_text, re.IGNORECASE):
                            is_invalid = True
                            break
                    
                    if not is_invalid:
                        metadata['title'] = title_text
                        print(f"[DEBUG] ✅ extract_metadata_from_script: Found title via explicit Title: field: '{title_text}'")
                        break
        
        if metadata.get('title'):
            break
    
    # Try multiple extraction strategies
    # Strategy 1: Look for structured sections with headers (if title not found yet)
    if not metadata.get('title'):
        metadata = extract_structured_sections(script_content, metadata)
    
    # Strategy 2: If title not found, look for title-like patterns in first lines
    if not metadata.get('title'):
        metadata = extract_title_from_start(script_content, metadata)
    
    # Strategy 3: Look for description in early sections
    if not metadata.get('description'):
        metadata = extract_description_patterns(script_content, metadata)
    
    # Strategy 4: Look for keywords/hashtags anywhere in the script
    if not metadata.get('keywords'):
        metadata = extract_keywords_patterns(script_content, metadata)
    
    # Clean up metadata - ensure strings are properly formatted
    if metadata.get('title'):
        metadata['title'] = str(metadata['title']).strip().strip('"').strip("'").strip()
        # Remove extra whitespace
        metadata['title'] = ' '.join(metadata['title'].split())
        
        # Final validation: reject if title is too short or matches invalid patterns
        title_lower = metadata['title'].lower()
        invalid_short_titles = ['common mistake', 'pro tip', 'myth-busting', 'mini makeover', 'how-to', 'how to']
        if len(metadata['title']) < 5 or (len(metadata['title']) < 20 and title_lower in invalid_short_titles):
            # Title is invalid - clear it
            print(f"[DEBUG] ❌ Rejected invalid title in cleanup: '{metadata['title']}' (too short or matches category)")
            metadata['title'] = ''
    
    if metadata.get('description'):
        metadata['description'] = str(metadata['description']).strip().strip('"').strip("'").strip()
        # Remove extra whitespace but preserve line breaks in longer descriptions
        if len(metadata['description']) > 100:
            # For longer descriptions, preserve some structure
            metadata['description'] = ' '.join(metadata['description'].split())
        else:
            metadata['description'] = ' '.join(metadata['description'].split())
    
    # Ensure keywords is a list
    if metadata.get('keywords'):
        if isinstance(metadata['keywords'], str):
            # If it's a string, parse it
            metadata['keywords'] = parse_keywords(metadata['keywords'])
        elif not isinstance(metadata['keywords'], list):
            metadata['keywords'] = []
    else:
        metadata['keywords'] = []
    
    # Debug output
    title_preview = metadata.get('title', 'NOT FOUND')
    desc_preview = metadata.get('description', 'NOT FOUND')
    keywords_preview = metadata.get('keywords', [])
    
    print(f"[DEBUG] Final extracted metadata:")
    print(f"  Title: '{title_preview}' (length: {len(str(title_preview))})")
    print(f"  Description: '{desc_preview[:100]}...' (length: {len(str(desc_preview))})")
    print(f"  Keywords: {keywords_preview} (count: {len(keywords_preview) if isinstance(keywords_preview, list) else 0})")
    
    return metadata

def extract_structured_sections(script_content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Extract metadata from structured sections with clear headers"""
    lines = script_content.split('\n')
    current_section = None
    section_content = []
    
    # Track if we've found title, description, keywords
    title_found = False
    desc_found = False
    keywords_found = False
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped:
            # Empty line might end a section, but continue collecting if in a section
            if current_section:
                section_content.append("")  # Preserve empty lines in section
            continue
        
        # Skip lines that are clearly section markers or headers
        if re.match(r'^[-=*]{3,}$', line_stripped):  # Separator lines
            if current_section and section_content:
                save_section_content(metadata, current_section, section_content)
            current_section = None
            section_content = []
            continue
        
        # Title patterns - very flexible, must come first
        # IMPORTANT: Skip category names - they should not be extracted as titles
        if not title_found:
            # First, check if this line is likely a category name (short, matches common category patterns)
            # Category names are usually short and don't have colons
            is_likely_category = False
            if len(line_stripped) < 30 and not (':' in line_stripped or '：' in line_stripped):
                # Check if it matches common category patterns
                category_patterns = [
                    r'^(How[- ]?To|How To|How-to)$',
                    r'^(Common\s+Mistake|Common\s+Mistakes)$',
                    r'^(Pro\s+Tip|Pro\s+Tips)$',
                    r'^(Myth[- ]?Busting|Myth\s+Busting)$',
                    r'^(Mini\s+Makeover|Mini\s+Makeovers)$',
                ]
                for cat_pattern in category_patterns:
                    if re.match(cat_pattern, line_stripped, re.IGNORECASE):
                        is_likely_category = True
                        break
            
            # Skip category names - don't extract them as titles
            if is_likely_category:
                continue
            
            title_patterns = [
                r'^(\d+[\.\)]?\s*)?Title\s*[:：]\s*(.+)$',  # "Title:", "1. Title:", "Title："
                r'^(\d+[\.\)]?\s*)?Video\s+Title\s*[:：]\s*(.+)$',
                r'^(\d+[\.\)]?\s*)?YouTube\s+Title\s*[:：]\s*(.+)$',
                r'^Title\s*[:：]\s*(.+)$',  # Just "Title:" followed by content
                r'^#+\s*Title\s*[:：]?\s*(.+)$',  # Markdown style
            ]
            
            for pattern in title_patterns:
                match = re.match(pattern, line_stripped, re.IGNORECASE)
                if match:
                    # Get title from match group
                    title_text = match.group(match.lastindex) if match.lastindex else (match.group(2) if len(match.groups()) >= 2 else match.group(1))
                    if title_text:
                        title_text = title_text.strip().strip('"').strip("'").strip()
                        # Clean up title - remove common prefixes
                        title_text = re.sub(r'^(Title|Video Title|YouTube Title)\s*[:：]\s*', '', title_text, flags=re.IGNORECASE).strip()
                        # Make sure it's not a category name
                        if title_text and len(title_text) > 3 and not is_likely_category:  # Minimum length
                            metadata['title'] = title_text
                            title_found = True
                            current_section = 'title'
                            section_content = []
                            # Check if there's more content on the same line after colon
                            if ':' in line_stripped or '：' in line_stripped:
                                # Title might continue on next lines, so continue to next line
                                continue
                            break
        
        # Description patterns
        if not desc_found:
            desc_patterns = [
                r'^(\d+[\.\)]?\s*)?(Short\s+)?Description\s*[:：]\s*(.+)$',
                r'^(\d+[\.\)]?\s*)?Caption\s*[:：]\s*(.+)$',
                r'^(\d+[\.\)]?\s*)?Summary\s*[:：]\s*(.+)$',
                r'^(Short\s+)?Description\s*[:：]\s*(.+)$',
                r'^#+\s*Description\s*[:：]?\s*(.+)$',
            ]
            
            for pattern in desc_patterns:
                match = re.match(pattern, line_stripped, re.IGNORECASE)
                if match:
                    desc_text = match.group(match.lastindex) if match.lastindex else (match.group(3) if len(match.groups()) >= 3 else match.group(1))
                    if desc_text:
                        desc_text = desc_text.strip().strip('"').strip("'").strip()
                        # Clean up description
                        desc_text = re.sub(r'^(Description|Short Description|Caption|Summary)\s*[:：]\s*', '', desc_text, flags=re.IGNORECASE).strip()
                        if desc_text and len(desc_text) > 5:
                            metadata['description'] = desc_text
                            desc_found = True
                            current_section = 'description'
                            section_content = []
                            # Continue to collect multi-line descriptions
                            if ':' in line_stripped or '：' in line_stripped:
                                continue
                            break
        
        # Keywords patterns - look more carefully for keywords
        if not keywords_found:
            keyword_patterns = [
                r'^(\d+[\.\)]?\s*)?(Keyword|Keywords|Hashtag|Hashtags)\s*(Selection)?\s*[:：]\s*(.+)$',
                r'^(\d+[\.\)]?\s*)?Tags?\s*[:：]\s*(.+)$',
                r'^(Keyword|Keywords|Hashtag|Hashtags)\s*(Selection)?\s*[:：]\s*(.+)$',
                r'^#+\s*Keywords?\s*[:：]?\s*(.+)$',
            ]
            
            for pattern in keyword_patterns:
                match = re.match(pattern, line_stripped, re.IGNORECASE)
                if match:
                    # Get keywords text - try different groups
                    keywords_text = None
                    if match.lastindex:
                        keywords_text = match.group(match.lastindex)
                    elif len(match.groups()) >= 4:
                        # For patterns with 4 groups, the last one is usually the keywords
                        keywords_text = match.group(4)
                    elif len(match.groups()) >= 3:
                        # For patterns with 3 groups, check which one is the keywords
                        if match.group(3) and match.group(3).lower() not in ['keyword', 'keywords', 'hashtag', 'hashtags', 'selection', 'tags']:
                            keywords_text = match.group(3)
                        else:
                            keywords_text = match.group(2) if match.group(2) and match.group(2).lower() not in ['keyword', 'keywords', 'hashtag', 'hashtags', 'selection'] else match.group(1)
                    elif len(match.groups()) >= 2:
                        keywords_text = match.group(2) if match.group(2) and not match.group(2).lower() in ['keyword', 'keywords', 'hashtag', 'hashtags', 'selection'] else match.group(1)
                    else:
                        keywords_text = match.group(1)
                    
                    if keywords_text:
                        keywords_text = keywords_text.strip().strip('"').strip("'").strip()
                        # Clean up keywords text - remove instruction phrases
                        keywords_text = re.sub(r'^(Keyword|Keywords|Hashtag|Hashtags|Tags?)\s*(Selection)?\s*[:：]\s*', '', keywords_text, flags=re.IGNORECASE).strip()
                        # Remove instruction text like "SELECTION (MUST INCL..."
                        keywords_text = re.sub(r'SELECTION\s*\([^)]*\)', '', keywords_text, flags=re.IGNORECASE).strip()
                        keywords_text = re.sub(r'\(MUST INCL[^)]*\)', '', keywords_text, flags=re.IGNORECASE).strip()
                        
                        if keywords_text:  # Only parse if there's actual content after cleaning
                            keywords = parse_keywords(keywords_text)
                            if keywords:
                                metadata['keywords'] = keywords
                                keywords_found = True
                                current_section = 'keywords'
                                section_content = []
                                break
        
        # If we're in a section, collect content
        if current_section == 'title' and not title_found:
            # Collect title content until we hit another section
            if not re.match(r'^\d+[\.\)]', line_stripped) and not re.match(r'^(Description|Caption|Keyword|Script|HeyGen|Avatar)', line_stripped, re.IGNORECASE):
                if line_stripped and len(line_stripped) < 200:  # Reasonable title length
                    section_content.append(line_stripped)
                else:
                    # Too long, probably not title content
                    if section_content:
                        save_section_content(metadata, 'title', section_content)
                        title_found = True
                    current_section = None
                    section_content = []
            else:
                # Hit a new section, save title
                if section_content:
                    save_section_content(metadata, 'title', section_content)
                    title_found = True
                current_section = None
                section_content = []
        elif current_section == 'description' and not desc_found:
            # Collect description content
            if not re.match(r'^\d+[\.\)]', line_stripped) and not re.match(r'^(Keyword|Script|HeyGen|Avatar|Title)', line_stripped, re.IGNORECASE):
                section_content.append(line_stripped)
            else:
                # Hit a new section, save description
                if section_content:
                    save_section_content(metadata, 'description', section_content)
                    desc_found = True
                current_section = None
                section_content = []
        elif current_section == 'keywords' and not keywords_found:
            # Collect keywords content - continue until we hit a new section
            if not re.match(r'^\d+[\.\)]', line_stripped) and not re.match(r'^(Script|HeyGen|Avatar|Title|Description|Short Description)', line_stripped, re.IGNORECASE):
                # Continue collecting keywords
                section_content.append(line_stripped)
            else:
                # Hit a new section, save keywords
                if section_content:
                    # Join all collected lines and parse
                    keywords_text = ' '.join(section_content).strip()
                    # Clean up instruction text
                    keywords_text = re.sub(r'SELECTION\s*\([^)]*\)', '', keywords_text, flags=re.IGNORECASE).strip()
                    keywords_text = re.sub(r'\(MUST INCL[^)]*\)', '', keywords_text, flags=re.IGNORECASE).strip()
                    if keywords_text:
                        keywords = parse_keywords(keywords_text)
                        if keywords:
                            metadata['keywords'] = keywords
                            keywords_found = True
                current_section = None
                section_content = []
        else:
            # Not in a known section, check if this starts a new section
            if re.match(r'^\d+[\.\)]', line_stripped):
                # New numbered section
                if current_section and section_content:
                    save_section_content(metadata, current_section, section_content)
                current_section = None
                section_content = []
    
    # Save last section
    if current_section and section_content:
        if current_section == 'keywords':
            # For keywords, join and parse directly
            keywords_text = ' '.join(section_content).strip()
            # Clean up instruction text
            keywords_text = re.sub(r'SELECTION\s*\([^)]*\)', '', keywords_text, flags=re.IGNORECASE).strip()
            keywords_text = re.sub(r'\(MUST INCL[^)]*\)', '', keywords_text, flags=re.IGNORECASE).strip()
            if keywords_text:
                keywords = parse_keywords(keywords_text)
                if keywords:
                    metadata['keywords'] = keywords
                    keywords_found = True
        else:
            save_section_content(metadata, current_section, section_content)
            if current_section == 'title':
                title_found = True
            elif current_section == 'description':
                desc_found = True
    
    return metadata

def extract_title_from_start(script_content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Extract title from the beginning of the script if not found in structured sections"""
    lines = script_content.split('\n')
    
    # Look at first 10 lines for a title-like pattern
    for i, line in enumerate(lines[:10]):
        line_stripped = line.strip()
        if not line_stripped:
            continue
        
        # Skip if it's clearly a header or section marker
        if re.match(r'^(\d+[\.\)]|#+|[-=*]{3,})', line_stripped):
            continue
        
        # Look for title-like content (short, capitalized, no special markers)
        if 10 < len(line_stripped) < 100:
            # Check if it looks like a title (has some capitalization, not all caps)
            words = line_stripped.split()
            if len(words) >= 3 and len(words) <= 15:
                # Has reasonable word count
                if not any(skip_word in line_stripped.lower() for skip_word in 
                          ['script', 'video', 'description', 'keyword', 'caption', 'heygen', 'avatar', 'setup']):
                    metadata['title'] = line_stripped
                    break
    
    return metadata

def extract_description_patterns(script_content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Extract description using various patterns"""
    lines = script_content.split('\n')
    
    # Look for description in first 30 lines
    description_lines = []
    in_description_section = False
    
    for i, line in enumerate(lines[:30]):
        line_stripped = line.strip()
        if not line_stripped:
            continue
        
        # Check for description section markers
        if re.search(r'(description|caption|summary|overview)', line_stripped, re.IGNORECASE):
            in_description_section = True
            # Try to extract from this line
            match = re.search(r'[:：]\s*(.+)$', line_stripped)
            if match:
                desc_text = match.group(1).strip()
                if desc_text and len(desc_text) > 10:
                    description_lines.append(desc_text)
            continue
        
        if in_description_section:
            # Collect description lines until we hit another section
            if re.match(r'^\d+[\.\)]', line_stripped) or re.match(r'^[A-Z][A-Z\s]+:?$', line_stripped):
                break
            if len(line_stripped) > 10:
                description_lines.append(line_stripped)
    
    if description_lines:
        metadata['description'] = ' '.join(description_lines[:3])  # Join first 3 lines
        metadata['description'] = metadata['description'][:300]  # Limit to 300 chars
    
    return metadata

def extract_keywords_patterns(script_content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Extract keywords/hashtags from anywhere in the script"""
    # Find all hashtags
    hashtags = re.findall(r'#(\w+)', script_content)
    if hashtags:
        metadata['keywords'] = list(set(hashtags[:10]))  # Remove duplicates, limit to 10
        return metadata
    
    # Look for keyword section
    keyword_section_patterns = [
        r'(?:Keyword|Keywords|Hashtag|Hashtags|Tags?)[\s:：]+(.+?)(?:\n\n|\n\d+\.|$)',
        r'Keywords?[\s:：]+([^\n]+)',
    ]
    
    for pattern in keyword_section_patterns:
        matches = re.finditer(pattern, script_content, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            keywords_text = match.group(1).strip()
            if keywords_text:
                keywords = parse_keywords(keywords_text)
                if keywords:
                    metadata['keywords'] = keywords
                    return metadata
    
    return metadata

def save_section_content(metadata: Dict[str, Any], section: str, lines: list):
    """Save collected lines to the appropriate metadata field"""
    # Join lines, but preserve meaningful structure
    text_lines = [line.strip() for line in lines if line.strip()]
    text = ' '.join(text_lines).strip().strip('"').strip("'")
    
    if not text:
        return
    
    if section == 'title':
        # For title, take first meaningful line or join if short
        if text_lines:
            title_text = text_lines[0]
            # Clean up title - remove common prefixes and suffixes
            title_text = re.sub(r'^(Title|Video Title|YouTube Title)\s*[:：]\s*', '', title_text, flags=re.IGNORECASE).strip()
            title_text = re.sub(r'\s*[:：]\s*$', '', title_text).strip()
            if title_text and len(title_text) > 3:
                # Only update if we don't have a title or this one is better
                if not metadata.get('title') or (len(title_text) > len(metadata.get('title', '')) and len(title_text) < 150):
                    metadata['title'] = title_text
    elif section == 'caption' and not metadata.get('description'):
        # Caption can be used as description
        desc_text = text[:500]  # Limit to 500 chars
        metadata['description'] = desc_text
    elif section == 'description':
        # For description, join all lines but limit length
        desc_text = text[:500]  # Limit to 500 chars for description
        # Only update if we don't have one or this one is longer/better
        if not metadata.get('description') or len(desc_text) > len(metadata.get('description', '')):
            metadata['description'] = desc_text
    elif section == 'keywords':
        keywords = parse_keywords(text)
        if keywords:
            metadata['keywords'] = keywords

def parse_keywords(keywords_text: str) -> list:
    """Parse keywords from text (handles comma-separated, hashtags, etc.)"""
    if not keywords_text:
        return []
    
    # Clean up the keywords text first
    keywords_text = keywords_text.strip()
    
    # Remove common prefixes
    keywords_text = re.sub(r'^(Keyword|Keywords|Hashtag|Hashtags|Tags?)\s*(Selection)?\s*[:：]\s*', '', keywords_text, flags=re.IGNORECASE).strip()
    
    # Remove phrases like "SELECTION (MUST INCL..." which are instructions, not keywords
    keywords_text = re.sub(r'SELECTION\s*\([^)]*\)', '', keywords_text, flags=re.IGNORECASE).strip()
    keywords_text = re.sub(r'\(MUST INCL[^)]*\)', '', keywords_text, flags=re.IGNORECASE).strip()
    keywords_text = re.sub(r'MUST INCL[^,;]*', '', keywords_text, flags=re.IGNORECASE).strip()
    
    if not keywords_text:
        return []
    
    keywords = []
    
    # Extract hashtags first (e.g., #keyword1 #keyword2)
    hashtags = re.findall(r'#(\w+)', keywords_text)
    for hashtag in hashtags:
        if hashtag and hashtag.lower() not in [k.lower() for k in keywords]:
            keywords.append(hashtag)
    
    # Remove hashtags from text for further processing
    keywords_text_no_hashtags = re.sub(r'#\w+', '', keywords_text).strip()
    
    # Split by common delimiters (comma, semicolon, newline, pipe)
    parts = re.split(r'[,;\n|]', keywords_text_no_hashtags)
    for part in parts:
        part = part.strip().strip('"').strip("'").strip()
        # Skip empty parts and instruction text
        if part and len(part) > 1:
            # Skip if it looks like an instruction
            if not any(instruction in part.upper() for instruction in ['SELECTION', 'MUST INCL', 'REQUIRED', 'INCLUDE']):
                # Clean up the keyword
                part = re.sub(r'^[-•*]\s*', '', part).strip()  # Remove bullet points
                if part and part.lower() not in [k.lower() for k in keywords]:
                    keywords.append(part)
    
    # Limit to 15 keywords and return as comma-separated string for display
    return keywords[:15]

