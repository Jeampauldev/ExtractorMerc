"""
Modelos de datos para el procesador de Afinia.

Este módulo define las clases y estructuras de datos utilizadas para
representar y validar la información de PQR extraída de Afinia.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class TipoPQR(Enum):
    """Tipos de PQR válidos en el sistema de Afinia."""
    PETICION = "Petición"
    QUEJA = "Queja"
    RECLAMO = "Reclamo"
    SUGERENCIA = "Sugerencia"
    DENUNCIA = "Denuncia"


class EstadoSolicitud(Enum):
    """Estados posibles de una solicitud PQR."""
    PENDIENTE = "Pendiente"
    EN_PROCESO = "En proceso"
    RESUELTO = "Resuelto"
    CERRADO = "Cerrado"
    CANCELADO = "Cancelado"


class CanalRespuesta(Enum):
    """Canales de respuesta disponibles."""
    CORREO = "Correo electrónico"
    TELEFONO = "Teléfono"
    PRESENCIAL = "Presencial"
    PORTAL_WEB = "Portal web"
    CORRESPONDENCIA = "Correspondencia física"


@dataclass
class AfiniaPQRData:
    """
    Modelo de datos para una PQR de Afinia.

    Representa la estructura completa de datos extraídos del sistema
    de oficina virtual de Afinia.
    """
    # Campos obligatorios
    nic: str
    fecha: str
    documento_identidad: str
    nombres_apellidos: str
    numero_radicado: str
    estado_solicitud: str

    # Campos opcionales con valores por defecto
    correo_electronico: Optional[str] = ""
    telefono: Optional[str] = ""
    celular: Optional[str] = ""
    tipo_pqr: Optional[str] = ""
    canal_respuesta: Optional[str] = ""
    lectura: Optional[str] = ""
    documento_prueba: Optional[str] = ""
    cuerpo_reclamacion: Optional[str] = ""
    finalizar: Optional[str] = ""
    adjuntar_archivo: Optional[str] = ""
    numero_reclamo_sgc: Optional[str] = ""
    comentarios: Optional[str] = ""

    # Metadatos del procesamiento
    fecha_procesamiento: Optional[datetime] = field(default_factory=datetime.now)
    archivo_origen: Optional[str] = ""
    hash_registro: Optional[str] = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el objeto a diccionario para inserción en BD."""
        return {
            'nic': self.nic,
            'fecha': self.fecha,
            'documento_identidad': self.documento_identidad,
            'nombres_apellidos': self.nombres_apellidos,
            'correo_electronico': self.correo_electronico,
            'telefono': self.telefono,
            'celular': self.celular,
            'tipo_pqr': self.tipo_pqr,
            'canal_respuesta': self.canal_respuesta,
            'numero_radicado': self.numero_radicado,
            'estado_solicitud': self.estado_solicitud,
            'lectura': self.lectura,
            'documento_prueba': self.documento_prueba,
            'cuerpo_reclamacion': self.cuerpo_reclamacion,
            'finalizar': self.finalizar,
            'adjuntar_archivo': self.adjuntar_archivo,
            'numero_reclamo_sgc': self.numero_reclamo_sgc,
            'comentarios': self.comentarios,
            'fecha_procesamiento': self.fecha_procesamiento,
            'archivo_origen': self.archivo_origen,
            'hash_registro': self.hash_registro
        }

    @classmethod
    def from_json(cls, json_data: Dict[str, Any], archivo_origen: str = "") -> 'AfiniaPQRData':
        """
        Crea una instancia desde datos JSON.

        Args:
            json_data: Diccionario con los datos JSON
            archivo_origen: Nombre del archivo de origen

        Returns:
            Instancia de AfiniaPQRData
        """
        return cls(
            nic=json_data.get('nic', ''),
            fecha=json_data.get('fecha', ''),
            documento_identidad=json_data.get('documento_identidad', ''),
            nombres_apellidos=json_data.get('nombres_apellidos', ''),
            correo_electronico=json_data.get('correo_electronico', ''),
            telefono=json_data.get('telefono', ''),
            celular=json_data.get('celular', ''),
            tipo_pqr=json_data.get('tipo_pqr', ''),
            canal_respuesta=json_data.get('canal_respuesta', ''),
            numero_radicado=json_data.get('numero_radicado', ''),
            estado_solicitud=json_data.get('estado_solicitud', ''),
            lectura=json_data.get('lectura', ''),
            documento_prueba=json_data.get('documento_prueba', ''),
            cuerpo_reclamacion=json_data.get('cuerpo_reclamacion', ''),
            finalizar=json_data.get('finalizar', ''),
            adjuntar_archivo=json_data.get('adjuntar_archivo', ''),
            numero_reclamo_sgc=json_data.get('numero_reclamo_sgc', ''),
            comentarios=json_data.get('comentarios', ''),
            archivo_origen=archivo_origen
        )

    def validate(self) -> List[str]:
        """
        Valida los datos del registro.

        Returns:
            Lista de errores de validación (vacía si es válido)
        """
        errors = []

        # Validar campos obligatorios
        if not self.nic or not self.nic.strip():
            errors.append("NIC es obligatorio")

        if not self.fecha or not self.fecha.strip():
            errors.append("Fecha es obligatoria")

        if not self.documento_identidad or not self.documento_identidad.strip():
            errors.append("Documento de identidad es obligatorio")

        if not self.nombres_apellidos or not self.nombres_apellidos.strip():
            errors.append("Nombres y apellidos son obligatorios")

        if not self.numero_radicado or not self.numero_radicado.strip():
            errors.append("Número de radicado es obligatorio")

        if not self.estado_solicitud or not self.estado_solicitud.strip():
            errors.append("Estado de solicitud es obligatorio")

        # Validar formato de correo si está presente
        if self.correo_electronico and self.correo_electronico.strip():
            if '@' not in self.correo_electronico:
                errors.append("Formato de correo electrónico inválido")

        # Validar longitud de campos
        if len(self.nic) > 50:
            errors.append("NIC excede la longitud máxima (50 caracteres)")

        if len(self.documento_identidad) > 20:
            errors.append("Documento de identidad excede la longitud máxima (20 caracteres)")

        if len(self.nombres_apellidos) > 200:
            errors.append("Nombres y apellidos exceden la longitud máxima (200 caracteres)")

        return errors

    def is_valid(self) -> bool:
        """
        Verifica si el registro es válido.

        Returns:
            True si es válido, False en caso contrario
        """
        return len(self.validate()) == 0

    def generate_hash(self) -> str:
        """
        Genera un hash único para el registro basado en campos clave.

        Returns:
            Hash MD5 del registro
        """
        import hashlib
        
        # Usar campos clave para generar hash único
        key_fields = f"{self.nic}|{self.fecha}|{self.documento_identidad}|{self.numero_radicado}"
        return hashlib.md5(key_fields.encode('utf-8')).hexdigest()

    def __post_init__(self):
        """Procesa los datos después de la inicialización."""
        # Generar hash si no existe
        if not self.hash_registro:
            self.hash_registro = self.generate_hash()

        # Limpiar espacios en blanco
        self.nic = self.nic.strip() if self.nic else ""
        self.fecha = self.fecha.strip() if self.fecha else ""
        self.documento_identidad = self.documento_identidad.strip() if self.documento_identidad else ""
        self.nombres_apellidos = self.nombres_apellidos.strip() if self.nombres_apellidos else ""
        self.numero_radicado = self.numero_radicado.strip() if self.numero_radicado else ""
        self.estado_solicitud = self.estado_solicitud.strip() if self.estado_solicitud else ""


