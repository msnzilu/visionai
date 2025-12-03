import sys

# Read the file
with open(r'd:\Desktop\visionai\backend\app\models\user.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and replace the PersonalInfo class
new_lines = []
i = 0
while i < len(lines):
    if 'class PersonalInfo(BaseModel):' in lines[i]:
        # Found the class, replace the next few lines
        new_lines.append(lines[i])  # Keep class definition
        i += 1
        
        # Replace first_name
        if 'first_name: str' in lines[i]:
            new_lines.append('    first_name: Optional[str] = ""\n')
            i += 1
        
        # Replace last_name
        if 'last_name: str' in lines[i]:
            new_lines.append('    last_name: Optional[str] = ""\n')
            i += 1
        
        # Keep phone
        if 'phone: Optional[str]' in lines[i]:
            new_lines.append(lines[i])
            i += 1
        
        # Add location and linkedin before address
        new_lines.append('    location: Optional[str] = None  # Added for frontend compatibility\n')
        new_lines.append('    linkedin: Optional[str] = None  # Added for frontend compatibility\n')
        
        # Continue with rest of the class
        while i < len(lines) and not lines[i].strip().startswith('class '):
            new_lines.append(lines[i])
            i += 1
    else:
        new_lines.append(lines[i])
        i += 1

# Write back
with open(r'd:\Desktop\visionai\backend\app\models\user.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Successfully updated PersonalInfo model")
