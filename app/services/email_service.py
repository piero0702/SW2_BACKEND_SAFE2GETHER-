import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

async def send_new_report_notification(
    to_email: str,
    follower_username: str,
    author_username: str,
    report_title: str,
    report_id: int,
    report_district: str
) -> bool:
    """Envía notificación por email cuando un usuario seguido sube un nuevo reporte"""
    
    # URL del frontend para ver el reporte
    report_link = f"http://localhost:52802/#/reportes/{report_id}"  # URL local del frontend Flutter
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #08192D 0%, #0D47A1 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
            <h1>🚨 Safe2Gether</h1>
            <p>Nuevo Reporte de Seguridad</p>
        </div>
        
        <div style="background: white; padding: 30px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 8px 8px;">
            <p>Hola <strong>{follower_username}</strong>,</p>
            
            <p><strong>{author_username}</strong> ha publicado un nuevo reporte que podría interesarte:</p>
            
            <div style="background-color: #f8f9fa; border-left: 4px solid #9B080C; padding: 20px; margin: 20px 0;">
                <h2 style="margin-top: 0; color: #08192D;">{report_title}</h2>
                <p style="margin: 10px 0;"><strong>📍 Distrito:</strong> {report_district}</p>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{report_link}" style="background-color: #9B080C; color: white; text-decoration: none; padding: 15px 30px; border-radius: 5px; display: inline-block; font-weight: bold;">
                    Ver Reporte Completo
                </a>
            </div>
            
            <p style="color: #666; font-size: 14px; margin-top: 30px;">
                Puedes configurar tus preferencias de notificación en tu perfil.
            </p>
        </div>
        
        <div style="text-align: center; padding: 20px; color: #999; font-size: 12px;">
            © 2025 Safe2Gether | Este es un email automático
        </div>
    </body>
    </html>
    """
    
    try:
        sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        
        if not sendgrid_api_key:
            print("❌ SENDGRID_API_KEY NO ENCONTRADA para notificación de reporte")
            return False
        
        message = Mail(
            from_email=Email("20213320@aloe.ulima.edu.pe", "Safe_2_Gether!"),
            to_emails=To(to_email),
            subject=f"🚨 Nuevo reporte de {author_username} en {report_district}",
            html_content=Content("text/html", html_content)
        )
        
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        
        if response.status_code in [200, 201, 202]:
            print(f"✅ Notificación de reporte enviada exitosamente a {to_email}")
            return True
        else:
            print(f"⚠️ Error SendGrid Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error en send_new_report_notification: {str(e)}")
        return False


async def send_password_reset_email(
    to_email: str,
    username: str,
    reset_link: str
) -> bool:
    """Envía email usando SendGrid"""
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #08192D 0%, #0D47A1 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
            <h1>🔐 Safe2Gether</h1>
            <p>Recuperación de Contraseña</p>
        </div>
        
        <div style="background: white; padding: 30px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 8px 8px;">
            <p>Hola <strong>{username}</strong>,</p>
            
            <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta.</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" style="background-color: #9B080C; color: white; text-decoration: none; padding: 15px 30px; border-radius: 5px; display: inline-block; font-weight: bold;">
                    Restablecer Contraseña
                </a>
            </div>
            
            <div style="background-color: #f8f9fa; border-left: 4px solid #9B080C; padding: 15px; margin: 20px 0;">
                <strong>⏰ Este link expira en 1 hora</strong>
            </div>
            
            <p>Si tienes problemas, copia este enlace:</p>
            <p style="word-break: break-all; color: #0D47A1;">{reset_link}</p>
            
            <p style="color: #666; font-size: 14px; margin-top: 30px;">
                Si no solicitaste este cambio, ignora este correo.
            </p>
        </div>
        
        <div style="text-align: center; padding: 20px; color: #999; font-size: 12px;">
            © 2025 Safe2Gether | Este es un email automático
        </div>
    </body>
    </html>
    """
    
    try:
        # Obtener API key de SendGrid desde variables de entorno
        sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        
        # Debug: Mostrar si la key existe (sin revelar el valor completo)
        if sendgrid_api_key:
            key_preview = f"{sendgrid_api_key[:10]}...{sendgrid_api_key[-5:]}"
            print(f"🔑 SendGrid API Key cargada: {key_preview}")
        else:
            print("❌ SENDGRID_API_KEY NO ENCONTRADA en variables de entorno")
            print("📋 Variables disponibles:", list(os.environ.keys()))
            return False
        
        # Crear mensaje con email verificado de SendGrid
        message = Mail(
            from_email=Email("20213320@aloe.ulima.edu.pe", "Safe_2_Gether!"),  # DEBES VERIFICAR ESTE EMAIL EN SENDGRID
            to_emails=To(to_email),
            subject="Recupera tu contraseña - Safe2Gether",
            html_content=Content("text/html", html_content)
        )
        
        # Enviar
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        
        print(f"📤 SendGrid Response Status: {response.status_code}")
        print(f"📤 SendGrid Response Body: {response.body}")
        print(f"📤 SendGrid Response Headers: {response.headers}")
        
        if response.status_code in [200, 201, 202]:
            print(f"✅ Email enviado exitosamente a {to_email}")
            return True
        else:
            print(f"⚠️ Error SendGrid Status: {response.status_code}")
            print(f"⚠️ Error Body: {response.body}")
            return False
            
    except Exception as e:
        print(f"❌ Error en send_password_reset_email: {str(e)}")
        import traceback
        print(f"🔍 Traceback completo:\n{traceback.format_exc()}")
        return False


