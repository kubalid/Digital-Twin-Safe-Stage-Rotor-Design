from dataclasses import dataclass

@dataclass
class MatlabData:
    rotor_speed: float
    angle: float
    # motor_active = bool
    # def __iter__(self):
    #     return iter((self.electromagnetic_torque, self.rotor_speed))

@dataclass
class TiaPortalData:
    manual_auto: bool
    start_stop_manual: bool
    start_stop_auto: bool
    direction: bool
    reset: bool
    home: bool
    angle_set: float
    angle_read: float
    speed_read: float
    speed_auto_rpm: float
    speed_manual_percent: float
    remote_local: bool
    home_mem: bool
    run_manual: bool
    direction_manual: bool
    slider_speed: float
@dataclass
class UnrealData:
    load: float



#Możliwe że unreal jeszcze