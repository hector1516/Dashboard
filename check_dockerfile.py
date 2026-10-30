path = r"C:\OpenCodeProyects\ECCSAWebApps\Dashboard\Dockerfile"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()
print("Has build.txt:", "build.txt" in content)
print("Has BUILD_ID:", "BUILD_ID" in content)
print("Has npm run build:", "npm run build" in content)
