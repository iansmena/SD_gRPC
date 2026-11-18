import grpc
import telemetria_pb2
import telemetria_pb2_grpc
import sys

DIRECCION = "localhost:50052"

def monitorear(stub, id_camion, intervalo):
    print(f"\n--- Suscripción a {id_camion} (cada {intervalo} s) ---")
    peticion = telemetria_pb2.SuscripcionCamion(
        id_camion=id_camion, intervalo_segundos=intervalo)
    try:
        for respuesta in stub.TransmitirTelemetria(peticion):
            linea = (f"[{respuesta.timestamp}] {respuesta.id_camion} | "
                     f"{respuesta.temperatura_celsius:5.2f} °C | "
                     f"({respuesta.latitud:.6f}, {respuesta.longitud:.6f})")
            if respuesta.alerta_critica:
                print(f"ALERTA CRÍTICA  {linea}")
            else:
                print(f"OK              {linea}")
        print("Flujo finalizado por el servidor")
    except grpc.RpcError as e:
        print(f"Error gRPC -> código: {e.code()}")
        print(f"              detalle: {e.details()}")


def main():
    id_camion = sys.argv[1] if len(sys.argv) > 1 else "CAM-001"
    intervalo = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    with grpc.insecure_channel(DIRECCION) as canal:
        stub = telemetria_pb2_grpc.MonitorCadenaFrioStub(canal)
        monitorear(stub, id_camion, intervalo)


if __name__ == "__main__":
    main()