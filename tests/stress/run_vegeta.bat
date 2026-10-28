@echo off
title Prueba de Carga con Vegeta - Windows

set TARGET_FILE=tests\stress\vegeta_targets.txt
set OUTPUT_FILE=tests\stress\results.bin

:: Ejecutar ataque Vegeta: 50 req/s, 30s, timeout 30s
vegeta attack -targets=%TARGET_FILE% -rate=50 -duration=30s -timeout=30s -insecure -output=%OUTPUT_FILE%

:: Generar reporte
vegeta report %OUTPUT_FILE%
