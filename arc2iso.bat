@echo off
set LOGFILE=%2\log.txt
IF EXIST %LOGFILE% del %LOGFILE%
IF "%1"=="" goto noinput
IF "%2"=="" goto nooutput

IF EXIST %1 (
    IF EXIST %2 (
        echo Converting files in %1 to ISO format...
        java -cp r:\scripts\saxon9he.jar net.sf.saxon.Transform -quit:on -warnings:fatal -s:%1 -xsl:r:\scripts\xslt\ArcGIS2ISO19139_uw-geodata.xsl -o:%2 
        goto done
    ) ELSE (
        echo ERROR: output folder does not exist
        goto done
    )
) ELSE (
    echo ERROR: input folder does not exist
    goto done
)

:noinput
echo ERROR: No input folder specified
goto done

:nooutput
echo ERROR: No output folder specified
goto done

:done