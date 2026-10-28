import time
import threading
import can

# إعداد ناقل CAN افتراضي مشترك في بيئة العمل
bus = can.interface.Bus(interface='virtual', channel='vcan0', receive_own_messages=False)

def periodic_engine_broadcast():
    """إرسال رسائل دورية لبيانات المحرك (EngineData - ID: 0x100 / 256)"""
    speed_raw = 0
    while True:
        speed_raw = (speed_raw + 10) % 20000
        data = bytearray(8)
        data[0] = 0x20  # RPM LSB
        data[1] = 0x1F  # RPM MSB (~2000 RPM)
        data[2] = speed_raw & 0xFF
        data[3] = (speed_raw >> 8) & 0xFF
        data[4] = 0x00  # Brake: Off

        msg = can.Message(arbitration_id=0x100, data=data, is_extended_id=False)
        try:
            bus.send(msg)
        except can.CanError:
            pass
        time.sleep(0.1)  # إرسال دوري كل 100ms

def uds_diagnostic_server():
    """محاكاة استجابة الـ ECU لطلبات التشخيص UDS (ISO 14229)"""
    print("[ECU] Virtual ECU is running and listening for UDS requests...")
    while True:
        msg = bus.recv()
        if msg and msg.arbitration_id == 0x7DF:  # المعرف القياسي للطلب التشخيصي (Tester Request)
            payload = list(msg.data)
            service_id = payload[1]

            # 1. خدمة DiagnosticSessionControl (0x10)
            if service_id == 0x10:
                sub_function = payload[2]
                # استجابة إيجابية: Positive Response SID = 0x50
                resp_data = [0x06, 0x50, sub_function, 0x00, 0x32, 0x01, 0xF4, 0xAA]
                resp_msg = can.Message(arbitration_id=0x7E8, data=resp_data, is_extended_id=False)
                bus.send(resp_msg)
                print(f"[ECU] Session Control (0x10) -> Switched to sub-function 0x{sub_function:02X}")

            # 2. خدمة ReadDataByIdentifier (0x22)
            elif service_id == 0x22:
                did = (payload[2] << 8) | payload[3]
                if did == 0xF190:  # قراءة رقم الشاسيه VIN
                    resp_data = [0x10, 0x14, 0x62, 0xF1, 0x90, ord('V'), ord('F'), ord('1')]
                    resp_msg = can.Message(arbitration_id=0x7E8, data=resp_data, is_extended_id=False)
                    bus.send(resp_msg)
                    print("[ECU] ReadDataByIdentifier (0x22) -> Returned VIN (DID: 0xF190)")
                else:
                    # استجابة سلبية: Negative Response (0x7F) - Request Out Of Range
                    neg_resp = [0x03, 0x7F, 0x22, 0x31, 0xAA, 0xAA, 0xAA, 0xAA]
                    resp_msg = can.Message(arbitration_id=0x7E8, data=neg_resp, is_extended_id=False)
                    bus.send(resp_msg)

if __name__ == "__main__":
    t = threading.Thread(target=periodic_engine_broadcast, daemon=True)
    t.start()
    uds_diagnostic_server()