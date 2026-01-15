import os
import sys
import time


if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("HATA: SUMO_HOME bulunamadı.")

import traci


sumoCmd = ["sumo-gui", "-c", "simulasyon.sumo.cfg", "--start", "--delay", "100"]


kavsak_id = "J9"
ambulans_yolu_id = "-E9"
ambulans_seridi_id = "-E9_0"


AMBULANS_YESIL = 0
NORMAL_TRAFIK_YESIL = 2


base_mesafe = 50.0
arac_basina_ek = 8.0
son_ambulans_zamani = 0
gecikme_suresi = 4

traci.start(sumoCmd)
print(" Akıllı Trafik Sistemi Başlatıldı...")

step = 0
while traci.simulation.getMinExpectedNumber() > 0:
    time.sleep(0.05)
    traci.simulationStep()

    su_anki_zaman = traci.simulation.getTime()


    arac_listesi = traci.vehicle.getIDList()


    aktif_ambulans = None
    for arac in arac_listesi:
        if "ambulans" in arac:
            aktif_ambulans = arac
            break

    if aktif_ambulans:
        try:


            tls_data = traci.vehicle.getNextTLS(aktif_ambulans)
            if len(tls_data) > 0:
                mesafe = tls_data[0][2]  # Işığa kalan metre


                seritteki_araclar = traci.lane.getLastStepVehicleIDs(ambulans_seridi_id)
                onundeki_arac_sayisi = 0


                ambulans_konumu = traci.vehicle.getLanePosition(aktif_ambulans)

                for diger_arac in seritteki_araclar:
                    if diger_arac == aktif_ambulans:
                        continue
                    diger_konum = traci.vehicle.getLanePosition(diger_arac)

                    if diger_konum > ambulans_konumu:
                        onundeki_arac_sayisi += 1


                tetikleme_mesafesi = base_mesafe + (onundeki_arac_sayisi * arac_basina_ek)


                if mesafe < tetikleme_mesafesi:
                    traci.trafficlight.setPhase(kavsak_id, AMBULANS_YESIL)
                    son_ambulans_zamani = su_anki_zaman  # Zaman damgasını güncelle

                    print(f" {aktif_ambulans} GELİYOR!")
                    print(f"   - Mesafe: {mesafe:.1f}m")
                    print(f"   - Önündeki Araç: {onundeki_arac_sayisi} tane")
                    print(f"   - Yeni Tetikleme Mesafesi: {tetikleme_mesafesi:.1f}m")
                    print("   -> IŞIKLAR YEŞİL KİLİTLENDİ! ")
                else:
                    pass

        except Exception as e:
            pass


    else:

        gecen_sure = su_anki_zaman - son_ambulans_zamani

        if gecen_sure < gecikme_suresi:
            traci.trafficlight.setPhase(kavsak_id, AMBULANS_YESIL)
            print(f"✋ Güvenlik Gecikmesi: {gecikme_suresi - gecen_sure:.1f}sn daha bekleniyor...")

        else:
            traci.trafficlight.setPhase(kavsak_id, NORMAL_TRAFIK_YESIL)

    step += 1

traci.close()
print("Simülasyon Bitti.")