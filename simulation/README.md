# Integración SUMO / TraCI

La integración está preparada mediante `SumoTrafficSimulator`, pero la red del
corredor no se incluye: primero debe validarse la geometría, carriles, conexiones,
semáforos y demanda. SUMO se mantiene fuera del contenedor inicial para evitar
acoplar la PoC a una instalación pesada y no validada.

Para habilitarlo, instale SUMO, exponga `SUMO_HOME/tools` en `PYTHONPATH`, cree una
configuración `.sumocfg` basada en cartografía validada y referénciela como
`sumo_config` en el escenario. La ausencia de TraCI o del archivo produce un error
controlado. `FakeTrafficSimulator` se usa exclusivamente en pruebas y desarrollo.

