import os

from twilio.rest import Client

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")

client = Client(account_sid, auth_token)


def make_call(to_number: str, audio_url: str = None, text_to_say: str = None):
    twilio_number = os.getenv("TWILIO_PHONE_NUMBER", "")
    # Remove 'whatsapp:' prefix if it exists when making a voice call
    from_number = twilio_number.replace("whatsapp:", "") if twilio_number else twilio_number
    
    if audio_url:
        twiml = f"<Response><Play>{audio_url}</Play></Response>"
    else:
        twiml = f"<Response><Say>{text_to_say}</Say></Response>"
        
    call = client.calls.create(
        to=to_number,
        from_=from_number,
        twiml=twiml,
    )

    return call.sid

def send_whatsapp_message(to_number: str, body: str):
    # Use explicit WhatsApp number if set, otherwise default to Twilio Sandbox number
    whatsapp_from = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
    
    formatted_to = to_number if to_number.startswith("whatsapp:") else f"whatsapp:{to_number}"
    
    message = client.messages.create(
        from_=whatsapp_from,
        body=body,
        to=formatted_to
    )
    return message.sid
