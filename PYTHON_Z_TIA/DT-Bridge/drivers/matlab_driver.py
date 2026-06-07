import socket
import struct
import time
from xml.sax.saxutils import escape

from core.interfaces import DeviceInterface
from core.models import MatlabData
import config

class MatlabUDP_RC_SND(DeviceInterface):
    def __init__(self):
        self.target_ip = config.UDP_IP_MATLAB
        self.target_port_rc = config.UDP_PORT_MATLAB_RC
        self.target_port_snd = config.UDP_PORT_MATLAB_SND
        self.signal = 0
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.speed = 0
        #Debug
        self.first_package = True
        self.start_time = 0
        self.total_duration = 0

    def connect(self) -> bool:
        try:
            if self.sock:
                try:
                    self.sock.close()
                except:
                    pass
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind((self.target_ip, self.target_port_rc))
            self.sock.settimeout(0.2)
            return True
        except Exception as e:
            return False

    def disconnect(self) -> bool:
        self.sock.close()
        self.total_duration = time.time() - self.start_time

    def read_data(self, check = False) -> MatlabData:
        try:
            if check:
                self.sock.settimeout(0.1)
            else:
                self.sock.settimeout(1.0)
            data, addr = self.sock.recvfrom(1024)
            try:
                self.sock.settimeout(0.0)
                while True:
                    try:
                        new_data, _ = self.sock.recvfrom(1024)
                        data = new_data
                    except BlockingIOError:
                        break
                    except socket.error:
                        break
            except Exception:
                pass

            if len(data) == 16:
                if self.first_package and check is False:
                    self.start_time = time.time()

                    self.first_package = False
                value_rpm, angle = struct.unpack('>dd', data)
            else:
                print(f"Otrzymano pakiet o innej dlugoci: {len(data)} bajtow")
                value_rpm, angle = 0, 0

            return MatlabData(value_rpm,angle)
        except socket.timeout:
            raise
        except Exception as e:
            print(f"Read error: {e}")
            raise

    def send_data(self, load: float, object_diameter: float, dist_between_centers: float, Stop_Start: int, Auto_Manual: int, Left_Right: int, Set_angle: int, Set_speed):
        try:
            self.sock.settimeout(1.0)
            packet = struct.pack('>dddddddd', load, object_diameter, dist_between_centers, Stop_Start, Auto_Manual, Left_Right, Set_angle, Set_speed)
            self.sock.sendto(packet,(self.target_ip,self.target_port_snd))
        except socket.timeout:
            raise
        except Exception as e:
            print(f"write error: {e}")
            raise

    def is_matlab_connected(self) -> bool:
        try:
            data = self.read_data(check=True)
            return True
        except socket.timeout:
            return False
        except Exception as e:
            print(f"Matlab Error: {e}")
            return False









