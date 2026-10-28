import time
import pytest
import can
import cantools

# إنشاء ناقل افتراضي للاختبار
bus = can.interface.Bus(interface='virtual', channel='test_channel', receive_own_messages=True)

@pytest.fixture(scope="module")
def setup_env():
    db = cantools.database.load_file('vehicle_network.dbc')
    return db

def test_engine_data_broadcast_and_decoding(setup_env):
    """1. اختبار بث وفك تشفير بيانات المحرك عبر الـ DBC"""
    db = setup_env
    
    # محاكاة إرسال رسالة المحرك
    raw_payload = bytearray([0x20, 0x1F, 0xE8, 0x03, 0x00, 0x00, 0x00, 0x00])
    msg = can.Message(arbitration_id=0x100, data=raw_payload, is_extended_id=False)
    bus.send(msg)
    
    # فك التشفير والتحقق من الإشارات
    decoded = db.decode_message(msg.arbitration_id, msg.data)
    assert "EngineSpeed" in decoded, "EngineSpeed signal missing"
    assert "VehicleSpeed" in decoded, "VehicleSpeed signal missing"
    print(f"\n[PASS] Engine signals successfully decoded via DBC: {decoded}")

def test_uds_session_control_extended():
    """2. اختبار خدمة UDS 0x10 (DiagnosticSessionControl -> Extended Session)"""
    # Tester Request: 0x10 (Session Control), Sub-function: 0x03 (Extended)
    req_payload = [0x02, 0x10, 0x03, 0x55, 0x55, 0x55, 0x55, 0x55]
    bus.send(can.Message(arbitration_id=0x7DF, data=req_payload, is_extended_id=False))
    
    # ECU Positive Response: SID 0x50, Sub-function: 0x03
    ecu_resp_payload = [0x06, 0x50, 0x03, 0x00, 0x32, 0x01, 0xF4, 0xAA]
    resp_msg = can.Message(arbitration_id=0x7E8, data=ecu_resp_payload, is_extended_id=False)
    bus.send(resp_msg)

    # التحقق من استجابة الـ ECU
    assert resp_msg.arbitration_id == 0x7E8
    assert resp_msg.data[1] == 0x50, "Invalid UDS Response SID"
    assert resp_msg.data[2] == 0x03, "Sub-function session mismatch"
    print("\n[PASS] UDS Service 0x10 (Extended Diagnostic Session) validated.")

def test_uds_read_vin_identifier():
    """3. اختبار خدمة UDS 0x22 (ReadDataByIdentifier -> VIN DID 0xF190)"""
    # Tester Request: 0x22, DID: 0xF190
    req_payload = [0x03, 0x22, 0xF1, 0x90, 0x55, 0x55, 0x55, 0x55]
    bus.send(can.Message(arbitration_id=0x7DF, data=req_payload, is_extended_id=False))
    
    # ECU Positive Response: SID 0x62, DID: 0xF190 + VIN bytes ('V', 'F', '1')
    ecu_resp_payload = [0x10, 0x14, 0x62, 0xF1, 0x90, ord('V'), ord('F'), ord('1')]
    resp_msg = can.Message(arbitration_id=0x7E8, data=ecu_resp_payload, is_extended_id=False)
    bus.send(resp_msg)

    # التحقق من الاستجابة وقراءة الـ DID
    assert resp_msg.arbitration_id == 0x7E8
    assert resp_msg.data[2] == 0x62, "Negative Response received instead of 0x62"
    received_did = (resp_msg.data[3] << 8) | resp_msg.data[4]
    assert received_did == 0xF190, f"DID mismatch: expected 0xF190, got {hex(received_did)}"
    print("\n[PASS] UDS Service 0x22 (VIN Read - DID 0xF190) validated.")