@dataclass
class ProcessingResult:
    """
    Resultado del procesamiento de un archivo o lote de archivos.
    """
    archivo: str
    exito: bool
    total_registros: int = 0
    registros_validos: int = 0
    registros_insertados: int = 0
    registros_actualizados: int = 0
    registros_duplicados: int = 0
    errores: List[str] = field(default_factory=list)
    tiempo_procesamiento: float = 0.0
    inicio_procesamiento: Optional[datetime] = None
    fin_procesamiento: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resultado a diccionario."""
        return {
            'archivo': self.archivo,
            'exito': self.exito,
            'total_registros': self.total_registros,
            'registros_validos': self.registros_validos,
            'registros_insertados': self.registros_insertados,
            'registros_actualizados': self.registros_actualizados,
            'registros_duplicados': self.registros_duplicados,
            'errores': self.errores,
            'tiempo_procesamiento': self.tiempo_procesamiento,
            'inicio_procesamiento': self.inicio_procesamiento.isoformat() if self.inicio_procesamiento else None,
            'fin_procesamiento': self.fin_procesamiento.isoformat() if self.fin_procesamiento else None
        }

    @property
    def tasa_exito(self) -> float:
        """Calcula la tasa de éxito del procesamiento."""
        if self.total_registros == 0:
            return 0.0
        return (self.registros_insertados + self.registros_actualizados) / self.total_registros * 100


@dataclass
class BatchProcessingResult:
    """
    Resultado del procesamiento de un lote de archivos.
    """
    total_archivos: int = 0
    archivos_exitosos: int = 0
    archivos_con_errores: int = 0
    total_registros: int = 0
    total_insertados: int = 0
    total_actualizados: int = 0
    total_duplicados: int = 0
    archivos_procesados: List[ProcessingResult] = field(default_factory=list)
    errores_globales: List[str] = field(default_factory=list)
    inicio_procesamiento: Optional[datetime] = None
    fin_procesamiento: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resultado a diccionario."""
        return {
            'total_archivos': self.total_archivos,
            'archivos_exitosos': self.archivos_exitosos,
            'archivos_con_errores': self.archivos_con_errores,
            'total_registros': self.total_registros,
            'total_insertados': self.total_insertados,
            'total_actualizados': self.total_actualizados,
            'total_duplicados': self.total_duplicados,
            'archivos_procesados': [archivo.to_dict() for archivo in self.archivos_procesados],
            'errores_globales': self.errores_globales,
            'inicio_procesamiento': self.inicio_procesamiento.isoformat() if self.inicio_procesamiento else None,
            'fin_procesamiento': self.fin_procesamiento.isoformat() if self.fin_procesamiento else None,
            'tasa_exito_global': self.tasa_exito_global,
            'tiempo_total': self.tiempo_total
        }

    @property
    def tasa_exito_global(self) -> float:
        """Calcula la tasa de éxito global del lote."""
        if self.total_archivos == 0:
            return 0.0
        return self.archivos_exitosos / self.total_archivos * 100

    @property
    def tiempo_total(self) -> float:
        """Calcula el tiempo total de procesamiento en segundos."""
        if self.inicio_procesamiento and self.fin_procesamiento:
            return (self.fin_procesamiento - self.inicio_procesamiento).total_seconds()
        return 0.0

    def add_file_result(self, result: ProcessingResult):
        """Agrega el resultado de un archivo al lote."""
        self.archivos_procesados.append(result)
        self.total_archivos += 1
        self.total_registros += result.total_registros
        self.total_insertados += result.registros_insertados
        self.total_actualizados += result.registros_actualizados
        self.total_duplicados += result.registros_duplicados

        if result.exito:
            self.archivos_exitosos += 1
        else:
            self.archivos_con_errores += 1
