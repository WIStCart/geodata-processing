@echo off
REM  Script to move completed GBL and ISO files to the appropriate folders.  Esri-format metadata are archived elsewhere, so they are deleted from the ready_for_ingest folder

SET ISO_OUT=\\robbie\web\public\metadata
SET GBL_OUT=r:\archive_project\GeoData_Ingest\archives\gbl
SET ISO_IN=r:\archive_project\GeoData_Ingest\ready_for_ingest\iso
SET GBL_IN=r:\archive_project\GeoData_Ingest\ready_for_ingest\gbl
SET ESRI=r:\archive_project\GeoData_Ingest\ready_for_ingest\esri
SET FOLDER=ingested_%DATE:~10,4%%DATE:~4,2%%DATE:~7,2%

echo.
echo Moving ISO metadata files to Robbie...
move /Y %ISO_IN%\* %ISO_OUT% >nul
echo Process complete.
echo.
echo Moving GBL metadata files to archive...
mkdir %GBL_OUT%\%FOLDER%
move /Y %GBL_IN%\* %GBL_OUT%\%FOLDER% >nul
echo Process complete.     
echo.
rem echo Deleting Esri metadata files...
rem del /Q %ESRI%\*
rem echo Process complete.    