from Models.cliente import Cliente
from orm import orm_delete, orm_insert, orm_list, orm_update
import uuid as uuid_lib

class cliente_services:
    def servListCliente():
        return orm_list("t_cliente", Cliente)

    def addCliente(persona_id):
        return orm_insert("t_cliente", {"CLI_UUID": str(uuid_lib.uuid4()), "CLI_PER_ID": persona_id})

    def deleteCliente(id):
        orm_delete("t_cliente", id)

        return "Cliente eliminado correctamente"

    def updateCliente(id, persona_id):
        orm_update("t_cliente", id, {"CLI_PER_ID": persona_id})

        return "Cliente actualizado correctamente"