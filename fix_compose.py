import re

FILE_PATH = r"g:\Desktop\visionai\docker-compose.swarm.yml"

with open(FILE_PATH, "r") as f:
    content = f.read()

# Replace Unencoded Password with Encoded Password Globally
# Target: HxHxHz@#@2030 -> HxHxHz%40%23%402030
new_content = content.replace("HxHxHz@#@2030", "HxHxHz%40%23%402030")

with open(FILE_PATH, "w") as f:
    f.write(new_content)

print("Fixed MONGODB_URL encoding in docker-compose.swarm.yml.")
