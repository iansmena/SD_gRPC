import grpc
import telemetria_pb2
import telemetria_pb2_grpc
from concurrent import futures
from datetime import datetime
import random
import time


# Camiones registrados con su posicion inicial (latitud, longitud)
CAMIONES = {
    "CAM-001": (-0.1807, -78.4678),
    "CAM-002": (-2.1894, -79.8891),
}

# Constantes
TEMP_MIN = 2.0
TEMP_MAX = 8.0
TOTAL_LECTURAS = 10
PUERTO = "50052"
INTERVALO_DEFAULT = 1.0


class MonitorCadenaFrioServicer(telemetria_pb2_grpc.MonitorCadenaFrioServicer):

    def TransmitirTelemetria(self, request, context):
        # Regla 1: el camion debe existir
        if request.id_camion not in CAMIONES:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"El camión {request.id_camion} no existe en el sistema")
            return

        for _ in range(TOTAL_LECTURAS):
            if not context.is_active():
                print("[servidor] El cliente se desconectó")
                return

            # Simulacion: rango mas amplio que 2-8 para que aparezcan alertas
            temperatura = round(random.uniform(0.0, 10.0), 2)

            # Regla 3: alerta si baja de 2.0 o supera 8.0
            alerta = temperatura < TEMP_MIN or temperatura > TEMP_MAX

            # yield envia UNA lectura al cliente y pausa la funcion hasta la siguiente vuelta
            yield telemetria_pb2.LecturaSensor(
                id_camion=request.id_camion,
                temperatura_celsius=temperatura,
                latitud=(CAMIONES[request.id_camion][0]),
                longitud=(CAMIONES[request.id_camion][1]),
                timestamp=datetime.now().isoformat(timespec="seconds"),
                alerta_critica=alerta,
            )

            # Regla 2: espera el intervalo pedido antes de la siguiente lectura
            time.sleep(intervalo=request.intervalo if request.intervalo > 0 else INTERVALO_DEFAULT)

        print(f"[servidor] Flujo de {request.id_camion} finalizado")

def servir():
    servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    telemetria_pb2_grpc.add_MonitorCadenaFrioServicer_to_server(
        MonitorCadenaFrioServicer(), servidor)
    servidor.add_insecure_port(f"[::]:{PUERTO}")
    servidor.start()
    print("[servidor] Servicio MonitorCadenaFrio corriendo (Ctrl+C para detener)")
    try:
        servidor.wait_for_termination()
    except KeyboardInterrupt:
        print("\n[servidor] Detenido")


if __name__ == "__main__":
    servir()