async def send_risk_alert_email(
    to_email: str,
    username: str,
    area_nombre: str,
    nivel_peligro: str,
    total_reportes: int,
    tipos_delitos: dict,
    dias_analisis: int
) -> bool:
    """Envía alerta preventiva sobre nivel de riesgo en área de interés"""
    
    # Color según nivel de peligro
    color_nivel = {
        "Bajo": "#28a745",  # Verde
        "Medio": "#ffc107",  # Amarillo
        "Alto": "#dc3545"    # Rojo
    }
    color = color_nivel.get(nivel_peligro, "#6c757d")
    
    # Emoji según nivel
    emoji_nivel = {
        "Bajo": "✅",
        "Medio": "⚠️",
        "Alto": "🚨"
    }
    emoji = emoji_nivel.get(nivel_peligro, "ℹ️")
    
    # Generar lista de tipos de delitos
    delitos_html = ""
    if tipos_delitos:
        delitos_html = "<ul style='margin: 10px 0; padding-left: 20px;'>"
        for categoria, cantidad in sorted(tipos_delitos.items(), key=lambda x: x[1], reverse=True):
            delitos_html += f"<li><strong>{categoria}:</strong> {cantidad} reporte(s)</li>"
        delitos_html += "</ul>"
    else:
        delitos_html = "<p>No se registraron incidentes en este período.</p>"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #08192D 0%, #0D47A1 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
            <h1>{emoji} Safe2Gether</h1>
            <p>Alerta Preventiva de Seguridad</p>
        </div>
        
        <div style="background: white; padding: 30px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 8px 8px;">
            <p>Hola <strong>{username}</strong>,</p>
            
            <p>Te enviamos un resumen del nivel de seguridad en tu área de interés:</p>
            
            <div style="background-color: #f8f9fa; border-left: 4px solid {color}; padding: 20px; margin: 20px 0;">
                <h2 style="margin-top: 0; color: {color};">{emoji} {area_nombre}</h2>
                <p style="margin: 10px 0;"><strong>Nivel de Peligro:</strong> 
                    <span style="color: {color}; font-size: 18px; font-weight: bold;">{nivel_peligro}</span>
                </p>
                <p style="margin: 10px 0;"><strong>Período analizado:</strong> Últimos {dias_analisis} días</p>
                <p style="margin: 10px 0;"><strong>Total de reportes:</strong> {total_reportes}</p>
            </div>
            
            <h3 style="color: #08192D; margin-top: 30px;">📊 Tipos de Incidentes Reportados:</h3>
            {delitos_html}
            
            <div style="background-color: #e7f3ff; border-radius: 5px; padding: 15px; margin: 20px 0;">
                <p style="margin: 0; color: #0D47A1;">
                    <strong>💡 Recomendación:</strong> 
                    {"Mantente alerta en esta zona y toma precauciones adicionales." if nivel_peligro in ["Medio", "Alto"] else "El área muestra baja actividad delictiva recientemente."}
                </p>
            </div>
            
            <p style="color: #666; font-size: 14px; margin-top: 30px;">
                Puedes ajustar la frecuencia de estas notificaciones desde tu perfil en la app.
            </p>
        </div>
        
        <div style="text-align: center; padding: 20px; color: #999; font-size: 12px;">
            © 2025 Safe2Gether | Este es un email automático
        </div>
    </body>
    </html>
    """
    
    try:
        sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        
        if not sendgrid_api_key:
            print("❌ SENDGRID_API_KEY NO ENCONTRADA para alerta de riesgo")
            return False
        
        message = Mail(
            from_email=Email("20213320@aloe.ulima.edu.pe", "Safe_2_Gether!"),
            to_emails=To(to_email),
            subject=f"{emoji} Alerta de Seguridad: {area_nombre} - Nivel {nivel_peligro}",
            html_content=Content("text/html", html_content)
        )
        
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        
        if response.status_code in [200, 201, 202]:
            print(f"✅ Alerta de riesgo enviada exitosamente a {to_email} para área {area_nombre}")
            return True
        else:
            print(f"⚠️ Error SendGrid Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error en send_risk_alert_email: {str(e)}")
        return False


# Función de prueba para verificar configuración
async def test_sendgrid_config():
    """Prueba la configuración de SendGrid sin enviar email"""
    api_key = os.getenv("SENDGRID_API_KEY")
    
    if not api_key:
        print("❌ SENDGRID_API_KEY no configurada")
        return False
    
    print(f"✅ API Key encontrada: {api_key[:10]}...{api_key[-5:]}")
    print(f"📏 Longitud de API Key: {len(api_key)} caracteres")
    
    # Verificar formato
    if api_key.startswith("SG."):
        print("✅ Formato de API Key correcto (comienza con SG.)")
    else:
        print("⚠️ Formato de API Key incorrecto (debería comenzar con SG.)")
    
    return True


async def send_report_confirmation_email(
    to_email: str,
    username: str,
    reporte_id: int,
    titulo: str,
    categoria: str | None = None,
    direccion: str | None = None,
) -> bool:
    """Envía un email de confirmación cuando se crea un reporte.

    Retorna True si SendGrid acepta el envío (202) o False en caso contrario.
    """
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset=\"UTF-8\">
    </head>
    <body style=\"font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;\">
        <div style=\"background: linear-gradient(135deg, #08192D 0%, #0D47A1 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;\">
            <h1>📣 Safe2Gether</h1>
            <p>Confirmación de Registro de Reporte</p>
        </div>

        <div style=\"background: white; padding: 30px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 8px 8px;\">
            <p>Hola <strong>{username}</strong>,</p>
            <p>Tu reporte ha sido registrado exitosamente.</p>

            <div style=\"background-color: #f8f9fa; border-left: 4px solid #0D47A1; padding: 15px; margin: 20px 0;\">
                <p style=\"margin: 0;\"><strong>N° de Reporte:</strong> #{reporte_id}</p>
                <p style=\"margin: 6px 0 0;\"><strong>Título:</strong> {titulo}</p>
                {f'<p style="margin: 6px 0 0;"><strong>Categoría:</strong> {categoria}</p>' if categoria else ''}
                {f'<p style="margin: 6px 0 0;"><strong>Dirección:</strong> {direccion}</p>' if direccion else ''}
            </div>

            <p style=\"color: #666; font-size: 14px;\">Gracias por ayudar a mantener informada a la comunidad.</p>
        </div>

        <div style=\"text-align: center; padding: 20px; color: #999; font-size: 12px;\">
            © 2025 Safe2Gether | Este es un email automático
        </div>
    </body>
    </html>
    """

    try:
        sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        if not sendgrid_api_key:
            print("❌ SENDGRID_API_KEY NO ENCONTRADA en variables de entorno")
            return False

        message = Mail(
            from_email=Email("20213320@aloe.ulima.edu.pe", "Safe_2_Gether!"),
            to_emails=To(to_email),
            subject=f"Reporte #{reporte_id} registrado - Safe2Gether",
            html_content=Content("text/html", html_content),
        )

        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)

        print(f"📤 SendGrid Response Status: {response.status_code}")
        if response.status_code in [200, 201, 202]:
            print(f"✅ Email de confirmación de reporte enviado a {to_email}")
            return True
        print(f"⚠️ Error SendGrid Status: {response.status_code}")
        return False

    except Exception as e:
        print(f"❌ Error en send_report_confirmation_email: {str(e)}")
        import traceback
        print(f"🔍 Traceback completo:\n{traceback.format_exc()}")
        return False