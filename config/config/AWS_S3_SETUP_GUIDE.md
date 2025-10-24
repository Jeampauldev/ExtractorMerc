# 🔧 **GUÍA DE CONFIGURACIÓN AWS S3 - EXTRACTOROV**

## 📋 **PASO 1: OBTENER CREDENCIALES AWS**

### **1.1 Acceso a AWS Console**
1. Ve a https://aws.amazon.com/console/
2. Inicia sesión con tu cuenta AWS
3. Navega a **IAM** (Identity and Access Management)

### **1.2 Crear Usuario IAM para ExtractorOV**
```bash
# Crear usuario específico para el bot
Usuario: extractorov-bot
Tipo de acceso: Acceso programático
```

### **1.3 Configurar Permisos S3**
Asignar la siguiente política JSON al usuario:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ExtractorOVS3Access",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket",
                "s3:GetBucketLocation",
                "s3:GetObjectVersion",
                "s3:PutObjectAcl"
            ],
            "Resource": [
                "arn:aws:s3:::extractorov-data",
                "arn:aws:s3:::extractorov-data/*"
            ]
        }
    ]
}
```

### **1.4 Descargar Credenciales**
- **Access Key ID**: AKIA...
- **Secret Access Key**: wJalrXUtnFEMI/K7MDENG...

---

## 📦 **PASO 2: CONFIGURAR BUCKET S3**

### **2.1 Crear Bucket**
```bash
# Nombre del bucket
extractorov-data

# Región recomendada
us-east-1 (por costos y latencia)
```

### **2.2 Estructura del Bucket**
```
extractorov-data/
├── raw_data/
│   ├── RE123456789/
│   │   ├── RE123456789_data_20251010_143022.json
│   │   └── adjuntos/
│   ├── RE987654321/
│   │   └── RE987654321_data_20251010_143045.json
│   └── misc_afinia/
│       └── archivos_sin_reclamo/
└── processed/
    ├── daily_reports/
    └── consolidated/
```

### **2.3 Configurar Bucket Policy**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ExtractorOVAccess",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::YOUR-ACCOUNT-ID:user/extractorov-bot"
            },
            "Action": "s3:*",
            "Resource": [
                "arn:aws:s3:::extractorov-data",
                "arn:aws:s3:::extractorov-data/*"
            ]
        }
    ]
}
```

---

## ⚙️ **PASO 3: CONFIGURAR VARIABLES DE ENTORNO**

### **3.1 Crear archivo .env**
```bash
# Crear archivo en config/env/.env
```

### **3.2 Configuración Completa**
```bash
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=AKIA_TU_ACCESS_KEY_REAL
AWS_SECRET_ACCESS_KEY=tu_secret_access_key_real
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=extractorov-data
S3_BASE_PATH=raw_data
AWS_S3_IAM_USER=extractorov-bot

# RDS Database Configuration
RDS_HOST=ce-ia.cluster-xyz.us-east-1.rds.amazonaws.com
RDS_DATABASE=ce-ia
RDS_USERNAME=tu_usuario_rds
RDS_PASSWORD=tu_password_rds
RDS_PORT=5432

# Oficinas Virtuales
OV_AFINIA_USERNAME=tu_usuario_afinia
OV_AFINIA_PASSWORD=tu_password_afinia
OV_AIRE_USERNAME=tu_usuario_aire
OV_AIRE_PASSWORD=tu_password_aire

# App Configuration
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO
```

---

## 🧪 **PASO 4: TESTING Y VALIDACIÓN**

### **4.1 Test de Conectividad AWS**