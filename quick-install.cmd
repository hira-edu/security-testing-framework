@echo off
:: Quick installer for Security Testing Framework
:: This file makes it easy to download and run the installer

echo Downloading Security Testing Framework installer...
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/hira-edu/security-testing-framework/main/install.bat' -OutFile '%TEMP%\stf-install.bat' -UseBasicParsing; & '%TEMP%\stf-install.bat'}"