import grpc
import pagos_pb2
import pagos_pb2_grpc
from concurrent import futures
import uuid                     # para generar codigos de autorizacion unicos

# Constantes
PREFIJO_LISTA_NEGRA = "4000"
LIMITE_MONTO_ALTO = 10_000.0
PAISES_EMISOR = {"US", "MX"}
PUERTO = "50051"

class ValidadorPagosServicer(pagos_pb2_grpc.ValidadorPagosServicer):
    """Implementa el servicio ValidadorPagos definido en el .proto."""

    def VerificarTransaccion(self, request, context):
        print(f"[servidor] Recibida {request.id_transaccion}: "
              f"monto={request.monto} pais={request.pais_origen}")

        tarjeta = request.numero_tarjeta

        # Regla 1: datos invalidos
        tarjeta_valida = len(tarjeta) == 16 and tarjeta.isdigit()
        if request.monto <= 0 or not tarjeta_valida:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Monto o número de tarjeta inválido")
            # Hay que retornar un mensaje aunque vaya vacio; el cliente recibira el error
            return pagos_pb2.ResultadoPago()

        # Regla 2: tarjeta en lista negra
        if tarjeta.startswith(PREFIJO_LISTA_NEGRA):
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            context.set_details("Tarjeta bloqueada por fraude")
            return pagos_pb2.ResultadoPago()

        # Regla 3: monto alto desde un pais que no es el del emisor.
        if request.monto > LIMITE_MONTO_ALTO and request.pais_origen not in PAISES_EMISOR:
            return pagos_pb2.ResultadoPago(
                aprobado=False,
                motivo_rechazo="Rechazada por política de fraude: monto superior a "
                               "10000 USD desde un país distinto al del emisor",
            )

        # Si paso todas las reglas, se aprueba con un codigo de autorizacion
        codigo = "AUT-" + uuid.uuid4().hex[:8].upper()
        return pagos_pb2.ResultadoPago(aprobado=True, codigo_autorizacion=codigo)


def servir():
    servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pagos_pb2_grpc.add_ValidadorPagosServicer_to_server(ValidadorPagosServicer(), servidor)
    servidor.add_insecure_port(f"[::]:{PUERTO}")
    servidor.start()
    print("[servidor] Servicio ValidadorPagos corriendo (Ctrl+C para detener)")
    try:
        servidor.wait_for_termination()
    except KeyboardInterrupt:
        print("\n[servidor] Detenido")


if __name__ == "__main__":
    servir()