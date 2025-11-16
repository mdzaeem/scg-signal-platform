import re
from datetime import datetime

def parse_filename(filename: str):
    """
    Parses complex filenames like: 
    'Artifacts_F4_BBox2_Pink_Operator_Ulf_28.10.2025.csv'
    'Artifacts_F4_BBox2_Orange_Subject_Laura_28.10.2025.csv'
    
    Returns a dictionary with metadata.
    """
    
    # Remove extension and "Artifacts_" prefix
    clean_name = filename.replace(".csv", "").replace("Artifacts_", "")
    
    # Split by underscore
    parts = clean_name.split("_")
    
    # Example: ['F4', 'BBox2', 'Pink', 'Operator', 'Ulf', '28.10.2025']
    
    try:
        metadata = {
            "flight_code": "Unknown",
            "box_name": "Unknown",
            "box_color": "Unknown",
            "role": "Unknown",
            "person_name": "Unknown",
            "file_date": None
        }

        # Dynamically find the date part (DD.MM.YYYY)
        date_str = None
        date_index = -1
        
        # Regex to find the date
        date_pattern = re.compile(r"^\d{2}\.\d{2}\.\d{4}$")
        
        for i, part in enumerate(parts):
            if date_pattern.match(part):
                date_str = part
                date_index = i
                break
        
        if not date_str:
            raise ValueError("Date part (e.g., 28.10.2025) not found in filename.")

        # Parse Date (Format: DD.MM.YYYY)
        metadata["file_date"] = datetime.strptime(date_str, "%d.%m.%Y").date()
        
        # Now extract other parts, assuming a consistent order before the date
        if date_index > 0:
            metadata["flight_code"] = parts[0]
        if date_index > 1:
            metadata["box_name"] = parts[1]
        if date_index > 2:
            metadata["box_color"] = parts[2]
        if date_index > 3:
            metadata["role"] = parts[3]
        if date_index > 4:
            # Join all parts between role and date as the name (e.g., "First Last")
            metadata["person_name"] = " ".join(parts[4:date_index])

        return metadata

    except Exception as e:
        print(f"Error parsing filename '{filename}': {e}")
        # Return default metadata with the error
        metadata["file_name_error"] = str(e)
        return metadata