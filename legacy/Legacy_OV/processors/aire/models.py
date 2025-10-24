"""
Modelos de datos para el procesador de Aire.

Este módulo define las clases y estructuras de datos utilizadas para
representar y validar la información de PQR extraída de Aire.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class TipoPQR(Enum):
    """Tipos de PQR válidos en el sistema de Aire."""
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
class AirePQRData:
    """
    Modelo de datos para una PQR de Aire.

    Representa la estructura completa de datos extraídos del sistema
    de oficina virtual de Aire.
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
    def from_json(cls, json_data: Dict[str, Any], archivo_origen: str = "") -> 'AirePQRData':
        """
        Crea una instancia desde datos JSON.

        Args:
            json_data: Diccionario con los datos JSON
            archivo_origen: Nombre del archivo de origen

        Returns:
            Instancia de AirePQRData
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

    def validate(self) -> tuple[bool, List[str]]:
        """
        Valida los datos del registro.

        Returns:
            Tupla con (es_válido, lista_errores)
        """
        errors = []

        # Validar campos obligatorios
        if not self.nic:
            errors.append("NIC es obligatorio")
        
        if not self.fecha:
            errors.append("Fecha es obligatoria")
        
        if not self.documento_identidad:
            errors.append("Documento de identidad es obligatorio")
        
        if not self.nombres_apellidos:
            errors.append("Nombres y apellidos son obligatorios")
        
        if not self.numero_radicado:
            errors.append("Número de radicado es obligatorio")
        
        if not self.estado_solicitud:
            errors.append("Estado de solicitud es obligatorio")

        # Validar formato de fecha si está presente
        if self.fecha:
            try:
                datetime.strptime(self.fecha, '%Y-%m-%d')
            except ValueError:
                try:
                    datetime.strptime(self.fecha, '%d/%m/%Y')
                except ValueError:
                    errors.append("Formato de fecha inválido (esperado: YYYY-MM-DD o DD/MM/YYYY)")

        # Validar email si está presente
        if self.correo_electronico and '@' not in self.correo_electronico:
            errors.append("Formato de correo electrónico inválido")

        # Validar tipo PQR si está presente
        if self.tipo_pqr:
            valid_tipos = [tipo.value for tipo in TipoPQR]
            if self.tipo_pqr not in valid_tipos:
                errors.append(f"Tipo PQR inválido: {self.tipo_pqr}")

        # Validar estado solicitud
        if self.estado_solicitud:
            valid_estados = [estado.value for estado in EstadoSolicitud]
            if self.estado_solicitud not in valid_estados:
                errors.append(f"Estado de solicitud inválido: {self.estado_solicitud}")

        # Validar canal respuesta si está presente
        if self.canal_respuesta:
            valid_canales = [canal.value for canal in CanalRespuesta]
            if self.canal_respuesta not in valid_canales:
                errors.append(f"Canal de respuesta inválido: {self.canal_respuesta}")

        return len(errors) == 0, errors

    def generate_hash(self) -> str:
        """
        Genera un hash único para el registro basado en campos clave.

        Returns:
            Hash MD5 del registro
        """
        import hashlib
        
        # Campos clave para generar el hash
        key_fields = [
            self.nic,
            self.documento_identidad,
            self.numero_radicado,
            self.fecha
        ]
        
        # Crear string concatenado
        hash_string = '|'.join(str(field) for field in key_fields)
        
        # Generar hash MD5
        return hashlib.md5(hash_string.encode('utf-8')).hexdigest()

    def __str__(self) -> str:
        """Representación string del objeto."""
        return f"AirePQRData(nic={self.nic}, radicado={self.numero_radicado}, estado={self.estado_solicitud})"

    def __repr__(self) -> str:
        """Representación detallada del objeto."""
        return (f"AirePQRData(nic='{self.nic}', fecha='{self.fecha}', "
                f"documento='{self.documento_identidad}', radicado='{self.numero_radicado}')")


@dataclass
class ProcessingResult:
    """
    Resultado del procesamiento de un archivo o lote de archivos.
    """
    archivo: str
    total_registros: int = 0
    registros_validos: int = 0
    registros_insertados: int = 0
    registros_actualizados: int = 0
    errores: List[str] = field(default_factory=list)
    tiempo_procesamiento: float = 0.0
    fecha_procesamiento: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resultado a diccionario."""
        return {
            'archivo': self.archivo,
            'total_registros': self.total_registros,
            'registros_validos': self.registros_validos,
            'registros_insertados': self.registros_insertados,
            'registros_actualizados': self.registros_actualizados,
            'errores': self.errores,
            'tiempo_procesamiento': self.tiempo_procesamiento,
            'fecha_procesamiento': self.fecha_procesamiento.isoformat()
        }

    @property
    def tasa_exito(self) -> float:
        """Calcula la tasa de éxito del procesamiento."""
        if self.total_registros == 0:
            return 0.0
        return (self.registros_insertados + self.registros_actualizados) / self.total_registros * 100

    @property
    def tiene_errores(self) -> bool:
        """Indica si el procesamiento tuvo errores."""
        return len(self.errores) > 0


@dataclass
class BatchProcessingResult:
    """
    Resultado del procesamiento de un lote de archivos.
    """
    directorio: str
    patron_archivos: str
    total_archivos: int = 0
    archivos_procesados: List[ProcessingResult] = field(default_factory=list)
    inicio_procesamiento: Optional[datetime] = None
    fin_procesamiento: Optional[datetime] = None

    @property
    def total_registros(self) -> int:
        """Total de registros procesados en el lote."""
        return sum(resultado.total_registros for resultado in self.archivos_procesados)

    @property
    def total_insertados(self) -> int:
        """Total de registros insertados en el lote."""
        return sum(resultado.registros_insertados for resultado in self.archivos_procesados)

    @property
    def total_actualizados(self) -> int:
        """Total de registros actualizados en el lote."""
        return sum(resultado.registros_actualizados for resultado in self.archivos_procesados)

    @property
    def tasa_exito_global(self) -> float:
        """Tasa de éxito global del lote."""
        if self.total_registros == 0:
            return 0.0
        return (self.total_insertados + self.total_actualizados) / self.total_registros * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resultado del lote a diccionario."""
        return {
            'directorio': self.directorio,
            'patron_archivos': self.patron_archivos,
            'total_archivos': self.total_archivos,
            'total_registros': self.total_registros,
            'total_insertados': self.total_insertados,
            'total_actualizados': self.total_actualizados,
            'tasa_exito_global': self.tasa_exito_global,
            'archivos_procesados': [resultado.to_dict() for resultado in self.archivos_procesados],
            'inicio_procesamiento': self.inicio_procesamiento.isoformat() if self.inicio_procesamiento else None,
            'fin_procesamiento': self.fin_procesamiento.isoformat() if self.fin_procesamiento else None
        }
