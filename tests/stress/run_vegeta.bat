@echo off
title Prueba de Carga con Vegeta - Windows
echo.
echo ==============================================================
echo Prueba de carga abierta: 50 req/s por 30s con timeout 30s
echo Servicio: http://localhost:8080/api/v1/extract (multipart/form-data)
echo PDF: pruebas/stress/prueba.pdf
echo ==============================================================
echo.

echo Generando objetivos y atacando con Vegeta...
echo.
set TARGET_FILE=tests\stress\vegeta_targets.txt
set OUTPUT_FILE=tests\stress\results.bin
set RESULTS_CSV=tests\stress\results.csv

:: Ejecutar ataque Vegeta con modelo abierto: 50 req/s por 30s, timeout 30s
cat %TARGET_FILE% | vegeta attack -rate=50 -duration=30s -timeout=30s > %OUTPUT_FILE%

echo.
echo Ejecutando análisis de resultados...
echo.
cat %OUTPUT_FILE% | vegeta results > %RESULTS_CSV%

echo.
echo ==============================================================
echo Resultados de la prueba de carga
echo.
type %RESULTS_CSV%
echo.
echo ==============================================================
echo Guardado en: %RESULTS_CSV%
echo.
pause