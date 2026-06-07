import snap7
from snap7.util import get_real, get_int, get_bool, set_bool, set_int, set_real

from core.interfaces import DeviceInterface
from core.models import TiaPortalData
import config

class TiaPortal_RC_SND(DeviceInterface):
    def __init__(self):
        self.target_ip = config.NETWORK_IP_ADDR
        self.target_rack = config.RACK
        self.target_slot = config.SLOT
        self.target_db_nbr = config.DB_NUMBER
        self.target_start_rd = config.START_READ
        self.target_size_db = config.SIZE_DB
        self.target_tcp_port = config.TCP_PORT
        self.current_load = 0
        self.client = snap7.client.Client()
        self.data = []

    def connect(self) -> bool:
        try:
            self.client.connect(self.target_ip, self.target_rack, self.target_slot, self.target_tcp_port)
            return True
        except Exception as e:
            print(f"TIA Portal Error: {e}")
            self.disconnect()
            return False


    def read_db(self) -> TiaPortalData:
        if not self.client.get_connected():
            raise ConnectionError("Brak Polaczenia z PLC. Najpier wywolaj _connect_to_plc")

        data_buffer = self.client.db_read(self.target_db_nbr,self.target_start_rd,self.target_size_db)
        manual_auto = get_bool(data_buffer, 0, 0)
        start_stop_manual = get_bool(data_buffer, 0, 1)
        start_stop_auto = get_bool(data_buffer, 0, 2)
        direction = get_bool(data_buffer, 0, 3)
        reset = get_bool(data_buffer, 0, 4)
        home = get_bool(data_buffer, 0, 5)
        angle_set = get_real(data_buffer, 2)
        angle_read = get_real(data_buffer,6)
        speed_read = get_real(data_buffer,10)
        speed_auto_rpm = get_real(data_buffer, 14)
        speed_manual_percent = get_real(data_buffer,18)
        remote_local = get_bool(data_buffer, 22, 0)
        home_mem = get_bool(data_buffer, 22, 1)
        run_manual = get_bool(data_buffer, 22, 2)
        direction_manual = get_bool(data_buffer, 22, 3)
        slider_speed = get_real(data_buffer, 24)
        return TiaPortalData(manual_auto,start_stop_manual,start_stop_auto,direction,reset,home,
        angle_set,angle_read,speed_read,speed_auto_rpm,speed_manual_percent, remote_local, home_mem, run_manual, direction_manual, slider_speed)

    def write_db(self, current_rpm: float, current_load: float):
        if not self.client.get_connected():
            raise ConnectionError("Brak Polaczenia z PLC. Najpier wywolaj _connect_to_plc")
        buffer = bytearray(8)
        set_real(buffer, 0, current_rpm)
        set_real(buffer, 4, current_load)
        self.client.db_write(self.target_db_nbr,8,buffer)

    def disconnect(self) -> bool:
        if self.client.get_connected():
            self.client.disconnect()

    def is_tia_connected(self) -> bool:
        return self.client.get_connected()



