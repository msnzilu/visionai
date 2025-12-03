import sys

# Read the file
with open(r'd:\Desktop\visionai\frontend\pages\profile.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace empty userEmail
content = content.replace(
    '<p class="text-sm text-gray-500" id="userEmail"></p>',
    '<p class="text-sm text-gray-500" id="userEmail">email@example.com</p>'
)

# Replace empty subscriptionBadge
content = content.replace(
    'id="subscriptionBadge"></span>',
    'id="subscriptionBadge">Free</span>'
)

# Write back
with open(r'd:\Desktop\visionai\frontend\pages\profile.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Successfully updated profile.html placeholders")
