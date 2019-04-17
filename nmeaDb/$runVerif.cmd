@rem @set pyBin=C:\CAT_dskD\myTools\Python\Python36\python.exe
@set pyBin=D:\myTools\Python\Python36\python.exe
@rem @set appHome=C:\RepoGit\nmeaDB\nmeaDb
@set appHome=D:\RepoS\nmeaDB\nmeaDb

@rem  VHF_20151215.nmea contient des $GPRMC non conformes !
@rem @set nmeaFile=VHF_20151215.nmea

@set nmeaFile=
@set nmeaFile=AISSinagot.nmea
@set nmeaFile=Calibration01.nmea
@set nmeaFile=Garmin152h.nmea
@set nmeaFile=Nav_20180601.nmea
@rem @set nmeaFile=NkeLauBen.nmea
@rem @set nmeaFile=opcn-20170911-082000.nmea
@rem @set nmeaFile=opcn-20170911-164500.nmea
@rem @set nmeaFile=opcn-20170912-081000.nmea
@rem @set nmeaFile=opcn-20170912-184500.nmea
@rem @set nmeaFile=opcn-20170913-081500.nmea
@rem @set nmeaFile=opcn-20170913-163000.nmea
@rem @set nmeaFile=Sortie_20170922-01.nmea
@rem @set nmeaFile=Sortie_20170922-02.nmea
@rem @set nmeaFile=opcn-20170911-164500.nmea

@rem nmeaDB_ExamineDateheureRmcZda.py
@rem nmeaDB_ExamineDateheureRmcZda.py
@rem nmeaDB_RotateNmeaFile.py
@rem 

REM pushd %appHome%\datas
REM for %%f in (*.nmea) do echo %%f
REM popd

REM pause

%pyBin% ^
	%appHome%\nmeaDB_verifNmeaFile.py ^
	%appHome%\datas\%nmeaFile% ^
	IIZDA ^
	GPRMC ^
	1> %appHome%\doc_dev\%nmeaFile%.infos ^
	2> %appHome%\%nmeaFile%.log



@rem pushd %appHome%\datas
@rem for %%f in (*.nmea) do %pyBin% %appHome%\nmeaDB_verifNmeaFile.py %appHome%\datas\%%f IIZDA 1> %appHome%\doc_dev\%%f.infos 2> %appHome%\%%f.log
@rem popd


	