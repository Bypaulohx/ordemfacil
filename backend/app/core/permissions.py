from enum import Enum


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    ATTENDANT = "ATTENDANT"
    TECHNICIAN = "TECHNICIAN"


ROLE_LABELS: dict[UserRole, str] = {
    UserRole.ADMIN: "Administrador",
    UserRole.ATTENDANT: "Atendente",
    UserRole.TECHNICIAN: "Técnico",
}
