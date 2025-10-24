@echo off
REM Crear tareas programadas para ExtractorOV

echo Creando tarea de ejecución masiva (4am diario)...
schtasks /create /tn "ExtractorOV_Massive" /tr "powershell.exe -ExecutionPolicy Bypass -File C:\00_Project_Dev\ExtractorOV_Modular\config\windows_config\run_massive_extraction.ps1" /sc daily /st 04:00 /ru SYSTEM

echo Creando tarea de verificación horaria (cada hora de 4am a 10pm)...
schtasks /create /tn "ExtractorOV_Verification" /tr "powershell.exe -ExecutionPolicy Bypass -File C:\00_Project_Dev\ExtractorOV_Modular\config\windows_config\run_hourly_verification.ps1" /sc hourly /mo 1 /st 04:00 /et 22:00 /ru SYSTEM

echo Tareas programadas creadas exitosamente.
pause
