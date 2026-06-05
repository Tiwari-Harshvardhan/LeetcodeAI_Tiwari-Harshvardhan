import os

from twilio.rest import Client

client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))


def make_call(to_number: str, audio_url: str = None, text_to_say: str = None):
    twilio_number = os.getenv("TWILIO_PHONE_NUMBER", "")
    from_number = twilio_number.replace("whatsapp:", "") if twilio_number else ""

    if not from_number:
        raise ValueError("TWILIO_PHONE_NUMBER is not set in environment variables.")

    if audio_url:
        twiml = f"<Response><Play>{audio_url}</Play></Response>"
    elif text_to_say:
        twiml = f"<Response><Say>{text_to_say}</Say></Response>"
    else:
        raise ValueError("Either audio_url or text_to_say must be provided.")

    call = client.calls.create(
        to=to_number,
        from_=from_number,
        twiml=twiml,
    )
    return call.sid
