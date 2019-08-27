@echo off
REM  Script to convert Esri-format metadata to GBL records via XSLT

SET ISO_XSLT=r:\scripts\xslt\arcgis2iso.xsl
SET GBL_XSLT=r:\scripts\xslt\iso2gbl.xsl
SET ESRI=r:\archive_project\GeoData_Ingest\ready_for_ingest\esri
SET ISO=r:\archive_project\GeoData_Ingest\ready_for_ingest\iso
SET GBL=r:\archive_project\GeoData_Ingest\ready_for_ingest\gbl

echo.
echo Converting all files in %ESRI% to ISO format...
java -cp r:\scripts\saxon9he.jar net.sf.saxon.Transform -quit:on -warnings:fatal -s:%ESRI% -xsl:%ISO_XSLT% -o:%ISO%
echo Process complete.
echo.
rem how the heck to get saxon to output files with .json extension?!
echo Converting all files in %ISO% to GBL format...
java -cp r:\scripts\saxon9he.jar net.sf.saxon.Transform -quit:on -warnings:fatal -s:%ISO% -xsl:%GBL_XSLT% -o:%GBL% 
rem this is my simple hack for renaming xml to json
for %%x IN (%GBL%\*.xml) do move /Y %%x %GBL%\%%~nx.json >nul
echo Process complete.     
