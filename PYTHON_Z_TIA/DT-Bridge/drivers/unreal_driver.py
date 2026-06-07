
from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
from select import error

from core.interfaces import DeviceInterface
from core.models import MatlabData, UnrealData
import config

class UnrealUDPClient(DeviceInterface):
    def __init__(self):
        self.target_ip_rcv = config.UDP_IP_UNREAL_RCV
        self.target_ip_snd = config.UDP_IP_UNREAL_SND

        self.target_port_rcv = config.UDP_PORT_UNREAL_RCV
        self.target_port_snd = config.UDP_PORT_UNREAL_SND

        self.target_addr_info = config.ADDR_INFO

        self.current_load = 0.0
        self.current_obj_diameter = 0.0
        self.current_dist_between_centers=0.0
        self.set_rpm = 0.0
        self.set_angle = 0.0
        self.set_direction = False
        self.manual_auto = False
        self.start = False
        self.connected = False
        self.client_osc = None
        self.server_osc = None
        self.dispatcher = None

    def connect(self) -> bool:
        try:
            self.client_osc = udp_client.SimpleUDPClient(self.target_ip_snd,self.target_port_snd)
            self.connected = True
            return True
        except Exception as e:
            print(f"[Unreal Connect Error] {e}")
            self.connected = False
            return False



    def send_data(self, rotor_speed: float, rotor_angle: float, scene_rpm: float):
        if self.client_osc and rotor_speed:
            self.client_osc.send_message(self.target_addr_info, [rotor_speed, rotor_angle, scene_rpm])

    def create_server(self):
        self.dispatcher = Dispatcher()
        self.dispatcher.map("/*", self._handle_message)

    def start_listening(self):
        self.create_server()
        try:
            self.server_osc = BlockingOSCUDPServer((self.target_ip_rcv, self.target_port_rcv), self.dispatcher)
            self.server_osc.serve_forever()
        except Exception as e:
            print(f"[Unreal Server Error] Nie udało się uruchomić serwera {e}")

    def _handle_message(self, address, *args):
        if len(args) > 0:
            self.current_load = args[0]
            self.current_obj_diameter = args[1]
            self.current_dist_between_centers = args[2]
            self.set_rpm = args[3]
            self.set_angle = args[4]
            self.set_direction = args[5]
            self.manual_auto = args[6]
            self.start = args[7]

    def disconnect(self) -> bool:
        try:
            if self.server_osc:
                self.server_osc.shutdown()
                self.server_osc.server_close()
            self.connected = False
            return True
        except Exception as e:
            print(f"[Unreal Disconnect Errror] Nie udało się rozłączyć z serwerem {e}")


    def is_unreal_connected(self) -> bool:
        return self.connected






