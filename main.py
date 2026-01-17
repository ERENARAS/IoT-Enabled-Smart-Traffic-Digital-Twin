import os
import sys
import time
import socket


pi_ip = '192.168.1.21'
pi_port = 12345


sumo_config_file = "simulasyon.sumo.cfg"
kavsak_id = "J9"
ambulans_yolu_id = "-E9"
ambulans_seridi_id = "-E9_0"


FAZ_AMBULANS_YESIL = 0
FAZ_AMBULANS_KIRMIZI = 2

# Mesafe ve Süre
base_mesafe = 50.0
arac_basina_ek = 8.0
gecikme_suresi = 4


client_socket = None


def baglanti_kur():
    global client_socket
    try:
        print(f" Raspberry Pi'ye bağlanılıyor... ({pi_ip}:{pi_port})")
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(5)
        client_socket.connect((pi_ip, pi_port))
        print("BAŞARILI! Bağlantı kuruldu.")
    except:
        print("UYARI: Raspberry Pi bulunamadı, simülasyon internetsiz devam ediyor.")


def sinyal_gonder(mesaj):
    if client_socket:
        try:
            client_socket.send(mesaj.encode())
        except:
            pass



# SUMO BAŞLATMA

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("HATA: SUMO_HOME bulunamadı.")

import traci

sumoCmd = ["sumo-gui", "-c", sumo_config_file, "--start", "--delay", "100"]

baglanti_kur()
traci.start(sumoCmd)


# Simülasyon başlar başlamaz ışığı KIRMIZI (Normal Trafik) yapıyoruz.
traci.trafficlight.setPhase(kavsak_id, FAZ_AMBULANS_KIRMIZI)
print("🔒 Işıklar Varsayılan Konuma (KIRMIZI) Kilitlendi.")


durum_gonderildi = False
acil_durum_modu = False
son_ambulans_zamani = 0

while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()

    su_anki_zaman = traci.simulation.getTime()
    arac_listesi = traci.vehicle.getIDList()

    # Ambulansı Bul
    aktif_ambulans = None
    for arac in arac_listesi:
        if "ambulans" in arac:
            aktif_ambulans = arac
            break

    # AMBULANS VARSA
    if aktif_ambulans:
        try:
            tls_data = traci.vehicle.getNextTLS(aktif_ambulans)
            if len(tls_data) > 0:
                mesafe = tls_data[0][2]

                # Kuyruk Hesabı
                seritteki_araclar = traci.lane.getLastStepVehicleIDs(ambulans_seridi_id)
                ambulans_konumu = traci.vehicle.getLanePosition(aktif_ambulans)
                onundeki_arac_sayisi = 0
                for diger_arac in seritteki_araclar:
                    if diger_arac == aktif_ambulans: continue
                    if traci.vehicle.getLanePosition(diger_arac) > ambulans_konumu:
                        onundeki_arac_sayisi += 1

                tetikleme_mesafesi = base_mesafe + (onundeki_arac_sayisi * arac_basina_ek)

                # Mesafeye girdiyse YEŞİL yap
                if mesafe < tetikleme_mesafesi:
                    traci.trafficlight.setPhase(kavsak_id, FAZ_AMBULANS_YESIL)
                    son_ambulans_zamani = su_anki_zaman
                    acil_durum_modu = True

                    if not durum_gonderildi:
                        sinyal_gonder("AMBULANS_GELDI")
                        print(f"🚑 YEŞİL YAKILDI! (Mesafe: {mesafe:.1f}m)")
                        durum_gonderildi = True

        except:
            pass

    # AMBULANS YOKSA
    else:
        # Eğer acil durum modundaysak (Ambulans yeni gittiyse)
        if acil_durum_modu:
            gecen_sure = su_anki_zaman - son_ambulans_zamani

            # Güvenlik süresi (4 saniye) bitti mi?
            if gecen_sure > gecikme_suresi:
                # EVET BİTTİ KIRMIZIYA DÖN VE KİLİTLE
                traci.trafficlight.setPhase(kavsak_id, FAZ_AMBULANS_KIRMIZI)
                acil_durum_modu = False

                if durum_gonderildi:
                    sinyal_gonder("AMBULANS_GITTI")
                    print("🛑 Ambulans geçti, sistem KIRMIZIYA kilitlendi.")
                    time.sleep(2)
                    durum_gonderildi = False
            else:
                # HAYIR BİTMEDİ Hala Yeşil tut (Kavşak boşalsın)
                traci.trafficlight.setPhase(kavsak_id, FAZ_AMBULANS_YESIL)

        # Acil durum yoksa, standart olarak hep KIRMIZI tut
        else:
            traci.trafficlight.setPhase(kavsak_id, FAZ_AMBULANS_KIRMIZI)

traci.close()
if client_socket:
    client_socket.close()