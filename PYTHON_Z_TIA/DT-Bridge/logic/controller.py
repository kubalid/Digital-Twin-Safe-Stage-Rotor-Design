import socket
from traceback import print_tb
from typing import dataclass_transform

import config
import time
import matplotlib.pyplot as plt
import numpy as np
import threading
import math

from drivers.matlab_driver import MatlabUDP_RC_SND
from drivers.unreal_driver import UnrealUDPClient
from drivers.tia_portal_driver import TiaPortal_RC_SND


class SystemController:
    def __init__(self):
        self.matlab = MatlabUDP_RC_SND()
        self.tia_portal_rc = TiaPortal_RC_SND()
        self.tia_portal_snd = TiaPortal_RC_SND()
        self.unreal_snd = UnrealUDPClient()
        self.unreal_rcv = UnrealUDPClient()

        self.data_lock = threading.Lock()
        self.running = False
        self.matlab_connected = False
        self.tia_connected_rc = False
        self.tia_connected_snd = False
        self.unreal_connected = False

        #=====tia portal zmienne=====
        self.target_rpm = 0
        self.target_angle = 0
        self.direction = False
        self.auto_manual = False
        self.stop_start = False
        self.home = False
        self.start_stop_manual = False
        self.start_stop_auto = False
        self.reset = False
        self.angle_read_scada = 0.0
        self.speed_read = 0.0
        self.speed_auto_rpm = 0.0
        self.speed_manual_percent = 0.0
        self.remote_local = False
        self.home_mem = False
        self.run_manual = False
        self.direction_manual = False
        self.slider_speed = 0.0
        # self.activator_tia = False
        # self.breakdown_tia = False
        # self.rotate_tia = False
        # self.previous_rotate = False
        # self.working_condition = 0
        # self.breakdown_signaling = False
        # self.alarm_confirmation = False

        #=====matlab zmienne=====
        self.current_rpm = 0
        self.current_angle = 0


        #=====unreal zmienne=====
        self.load = 0.0
        self.object_diameter = 0.0
        self.distance_between_centers = 0.0

        # =====Wykresy=====
        self.dt = 1e-5
        self.torque_history = []
        self.rpm_history = []
        self.sample_counter = 0
        self.time_history = []

    def _tia_worker_rc(self):
        while self.running:
            try:
                if not self.tia_connected_rc:
                    if self.tia_portal_rc.connect():
                        self.tia_connected_rc = True
                    else:
                        time.sleep(1)
                        continue
                else:
                    data = self.tia_portal_rc.read_db()
                    with self.data_lock:
                        self.auto_manual = data.manual_auto
                        self.start_stop_manual = data.start_stop_manual
                        self.start_stop_auto = data.start_stop_auto
                        self.direction = data.direction
                        self.reset = data.reset
                        self.home = data.home
                        self.target_angle = data.angle_set
                        self.angle_read = data.angle_read
                        self.speed_read = data.speed_read
                        self.speed_auto_rpm = data.speed_auto_rpm
                        self.speed_manual_percent = data.speed_manual_percent
                        self.remote_local = data.remote_local
                        self.home_mem = data.home_mem
                        self.run_manual = data.run_manual
                        self.direction_manual = data.direction_manual
                        self.slider_speed = data.slider_speed

                    print(
                    f"auto_manual: {self.auto_manual} \n"
                    f"start_stop_manual: {self.start_stop_manual} \n"
                    f"start_stop_auto: {self.start_stop_auto} \n"
                    f"direction: {self.direction} \n"
                    f"reset: {self.reset} \n"
                    f"target_angle: {self.target_angle} \n"
                    f"angle_read: {self.angle_read} \n"
                    f"SPEED_READ: {self.speed_read} \n"
                    f"speed_RPM: {self.speed_auto_rpm} \n"
                    f"speed%: {self.speed_manual_percent} \n"
                    
                    f"remote_local: {self.remote_local} \n"
                    f"home_mem: {self.home_mem} \n"
                    f"run_manual: {self.run_manual} \n"
                    f"direction_manual%: {self.direction_manual} \n"
                    f"slider_speed%: {self.slider_speed} \n"
                    f"==================================================")
            except Exception as e:
                print(f"[TIA read Error] utrata połączenia: {e}")
                self.tia_connected_rc = False
            time.sleep(0.1)



    def _tia_worker_snd(self):
        while self.running:
            try:
                if not self.tia_connected_snd:
                    if self.tia_portal_snd.connect():
                        self.tia_connected_snd = True
                    else:
                        time.sleep(1)
                        continue
                else:
                    with self.data_lock:
                        rpm_to_send = self.current_rpm
                        rotate_temp = self.rotate_tia
                        current_load = self.load
                        working_condition = self.working_condition
                    if rotate_temp and working_condition != 7:
                        rpm_to_send = rpm_to_send * -1
                    self.tia_portal_snd.write_db(round(rpm_to_send,1),current_load)

            except Exception as e:
                print(f"[TIA snd Error] utrata połączenia: {e}")
                self.tia_connected_snd = False
                time.sleep(1)
            time.sleep(0.01)


    def _matlab_worker(self):
        zero_rpm = 0.0
        while self.running:
            try:
                if not self.matlab_connected:
                    if self.matlab.connect():
                        self.matlab_connected = True
                    else:
                        time.sleep(1)
                        continue
                try:
                    data = self.matlab.read_data()
                    with self.data_lock:
                        current_timestamp = time.time() - self.matlab.start_time
                        self.current_rpm = data.rotor_speed
                        temp_cur_rpm = data.rotor_speed
                        self.current_angle = data.angle
                        current_temp_angle = data.angle
                        load = self.load
                        object_diameter = self.object_diameter
                        distance_between_centers = self.distance_between_centers

                        auto_manual = int(self.auto_manual)
                        start_stop_manual = int(self.start_stop_manual)
                        start_stop_auto = int(self.start_stop_auto)
                        direction = self.direction
                        reset = self.reset
                        home = self.home
                        target_angle = self.target_angle
                        speed_auto_rpm = self.speed_auto_rpm
                        speed_manual_percent = self.speed_manual_percent
                        remote_local = self.remote_local
                        home_mem = self.home_mem
                        run_manual = self.run_manual
                        direction_manual = self.direction_manual
                        slider_speed = self.slider_speed

                    stop_start = 0
                    target_speed = 0
                    #0 local, 1 remote
                    if int(remote_local) == 0:
                        stop_start = 0
                        target_speed = 0.0

                        if run_manual:
                            stop_start = 1
                            real_percent = slider_speed / 100
                            target_speed = real_percent * 3.338
                            auto_manual = 1
                            direction = direction_manual
                            if target_speed <= 0:
                                stop_start = 0
                        if home_mem:
                            stop_start = 1
                            auto_manual = 0
                            target_angle = 0
                            target_speed = 3.338 * 0.6

                    elif int(remote_local) == 1:
                        if auto_manual == 0:
                            
                            real_percent = speed_manual_percent / 100
                            target_speed = real_percent * 3.338
                            stop_start = int(start_stop_manual)
                        elif auto_manual == 1:
                            
                            target_speed = speed_auto_rpm
                            stop_start = int(start_stop_auto)
                        #
                        if home:
                            stop_start = 1
                            auto_manual = 0
                            target_angle = 0
                            target_speed = 3.338 * 0.6
                        scene_rpm = temp_cur_rpm * (1 / 44.9405)

                    self.matlab.send_data(load,object_diameter,distance_between_centers,int(stop_start),int(auto_manual),int(direction),target_angle,target_speed)
                    print(  f"================================================== \n"
                        # f"Tia Portall sending status: {tia_connected_snd} \n"
                        # f"Tia Portall receive status: {tia_connected_rcv} \n"
                        # f"Unreal Engine status: {unreal_connected} \n"
                        # f"Matlab status: {matlab_connected} \n"
                        f"LOAD: {load} \n"
                        f"diameter: {object_diameter} \n"
                        f"dist: {distance_between_centers} \n"
                        f"start: {stop_start} \n"
                        f"dir: {direction} \n"
                        f"target angle: {target_angle} \n"
                        f"current angle: {current_temp_angle} \n"
                        f"manual_auto: {auto_manual} \n"
                        f"speed: {target_speed} \n"
                        f"speed: {scene_rpm} \n"
                        f"home: {home} \n"
                        f"==================================================")
                        # self.rpm_history.append(self.current_rpm)
                        # # self.torque_history.append(data.electromagnetic_torque)
                        # self.time_history.append(current_timestamp)
                        # activator_temp = self.activator_tia
                        # target_rpm_temp = self.target_rpm
                        # previous_target_rpm_temp = self.previous_target_rpm
                        # breakdown_temp = self.breakdown_tia
                        # target_load = self.load
                        # previous_load = self.previous_load
                        # rotate = self.rotate_tia
                        # working_condition = self.working_condition




                    # if not breakdown_temp and activator_temp:
                    #     target_rpm_temp = target_rpm_temp / 9.55
                    #     if rotate:
                    #         target_rpm_temp = target_rpm_temp * -1
                    #         if working_condition == 0 :
                    #             if target_rpm_temp != previous_target_rpm_temp:
                    #                 self.matlab.send_data(round(target_rpm_temp,1),target_load)
                    #                 with self.data_lock:
                    #                     self.previous_target_rpm = target_rpm_temp
                    #         elif working_condition == 7 or working_condition == 9:
                    #             self.matlab.send_data(round(zero_rpm, 1), target_load)
                    #             with self.data_lock:
                    #                 self.previous_target_rpm = zero_rpm
                    #         else:
                    #             if target_rpm_temp != previous_target_rpm_temp:
                    #                 self.matlab.send_data(round(target_rpm_temp, 1), target_load)
                    #                 with self.data_lock:
                    #                     self.previous_target_rpm = target_rpm_temp
                    #     else:
                    #         if working_condition == 8 or working_condition == 9:
                    #             self.matlab.send_data(round(zero_rpm, 1), target_load)
                    #             with self.data_lock:
                    #                 self.previous_target_rpm = zero_rpm
                    #         else:
                    #             if target_rpm_temp != previous_target_rpm_temp:
                    #                 with self.data_lock:
                    #                     self.previous_target_rpm = target_rpm_temp
                    #                 self.matlab.send_data(round(target_rpm_temp, 1),target_load)
                    #             elif target_load != previous_load:
                    #                 with self.data_lock:
                    #                     self.previous_load = target_load
                    #                 print(target_load)
                    # else:
                    #     self.matlab.send_data(round(zero_rpm, 1),target_load)
                    #     with self.data_lock:
                    #         self.previous_target_rpm = 0

                except socket.timeout:
                    pass

            except Exception as e:
                print(f"[matlab Error] {e}")
                self.matlab_connected = False


            time.sleep(0.1)




    def _unreal_worker_rcv_snd(self):
        rpm = 0.0
        while self.running:
            try:
                if not self.unreal_connected:
                    if self.unreal_snd.connect():
                        self.unreal_connected = True
                    else:
                        time.sleep(1)
                        continue
                else:
                    # new_load = self.unreal_rcv.current_load
                    # new_current_obj_diameter = self.unreal_rcv.current_obj_diameter
                    # new_current_dist_between_centers = self.unreal_rcv.current_dist_between_centers
                    # set_rpm = self.unreal_rcv.set_rpm
                    # set_angle = self.unreal_rcv.set_angle
                    # set_direction = self.unreal_rcv.set_direction
                    # manual_auto = self.unreal_rcv.manual_auto
                    # start = self.unreal_rcv.start
                    with self.data_lock:
                        # self.load = new_load
                        # self.object_diameter = new_current_obj_diameter
                        # self.distance_between_centers = new_current_dist_between_centers
                        # self.target_rpm = set_rpm
                        # self.target_angle = set_angle
                        # self.direction = set_direction
                        # self.auto_manual = manual_auto
                        # self.stop_start = start
                        rpm = self.current_rpm
                        angle = self.current_angle

                    scene_rpm = rpm * (1/44.9405)
                    self.unreal_snd.send_data(rpm, angle, scene_rpm)

            except Exception as e:
                print(f"[Unreal Send Error] Nie udało sie wysłać danych {e}")

            time.sleep(0.01)

    def _unreal_worker_server(self):
        self.unreal_rcv.start_listening()



    def start(self, log_every_n = 5):
        self.running = True
        t_tia_rc = threading.Thread(target=self._tia_worker_rc, daemon=True)
        # t_tia_snd = threading.Thread(target=self._tia_worker_snd, daemon=True)
        t_matlab = threading.Thread(target=self._matlab_worker, daemon=True)
        t_unreal_rc = threading.Thread(target=self._unreal_worker_server, daemon=True)
        t_unreal_snd = threading.Thread(target=self._unreal_worker_rcv_snd, daemon=True)
        t_tia_rc.start()
        # t_tia_snd.start()
        t_matlab.start()
        t_unreal_rc.start()
        t_unreal_snd.start()


        self._loop()

    def stop(self):
        self.running = False
        self.matlab.disconnect()
        self.tia_portal_rc.disconnect()
        self.unreal_rcv.disconnect()

        print(f"SYMULACJA ZAKOŃCZONA")
        print(f"Czas trwania połączenia z Matlabem: {self.matlab.total_duration:.2f} sekund")


        self.plot_results()

    def plot_results(self):
        # Generujemy oś czasu na podstawie liczby próbek i kroku 1e-5
        # np.arange jest szybsze niż lista
        if not self.torque_history or not self.time_history:
            print("Brak danych do wyrysowania.")
            return

        time_axis = self.time_history

        plt.figure(figsize=(10, 8))

        # Wykres 1: Moment (Torque)
        plt.subplot(2, 1, 1)
        plt.plot(time_axis, self.torque_history, label='Torque', color='blue')
        plt.title(f'Electromagnetic Torque (Total: {time_axis[-1]:.2f}s)')
        plt.ylabel('Torque [Nm]')
        plt.grid(True)
        plt.legend()

        # Wykres 2: Prędkość (RPM)
        plt.subplot(2, 1, 2)
        plt.plot(time_axis, self.rpm_history, label='Rotor Speed', color='orange')
        plt.title('Rotor Speed')
        plt.xlabel('Real Time [s]')  # Zmieniono etykietę
        plt.ylabel('Speed [RPM]')
        plt.grid(True)
        plt.legend()

        plt.tight_layout()
        plt.show()


    def _loop(self):
        try:
            while self.running:
                curr = 0.0
                with self.data_lock:
                    tia_connected_snd = self.tia_connected_snd
                    tia_connected_rcv = self.tia_connected_rc
                    unreal_connected = self.unreal_connected
                    matlab_connected = self.matlab_connected
                    load = self.unreal_rcv.current_load
                    diameter = self.unreal_rcv.current_obj_diameter
                    dist = self.unreal_rcv.current_dist_between_centers
                    start = self.stop_start
                    dir = self.direction
                    angle = self.target_angle
                    manual_auto = self.auto_manual
                # print(  f"================================================== \n"
                #         # f"Tia Portall sending status: {tia_connected_snd} \n"
                #         # f"Tia Portall receive status: {tia_connected_rcv} \n"
                #         # f"Unreal Engine status: {unreal_connected} \n"
                #         # f"Matlab status: {matlab_connected} \n"
                #         f"LOAD: {load} \n"
                #         f"diameter: {diameter} \n"
                #         f"dist: {dist} \n"
                #         f"start: {start} \n"
                #         f"dir: {dir} \n"
                #         f"target angle: {angle} \n"
                #         f"manual_auto: {manual_auto} \n"
                #         f"==================================================")

                time.sleep(2)
                    # print(curr)
        except KeyboardInterrupt:
            self.stop()



