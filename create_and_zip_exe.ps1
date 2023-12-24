# Activate the virtual environment
& ".\venv\Scripts\Activate"

# Execute pyinstaller
pyinstaller --onefile main.py

# Deactivate the virtual environment
deactivate

# Set the paths
$distPath = ".\dist"
$destinationDir = "lethal-company-mod-updater"
$zipFileName = "lethal-company-mod-updater.zip"
$exeFileName = "run-mod-updater.exe"

# Delete existing zip file
Remove-Item -Path $zipFileName -Force -ErrorAction SilentlyContinue

# Create a new directory
New-Item -ItemType Directory -Path $destinationDir -Force

# Copy main.exe and config.py to the destination directory
Copy-Item -Path "$distPath\main.exe" -Destination "$destinationDir\$exeFileName" -Force
Copy-Item -Path ".\main.py" -Destination "$destinationDir\main.py" -Force
Copy-Item -Path ".\config.py" -Destination "$destinationDir\config.py" -Force
Copy-Item -Path ".\readme.txt" -Destination "$destinationDir\readme.txt" -Force

# Create a zip file
Compress-Archive -Path $destinationDir -DestinationPath $zipFileName -Force

# Delete pyinstaller build files and zipped directory
Remove-Item -Path ".\dist\" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path ".\build\" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path ".\main.spec" -Force -ErrorAction SilentlyContinue
Remove-Item -Path $destinationDir -Recurse -Force -ErrorAction SilentlyContinue
