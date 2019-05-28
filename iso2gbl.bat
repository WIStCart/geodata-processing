@echo off
SET XSLT=r:\scripts\xslt\iso2geoBL_uw-geodata.xsl

IF "%1"=="" goto noinput
IF "%2"=="" goto nooutput
echo.
IF EXIST %1 (
    IF EXIST %2 (
        rem how the heck to get saxon to output files with .json extension?!
        echo Converting all files in %1 to GBL format...
        java -cp r:\scripts\saxon9he.jar net.sf.saxon.Transform -quit:on -warnings:fatal -s:%1 -xsl:%XSLT% -o:%2 

        rem this is my simple hack for now
        ren %2\*.xml *.json
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

