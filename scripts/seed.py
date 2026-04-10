import sys
import os

# Esto le dice al script que mire una carpeta hacia atrás para encontrar 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models import Usuario, Mesa, Producto
from app.models.enums import UserRole, MesaEstado
from app.core.security import get_password_hash
from decimal import Decimal

def seed():
    db: Session = SessionLocal()
    try:
        print("--- Iniciando Semilla de Datos para GastroHub ---")

        # 1. CREAR USUARIOS (Los tres roles principales)
        usuarios_demo = [
            {
                "nombre": "Andrés Administrador",
                "email": "admin@gastrohub.com",
                "password": "admin12345",
                "rol": UserRole.ADMIN
            },
            {
                "nombre": "Andrés Mesero",
                "email": "mesero@gastrohub.com",
                "password": "mesero12345",
                "rol": UserRole.MESERO
            },
            {
                "nombre": "Andrés Cocinero",
                "email": "cocina@gastrohub.com",
                "password": "cocina12345",
                "rol": UserRole.COCINA
            }
        ]

        for u in usuarios_demo:
            existe = db.query(Usuario).filter(Usuario.email == u["email"]).first()
            if not existe:
                nuevo_usuario = Usuario(
                    nombre=u["nombre"],
                    email=u["email"],
                    password=get_password_hash(u["password"]),
                    rol=u["rol"],
                    activo=True
                )
                db.add(nuevo_usuario)
                print(f"Usuario {u['rol'].value} creado: {u['email']} / {u['password']}")

        # 2. CREAR MESAS (10 mesas para que el restaurante se vea grande)
        if db.query(Mesa).count() == 0:
            for i in range(1, 11):
                capacidad = 2 if i > 7 else 4 # Mesas pequeñas al fondo
                nueva_mesa = Mesa(numero=i, capacidad=capacidad, estado=MesaEstado.LIBRE)
                db.add(nueva_mesa)
            print("10 Mesas de prueba generadas.")

        # 3. CREAR MENÚ COMPLETO (Variedad para la demo)
        if db.query(Producto).count() == 0:
            menu = [
                {"nombre": "Hamburguesa Especial", "precio": Decimal("22000.00"), "desc": "Carne Angus 200g, tocino y queso chedar"},
                {"nombre": "Papas a la Francesa", "precio": Decimal("9000.00"), "desc": "Porción familiar con salsa de la casa"},
                {"nombre": "Gaseosa 400ml", "precio": Decimal("5000.00"), "desc": "Refrescante sabor original"},
                {"nombre": "Club Colombia 330ml", "precio": Decimal("7500.00"), "desc": "Cerveza nacional premium"},
                {"nombre": "Pizza Pepperoni", "precio": Decimal("25000.00"), "desc": "Masa artesanal y pepperoni importado"},
                {"nombre": "Jugo Natural", "precio": Decimal("6500.00"), "desc": "Fruta de temporada en agua o leche"}
            ]
            for p in menu:
                nuevo_prod = Producto(
                    nombre=p["nombre"], 
                    precio=p["precio"], 
                    descripcion=p["desc"], 
                    disponible=True
                )
                db.add(nuevo_prod)
            print(f"Menú de {len(menu)} productos listo.")

        db.commit()
        print("\n--- GastroHub está listo para operar ---")

    except Exception as e:
        print(f"ERROR: No se pudo completar la semilla: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()