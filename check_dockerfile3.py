path = r"C:\OpenCodeProyects\ECCSAWebApps\Dashboard\Dockerfile"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Add a RUN echo with timestamp before COPY . .
old = "COPY . .\nRUN ARG BUILD_ID=dev\nRUN echo \"$BUILD_ID\" > static/build.txt && npm run build"
# Actually let me check the current content
print("Current Dockerfile:")
print(content)
