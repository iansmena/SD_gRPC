import grpc
import pagos_pb2
import pagos_pb2_grpc

DIRECCION = "localhost:50051"


def probar(stub, titulo, solicitud):
    print(f"\n--- {titulo} ---")
    try:
        respuesta = stub.VerificarTransaccion(solicitud, timeout=2)
        if respuesta.aprobado:
            print(f"APROBADA. Código de autorización: {respuesta.codigo_autorizacion}")
        else:
            print(f"RECHAZADA. Motivo: {respuesta.motivo_rechazo}")
    except grpc.RpcError as e:
        print(f"Error gRPC -> código: {e.code()}")
        print(f"              detalle: {e.details()}")


def main():
    with grpc.insecure_channel(DIRECCION) as canal:
        stub = pagos_pb2_grpc.ValidadorPagosStub(canal)

        # Caso 1: pago exitoso
        probar(stub, "Caso 1: pago exitoso", pagos_pb2.SolicitudPago(
            id_transaccion="TX-001",
            numero_tarjeta="5105105105105100",
            monto=250.75,
            codigo_moneda="USD",
            pais_origen="EC",
        ))

        # Caso 2: monto negativo
        probar(stub, "Caso 2: monto negativo", pagos_pb2.SolicitudPago(
            id_transaccion="TX-002",
            numero_tarjeta="5105105105105100",
            monto=-50.0,
            codigo_moneda="USD",
            pais_origen="EC",
        ))

        # Caso 3: tarjeta denegada
        probar(stub, "Caso 3: tarjeta en lista negra", pagos_pb2.SolicitudPago(
            id_transaccion="TX-003",
            numero_tarjeta="4000123412341234",
            monto=120.0,
            codigo_moneda="USD",
            pais_origen="US",
        ))

        # Caso 4: monto alto desde un pais no permitido
        probar(stub, "Caso 4 (extra): monto alto fuera de US/MX", pagos_pb2.SolicitudPago(
            id_transaccion="TX-004",
            numero_tarjeta="5105105105105100",
            monto=15000.0,
            codigo_moneda="USD",
            pais_origen="EC",
        ))


if __name__ == "__main__":
    main()