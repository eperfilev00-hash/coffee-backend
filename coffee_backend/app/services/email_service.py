from typing import Optional, cast
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import SecretStr
from coffee_backend.app.config import settings


async def send_password_reset_email(
    email: str, 
    reset_code: str,
    reset_link: Optional[str] = None
) -> bool:
    """
    Отправляет email с кодом для сброса пароля.
    
    Args:
        email: Получатель
        reset_code: 6-значный код
        reset_link: Опциональная ссылка для сброса
    """
    if (
        not settings.mail_username
        or not settings.mail_password
        or not settings.mail_from
        or not settings.mail_server
    ):
        print("Email settings not configured, skipping email sending")
        return False
    
    try:
        # Формируем тело письма с кодом
        if reset_link:
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: #f5f5f5; padding: 20px; border-radius: 8px;">
                        <h2 style="color: #333;">🔐 Запрос на сброс пароля</h2>
                        <p>Вы получили это письмо, потому что запросили сброс пароля.</p>
                        
                        <div style="background: #fff; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ff6b6b;">
                            <p style="margin: 0; color: #666;">Ваш код для сброса пароля:</p>
                            <h1 style="color: #ff6b6b; letter-spacing: 8px; margin: 10px 0;">{reset_code}</h1>
                            <p style="color: #999; font-size: 12px;">Действителен в течение 1 часа</p>
                        </div>
                        
                        <p>Или нажмите кнопку ниже:</p>
                        <a href="{reset_link}" 
                            style="display: inline-block; background: #ff6b6b; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; margin: 10px 0;">
                            Сбросить пароль
                        </a>
                        
                        <p style="color: #666; font-size: 12px; margin-top: 20px;">
                            Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.
                        </p>
                    </div>
                </body>
            </html>
            """
        else:
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: #f5f5f5; padding: 20px; border-radius: 8px;">
                        <h2 style="color: #333;">🔐 Запрос на сброс пароля</h2>
                        <p>Вы получили это письмо, потому что запросили сброс пароля.</p>
                        
                        <div style="background: #fff; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ff6b6b;">
                            <p style="margin: 0; color: #666;">Ваш код для сброса пароля:</p>
                            <h1 style="color: #ff6b6b; letter-spacing: 8px; margin: 10px 0;">{reset_code}</h1>
                            <p style="color: #999; font-size: 12px;">Действителен в течение 1 часа</p>
                        </div>
                        
                        <p style="color: #666; font-size: 12px; margin-top: 20px;">
                            Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.
                        </p>
                    </div>
                </body>
            </html>
            """
        
        conf = ConnectionConfig(
            MAIL_USERNAME=settings.mail_username,
            MAIL_PASSWORD=SecretStr(settings.mail_password),
            MAIL_FROM=settings.mail_from,
            MAIL_PORT=settings.mail_port,
            MAIL_SERVER=settings.mail_server,
            MAIL_STARTTLS=settings.mail_starttls,
            MAIL_SSL_TLS=settings.mail_ssl_tls,
            USE_CREDENTIALS=settings.use_credentials,
            VALIDATE_CERTS=settings.validate_certs
        )
        
        message = MessageSchema(
            subject="🔐 Сброс пароля - ваш код подтверждения",
            recipients=cast(list, [email]),
            body=html_body,
            subtype="html" # type: ignore
        )
        
        fm = FastMail(conf)
        await fm.send_message(message)
        return True
    except Exception as e:
        print(f"Ошибка отправки email: {e}")
        return False