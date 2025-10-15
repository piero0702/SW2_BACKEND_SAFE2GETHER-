import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

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