import importlib
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from flask import Flask

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

auth_module = importlib.import_module("Routes.auth_bp")
from Services import usuarios_services


class MasterAdminTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            MARQUEZA_MASTER_ADMIN_USERNAME="admin",
            MARQUEZA_MASTER_ADMIN_EMAIL="admin@marqueza.local",
            MARQUEZA_MASTER_ADMIN_PASSWORD="private-admin-secret",
        )
        self.app.register_blueprint(auth_module.auth_bp, url_prefix="/auth")
        self.client = self.app.test_client()
        self.admin_row = {
            "USUA_ID": 1,
            "USUA_NOMBRE": "admin",
            "USUA_CORREO": "admin@marqueza.local",
            "USUA_CONTRASENA": "private-admin-secret",
            "USUA_ESTADO": "Activo",
            "USUA_DET_ETC_ID": 1,
            "DET_ETC_NOMBRE": "Administrador",
        }

    def test_login_requires_private_secret_and_provisions_admin(self):
        with patch.object(auth_module, "query", return_value=[self.admin_row]), \
                patch.object(usuarios_services, "provisionar_admin_maestro") as provision, \
                patch.object(usuarios_services, "marcar_ultimo_acceso"):
            response = self.client.post("/auth/login", json={
                "usuario": "admin",
                "contrasena": "private-admin-secret",
            })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["usuario"]["nombre"], "admin")
        provision.assert_called_once_with("private-admin-secret")

    def test_wrong_master_secret_is_rejected_before_database_lookup(self):
        with patch.object(auth_module, "query") as database_query, \
                patch.object(usuarios_services, "provisionar_admin_maestro") as provision:
            response = self.client.post("/auth/login", json={
                "usuario": "admin",
                "contrasena": "wrong-secret",
            })

        self.assertEqual(response.status_code, 401)
        database_query.assert_not_called()
        provision.assert_not_called()

    def test_legacy_admin_email_cannot_use_seed_password(self):
        legacy_admin = {**self.admin_row, "USUA_CORREO": "admin@example.com", "USUA_CONTRASENA": "1234"}
        with patch.object(auth_module, "query", return_value=[legacy_admin]), \
                patch.object(usuarios_services, "provisionar_admin_maestro") as provision:
            response = self.client.post("/auth/login", json={
                "correo": "admin@example.com",
                "contrasena": "1234",
            })

        self.assertEqual(response.status_code, 401)
        provision.assert_not_called()

    def test_legacy_admin_email_migrates_with_master_secret(self):
        legacy_admin = {**self.admin_row, "USUA_CORREO": "admin@example.com", "USUA_CONTRASENA": "1234"}
        with patch.object(auth_module, "query", side_effect=[[legacy_admin], [self.admin_row]]) as database_query, \
                patch.object(usuarios_services, "provisionar_admin_maestro") as provision, \
                patch.object(usuarios_services, "marcar_ultimo_acceso"):
            response = self.client.post("/auth/login", json={
                "correo": "admin@example.com",
                "contrasena": "private-admin-secret",
            })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(database_query.call_args.args[1], ("admin@marqueza.local", "admin"))
        provision.assert_called_once_with("private-admin-secret")

    def test_master_cannot_be_updated_or_deleted(self):
        master = {
            "USUA_ID": 1,
            "USUA_NOMBRE": "admin",
            "USUA_CORREO": "admin@marqueza.local",
        }
        with self.app.app_context(), patch.object(usuarios_services, "query", return_value=[master]):
            self.assertEqual(usuarios_services.updateUsuarios(1, {})[1], 403)
            self.assertEqual(usuarios_services.deleteUsuarios(1)[1], 403)

    def test_reserved_master_identity_cannot_be_created(self):
        with self.app.app_context(), patch.object(
            usuarios_services,
            "_payload",
            return_value=("admin", "admin@marqueza.local", "Administrador", "x", "Activo", 1),
        ):
            self.assertEqual(usuarios_services.addUsuarios({})[1], 409)

    def test_first_master_login_provisions_database_row(self):
        with self.app.app_context(), \
                patch.object(usuarios_services, "resolve_rol", return_value=1), \
                patch.object(usuarios_services, "query", side_effect=[[], []]), \
                patch.object(usuarios_services, "hash_password", return_value="bcrypt-hash"), \
                patch.object(usuarios_services, "new_uuid", return_value="uuid"), \
                patch.object(usuarios_services, "execute", return_value=7) as execute:
            user_id = usuarios_services.provisionar_admin_maestro("private-admin-secret")

        self.assertEqual(user_id, 7)
        self.assertIn("INSERT INTO t_usuarios", execute.call_args.args[0])
        self.assertEqual(execute.call_args.args[1][1:4], (
            "admin", "admin@marqueza.local", "bcrypt-hash"
        ))

    def test_altered_master_row_is_restored_by_reserved_email(self):
        altered = {
            "USUA_ID": 7,
            "USUA_NOMBRE": "changed-name",
            "USUA_CORREO": "admin@marqueza.local",
            "USUA_CONTRASENA": "changed-hash",
            "USUA_ESTADO": "Inactivo",
            "USUA_DET_ETC_ID": 2,
        }
        with self.app.app_context(), \
                patch.object(usuarios_services, "resolve_rol", return_value=1), \
                patch.object(usuarios_services, "query", side_effect=[[altered], []]), \
                patch.object(usuarios_services, "verify_password", return_value=False), \
                patch.object(usuarios_services, "hash_password", return_value="restored-hash"), \
                patch.object(usuarios_services, "execute") as execute:
            user_id = usuarios_services.provisionar_admin_maestro("private-admin-secret")

        self.assertEqual(user_id, 7)
        self.assertIn("UPDATE t_usuarios", execute.call_args.args[0])
        self.assertEqual(execute.call_args.args[1], (
            "admin", "admin@marqueza.local", "restored-hash", 1, 7
        ))

    def test_master_password_cannot_be_reset_by_email(self):
        forgot_response = self.client.post("/auth/forgot-password", json={
            "correo": "admin@marqueza.local",
        })
        self.assertEqual(forgot_response.status_code, 403)

        token = "master-reset-test"
        auth_module._reset_tokens[token] = {
            "correo": "admin@marqueza.local",
            "expires": datetime.now(timezone.utc) + timedelta(minutes=5),
        }
        try:
            reset_response = self.client.post("/auth/reset-password", json={
                "token": token,
                "nueva_contrasena": "changed-secret",
            })
        finally:
            auth_module._reset_tokens.pop(token, None)
        self.assertEqual(reset_response.status_code, 403)


if __name__ == "__main__":
    unittest.main()