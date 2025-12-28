from dataclasses import dataclass


@dataclass
class Keys:
    BESSKEY = "bess"
    PVKEY = "Pv"
    GENSETKEY = "genset"
    TEMPERATURE_BESS_KEY = "temperature_bess"
    IRRADIANCE_KEY = "irradiance"
    BESS_SETPOINT_KEY = "bess_setpoint"
    PV_SETPOINT_KEY = "pv_setpoint"
    WATCHDOG_BESS_KEY = "watchdog_bess"
