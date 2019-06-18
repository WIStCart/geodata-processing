@echo off
SET XSLT=r:\scripts\xslt\arcgis2iso.xsl

IF "%1"=="" goto noinput
IF "%2"=="" goto nooutput
echo.
IF EXIST %1 (
    IF EXIST %2 (
        echo Converting all files in %1 to ISO format...
        java -cp r:\scripts\saxon9he.jar net.sf.saxon.Transform -quit:on -warnings:fatal -s:%1 -xsl:%XSLT% -o:%2
        echo Process complete.
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
echo.