# 🚨 **SOLUCIÓN PERMISOS S3 - ACCESS DENIED**

## ❌ **PROBLEMA DETECTADO**
```
User: arn:aws:iam::062967432053:user/IAM-S3-CEIA-Produccion 
is not authorized to perform: s3:PutObject
```

**Tu usuario tiene permisos de LECTURA pero NO de ESCRITURA**

---

## ✅ **SOLUCIÓN PASO A PASO**

### **OPCIÓN 1: Actualizar Permisos IAM (RECOMENDADO)**

1. **Ve a AWS Console** → IAM → Users
2. **Busca el usuario:** `IAM-S3-CEIA-Produccion`
3. **Ir a la pestaña "Permissions"**
4. **Agregar la siguiente política:**

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ExtractorOVS3WriteAccess",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl",
                "s3:DeleteObject",
                "s3:GetObject",
                "s3:ListBucket",
                "s3:GetBucketLocation",
                "s3:GetObjectVersion"
            ],
            "Resource": [
                "arn:aws:s3:::bucket-s3-ceia-produccion-a903ce24-8ecd-4dea-b9a3-eb34763d4b05",
                "arn:aws:s3:::bucket-s3-ceia-produccion-a903ce24-8ecd-4dea-b9a3-eb34763d4b05/*"
            ]
        }
    ]
}
```

### **OPCIÓN 2: Usar Política AWS Predefinida**

1. **Ir a:** IAM → Users → `IAM-S3-CEIA-Produccion`
2. **Attach policies**
3. **Buscar y agregar:** `AmazonS3FullAccess` (solo para testing)

---

## 🧪 **VERIFICAR LA SOLUCIÓN**

Después de actualizar permisos, ejecutar:

```bash
# Test básico
python config/check_s3_status.py

# Test de carga
python -m src.services.aws_s3_service
```

---

## 🔍 **DIAGNÓSTICO ACTUAL**

```bash
Bucket: bucket-s3-ceia-produccion-a903ce24-8ecd-4dea-b9a3-eb34763d4b05
Usuario: IAM-S3-CEIA-Produccion
Región: us-west-2
Estado: ✅ Conectado / ❌ Sin permisos de escritura
```

---

## 📝 **POLÍTICA MÍNIMA REQUERIDA**

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::bucket-s3-ceia-produccion-a903ce24-8ecd-4dea-b9a3-eb34763d4b05/*",
                "arn:aws:s3:::bucket-s3-ceia-produccion-a903ce24-8ecd-4dea-b9a3-eb34763d4b05"
            ]
        }
    ]
}
```

---

## 🚀 **PRÓXIMOS PASOS**

1. ✅ **Actualizar permisos IAM** (tú o administrador AWS)
2. ⏳ **Probar conexión:** `python config/check_s3_status.py`
3. ⏳ **Test de carga:** `python -m src.services.aws_s3_service`
4. ⏳ **Continuar con scheduler y monitoreo**

---

**¿Necesitas que alguien más actualice los permisos o tienes acceso de administrador IAM?**