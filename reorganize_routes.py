with open(r'd:\Desktop\visionai\backend\app\api\applications.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find section boundaries
agg_start = next(i for i, l in enumerate(lines) if '# ==================== AGGREGATION ENDPOINTS' in l)
agg_end = next(i for i, l in enumerate(lines) if '# ==================== TASK MANAGEMENT ENDPOINTS' in l)

# Extract aggregation section
agg_section = lines[agg_start:agg_end]

# Remove from original location
new_lines = lines[:agg_start] + lines[agg_end:]

# Find new position for get_application (it shifted after deletion)
get_app_idx_new = next(i for i, l in enumerate(new_lines) if '@router.get("/{application_id}"' in l)

# Insert aggregation section before get_application
final_lines = new_lines[:get_app_idx_new] + agg_section + new_lines[get_app_idx_new:]

# Write back
with open(r'd:\Desktop\visionai\backend\app\api\applications.py', 'w', encoding='utf-8') as f:
    f.writelines(final_lines)

print('File reorganized successfully')
