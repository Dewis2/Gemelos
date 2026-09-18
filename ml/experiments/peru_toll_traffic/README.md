# Experimento de tráfico de peajes del Perú

Experimento independiente para predecir el total vehicular del siguiente mes por
unidad de peaje. Usa exclusivamente el CSV oficial del MTC, variables temporales,
identificador de ubicación, rezagos y media móvil derivados de observaciones reales.

La división es temporal. Se comparan el baseline `y(t+1)=y(t)`, regresión lineal y
Random Forest mediante MAE, RMSE y R². MAPE solo se calcula si el conjunto de prueba
no contiene ceros.

```powershell
.venv\Scripts\python.exe ml\experiments\peru_toll_traffic\train.py
```

> Modelo experimental entrenado con datos nacionales de peaje. No es un modelo
> predictivo de la Av. Ferrocarril ni una validación local de Huancayo.
